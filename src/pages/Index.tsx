import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ChatInterface } from '@/components/ChatInterface';
import { AIAnalysisPanel } from '@/components/AIAnalysisPanel';
import { PlusCircle, Headphones, Shield, Database } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface Message {
  id: string;
  speaker: 'agent' | 'customer';
  text: string;
  created_at: string;
}

const Index = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    // 자동으로 새 세션 생성
    createNewSession();
  }, []);

  const createNewSession = async () => {
    try {
      const { data, error } = await supabase
        .from('sessions')
        .insert({
          agent_id: 'AGENT-001',
          customer_name: '고객',
          customer_id: `CUST-${Date.now()}`
        })
        .select()
        .single();

      if (error) throw error;

      setSessionId(data.id);
      setMessages([]);
      
      toast({
        title: "새 상담 세션",
        description: "새로운 상담 세션이 시작되었습니다.",
      });
    } catch (error) {
      console.error('Error creating session:', error);
      toast({
        title: "세션 생성 실패",
        description: error instanceof Error ? error.message : '알 수 없는 오류',
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                <Headphones className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">AI 컨택센터</h1>
                <p className="text-sm text-muted-foreground">지능형 상담 지원 시스템</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Shield className="w-4 h-4 text-success" />
                <span>DLP 활성</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Database className="w-4 h-4 text-info" />
                <span>로컬 저장</span>
              </div>
              <Button onClick={createNewSession} variant="default">
                <PlusCircle className="w-4 h-4 mr-2" />
                새 세션
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {!sessionId ? (
          <Card className="p-12 text-center">
            <div className="flex flex-col items-center gap-4">
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                <Headphones className="w-10 h-10 text-primary" />
              </div>
              <h2 className="text-2xl font-semibold">세션을 시작하세요</h2>
              <p className="text-muted-foreground max-w-md">
                새 세션 버튼을 클릭하여 AI 기반 상담을 시작할 수 있습니다.
              </p>
              <Button onClick={createNewSession} size="lg" className="mt-4">
                <PlusCircle className="w-5 h-5 mr-2" />
                새 상담 세션 시작
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">
            {/* Chat Interface - 2/3 width on large screens */}
            <div className="lg:col-span-2">
              <Card className="h-full overflow-hidden">
                <ChatInterface 
                  sessionId={sessionId} 
                  onMessagesUpdate={setMessages}
                />
              </Card>
            </div>

            {/* AI Analysis Panel - 1/3 width on large screens */}
            <div className="lg:col-span-1">
              <Card className="h-full overflow-hidden">
                <AIAnalysisPanel 
                  sessionId={sessionId}
                  messages={messages}
                />
              </Card>
            </div>
          </div>
        )}
      </main>

      {/* Footer Info */}
      <div className="fixed bottom-4 right-4">
        <Card className="p-3 bg-card/95 backdrop-blur-sm shadow-lg">
          <div className="flex flex-col gap-1 text-xs">
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
              <span>AI 분석 준비완료</span>
            </div>
            {sessionId && (
              <div className="text-muted-foreground">
                세션: {sessionId.slice(0, 8)}...
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Index;