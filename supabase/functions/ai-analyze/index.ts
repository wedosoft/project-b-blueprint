import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { messages, type, sessionId } = await req.json();
    
    console.log('AI analyze request:', { type, sessionId, messageCount: messages?.length });
    
    if (!messages || !type || !sessionId) {
      throw new Error('Missing required fields: messages, type, or sessionId');
    }

    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY not configured');
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // DLP 마스킹 함수
    const maskPII = (text: string): string => {
      let masked = text;
      // 주민등록번호
      masked = masked.replace(/\d{6}-\d{7}/g, '######-#######');
      // 전화번호
      masked = masked.replace(/01\d-\d{3,4}-\d{4}/g, '###-####-####');
      // 이메일
      masked = masked.replace(/[\w.-]+@[\w.-]+\.\w+/g, '#####@#####.###');
      // 카드번호
      masked = masked.replace(/\d{4}-\d{4}-\d{4}-\d{4}/g, '####-####-####-####');
      return masked;
    };

    // 대화 컨텍스트 생성
    const conversationContext = messages.map((m: any) => 
      `${m.speaker === 'customer' ? '고객' : '상담사'}: ${m.text}`
    ).join('\n');

    let systemPrompt = '';
    let userPrompt = '';

    // 분석 타입별 프롬프트 설정
    if (type === 'summary') {
      systemPrompt = `당신은 고객센터 대화를 요약하는 AI 어시스턴트입니다. 
대화의 핵심 내용을 3-4문장으로 간결하게 요약해주세요.
- 고객의 주요 문의사항
- 상담사의 대응 내용
- 현재 상황 및 다음 단계`;
      
      userPrompt = `다음 고객센터 대화를 요약해주세요:\n\n${conversationContext}`;

    } else if (type === 'emotion') {
      systemPrompt = `당신은 고객 감정을 분석하는 AI 어시스턴트입니다.
대화에서 고객의 감정 상태를 분석하여 JSON 형식으로 응답해주세요.
형식: {"sentiment": "긍정|중립|부정", "intensity": 0.0-1.0, "keywords": ["키워드1", "키워드2"]}`;
      
      userPrompt = `다음 대화에서 고객의 감정을 분석해주세요:\n\n${conversationContext}`;

    } else if (type === 'intent') {
      systemPrompt = `당신은 고객 의도를 분류하는 AI 어시스턴트입니다.
고객의 문의 의도를 다음 중 하나로 분류하고, JSON 형식으로 응답해주세요.
카테고리: 불만, 문의, 환불요청, 정보요청, 기술지원, 기타
형식: {"intent": "카테고리", "confidence": 0.0-1.0, "reason": "분류 근거"}`;
      
      userPrompt = `다음 대화에서 고객의 의도를 분류해주세요:\n\n${conversationContext}`;

    } else if (type === 'reply') {
      systemPrompt = `당신은 고객센터 상담사를 돕는 AI 어시스턴트입니다.
현재 상황에 적합한 응답을 1-2문장으로 제안해주세요.
- 공손하고 전문적인 톤
- 구체적이고 실용적인 조언
- 고객의 감정을 고려한 응답`;
      
      userPrompt = `다음 대화 상황에서 상담사가 사용할 수 있는 적절한 응답을 제안해주세요:\n\n${conversationContext}`;
    }

    // Lovable AI 호출
    const startTime = Date.now();
    const response = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LOVABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-flash',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.7,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Lovable AI error:', response.status, errorText);
      throw new Error(`AI gateway error: ${response.status}`);
    }

    const data = await response.json();
    const aiResponse = data.choices[0].message.content;
    const latency = Date.now() - startTime;

    console.log('AI response received:', { type, latency, responseLength: aiResponse?.length });

    // 결과 저장
    const { data: suggestion, error: suggestionError } = await supabase
      .from('ai_suggestions')
      .insert({
        session_id: sessionId,
        type,
        text: maskPII(aiResponse),
        metadata: {
          model: 'google/gemini-2.5-flash',
          latency,
          messageCount: messages.length
        }
      })
      .select()
      .single();

    if (suggestionError) {
      console.error('Failed to save suggestion:', suggestionError);
    }

    // 감사 로그 저장
    await supabase.from('audit_log').insert({
      event: `ai_${type}`,
      model_id: 'google/gemini-2.5-flash',
      latency,
      dlp_flag: conversationContext !== maskPII(conversationContext)
    });

    return new Response(
      JSON.stringify({ 
        text: aiResponse,
        suggestion: suggestion,
        latency 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error in ai-analyze:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});