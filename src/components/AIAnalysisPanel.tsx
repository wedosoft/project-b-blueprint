import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { 
  Brain, 
  Heart, 
  Target, 
  MessageSquare, 
  ThumbsUp, 
  ThumbsDown,
  Loader2,
  Sparkles
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface Message {
  id: string;
  speaker: 'agent' | 'customer';
  text: string;
  created_at: string;
}

interface AISuggestion {
  id: string;
  type: string;
  text: string;
  score?: number;
  created_at: string;
  metadata?: any;
}

interface AIAnalysisPanelProps {
  sessionId: string;
  messages: Message[];
}

export const AIAnalysisPanel = ({ sessionId, messages }: AIAnalysisPanelProps) => {
  const [suggestions, setSuggestions] = useState<Record<string, AISuggestion>>({});
  const [loadingTypes, setLoadingTypes] = useState<Set<string>>(new Set());
  const [editOpen, setEditOpen] = useState(false);
  const [editText, setEditText] = useState('');
  const [sending, setSending] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadSuggestions();

    // 실시간 업데이트 구독
    const channel = supabase
      .channel('suggestions-changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'ai_suggestions',
          filter: `session_id=eq.${sessionId}`
        },
        (payload) => {
          const newSuggestion = payload.new as AISuggestion;
          setSuggestions(prev => ({
            ...prev,
            [newSuggestion.type]: newSuggestion
          }));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [sessionId]);

  const loadSuggestions = async () => {
    const { data, error } = await supabase
      .from('ai_suggestions')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error loading suggestions:', error);
    } else if (data) {
      const suggestionMap = data.reduce((acc, item) => {
        if (!acc[item.type]) {
          acc[item.type] = item;
        }
        return acc;
      }, {} as Record<string, AISuggestion>);
      setSuggestions(suggestionMap);
    }
  };

  const analyzeWithAI = async (type: 'summary' | 'emotion' | 'intent' | 'reply') => {
    if (messages.length === 0) {
      toast({
        title: "메시지가 없습니다",
        description: "분석할 대화가 없습니다.",
        variant: "destructive"
      });
      return;
    }

    setLoadingTypes(prev => new Set(prev).add(type));

    try {
      const { data, error } = await supabase.functions.invoke('ai-analyze', {
        body: {
          messages: messages.slice(-10), // 최근 10개 메시지만 분석
          type,
          sessionId
        }
      });

      if (error) throw error;

      toast({
        title: "분석 완료",
        description: `${getTypeLabel(type)} 분석이 완료되었습니다.`,
      });

    } catch (error) {
      console.error('Error analyzing:', error);
      toast({
        title: "분석 실패",
        description: error instanceof Error ? error.message : '알 수 없는 오류',
        variant: "destructive"
      });
    } finally {
      setLoadingTypes(prev => {
        const newSet = new Set(prev);
        newSet.delete(type);
        return newSet;
      });
    }
  };

  const handleFeedback = async (suggestionId: string, approved: boolean) => {
    try {
      const { error } = await supabase
        .from('feedback')
        .insert({
          suggestion_id: suggestionId,
          approved
        });

      if (error) throw error;

      toast({
        title: "피드백 전송 완료",
        description: "귀하의 피드백이 저장되었습니다.",
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      summary: '대화 요약',
      emotion: '감정 분석',
      intent: '의도 분류',
      reply: '응답 제안'
    };
    return labels[type] || type;
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, any> = {
      summary: Brain,
      emotion: Heart,
      intent: Target,
      reply: MessageSquare
    };
    const Icon = icons[type] || Sparkles;
    return <Icon className="w-4 h-4" />;
  };

  const parseAndFormatSuggestion = (text: string, type: string) => {
    const extractJsonCandidate = (raw: string) => {
      // 1) 코드펜스 안의 JSON 추출
      const codeMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/i);
      if (codeMatch) return codeMatch[1].trim();
      // 2) 본문 중 첫번째 중괄호 블록 추출
      const braceMatch = raw.match(/(\{[\s\S]*\})/);
      if (braceMatch) return braceMatch[1];
      return raw.trim();
    };

    try {
      const candidate = extractJsonCandidate(text);
      if (type === 'emotion') {
        const parsed = JSON.parse(candidate);
        const intensity = typeof parsed.intensity === 'number' ? (parsed.intensity * 100).toFixed(0) + '%' : 'N/A';
        const keywords = Array.isArray(parsed.keywords) ? parsed.keywords.join(', ') : 'N/A';
        return `감정: ${parsed.sentiment ?? 'N/A'}\n강도: ${intensity}\n키워드: ${keywords}`;
      } else if (type === 'intent') {
        const parsed = JSON.parse(candidate);
        const confidence = typeof parsed.confidence === 'number' ? (parsed.confidence * 100).toFixed(0) + '%' : 'N/A';
        return `의도: ${parsed.intent ?? 'N/A'}\n신뢰도: ${confidence}\n근거: ${parsed.reason ?? 'N/A'}`;
      }
    } catch (e) {
      // JSON 파싱 실패 시 원본 텍스트 반환
    }
    return text;
  };

  const analyzeAll = async () => {
    const types: ('summary' | 'emotion' | 'intent' | 'reply')[] = ['summary', 'emotion', 'intent', 'reply'];
    for (const type of types) {
      await analyzeWithAI(type);
      // 각 분석 사이에 약간의 지연
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  const sendAgentMessage = async (text: string) => {
    const content = text.trim();
    if (!content) return;
    setSending(true);
    try {
      const { error } = await supabase
        .from('messages')
        .insert({ session_id: sessionId, speaker: 'agent', text: content });
      if (error) throw error;
      await supabase.from('sessions').update({ status: 'in_progress' }).eq('id', sessionId);
      toast({ title: '전송 완료', description: '응답이 전송되었습니다.' });
    } catch (e) {
      console.error(e);
      toast({ title: '전송 실패', description: e instanceof Error ? e.message : '알 수 없는 오류', variant: 'destructive' });
    } finally {
      setSending(false);
      setEditOpen(false);
    }
  };

  const renderSuggestionCard = (type: string) => {
    const suggestion = suggestions[type];
    const isLoading = loadingTypes.has(type);

    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {getTypeIcon(type)}
              {getTypeLabel(type)}
            </CardTitle>
            <Button
              size="sm"
              onClick={() => analyzeWithAI(type as any)}
              disabled={isLoading || messages.length === 0}
              variant="outline"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {suggestion ? (
            <div className="space-y-3">
              {(() => {
                const formattedText = parseAndFormatSuggestion(suggestion.text, type);
                return (
                  <>
                    <div className="text-sm whitespace-pre-wrap bg-muted/50 p-3 rounded-md">
                      {formattedText}
                    </div>
                    {suggestion.metadata?.latency && (
                      <Badge variant="secondary" className="text-xs">
                        응답시간: {suggestion.metadata.latency}ms
                      </Badge>
                    )}

                    {(type === 'intent' || type === 'emotion' || type === 'reply') && (
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => sendAgentMessage(formattedText)} disabled={sending}>
                          {sending ? '전송 중...' : '보내기'}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => { setEditText(formattedText); setEditOpen(true); }}
                        >
                          편집 후 전송
                        </Button>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleFeedback(suggestion.id, true)}
                      >
                        <ThumbsUp className="w-3 h-3 mr-1" />
                        유용함
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleFeedback(suggestion.id, false)}
                      >
                        <ThumbsDown className="w-3 h-3 mr-1" />
                        개선 필요
                      </Button>
                    </div>
                  </>
                );
              })()}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {messages.length === 0 
                ? '대화를 시작하면 AI 분석을 사용할 수 있습니다.'
                : '분석 버튼을 클릭하여 AI 분석을 시작하세요.'}
            </p>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="h-full flex flex-col bg-card">
      <div className="border-b border-border p-4 bg-muted/30">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            AI 분석
          </h2>
          <Button
            onClick={analyzeAll}
            disabled={messages.length === 0 || loadingTypes.size > 0}
            size="sm"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            전체 분석
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="all">전체</TabsTrigger>
            <TabsTrigger value="summary">요약</TabsTrigger>
            <TabsTrigger value="emotion">감정</TabsTrigger>
            <TabsTrigger value="intent">의도</TabsTrigger>
            <TabsTrigger value="reply">응답</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4 mt-4">
            {renderSuggestionCard('summary')}
            {renderSuggestionCard('emotion')}
            {renderSuggestionCard('intent')}
            {renderSuggestionCard('reply')}
          </TabsContent>

          <TabsContent value="summary" className="mt-4">
            {renderSuggestionCard('summary')}
          </TabsContent>

          <TabsContent value="emotion" className="mt-4">
            {renderSuggestionCard('emotion')}
          </TabsContent>

          <TabsContent value="intent" className="mt-4">
            {renderSuggestionCard('intent')}
          </TabsContent>

          <TabsContent value="reply" className="mt-4">
            {renderSuggestionCard('reply')}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};