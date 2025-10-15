import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { MessageSquare } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { ChatInterface } from '@/components/ChatInterface';

const Customer = () => {
  const [name, setName] = useState('');
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !title || !message) {
      toast({
        title: "입력 오류",
        description: "모든 필드를 입력해주세요.",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);

    try {
      // 1. 세션(티켓) 생성
      const { data: session, error: sessionError } = await supabase
        .from('sessions')
        .insert({
          customer_name: name,
          customer_id: `CUST-${Date.now()}`,
          agent_id: 'UNASSIGNED',
          title: title,
          status: 'pending'
        })
        .select()
        .single();

      if (sessionError) throw sessionError;

      // 2. 첫 메시지 생성
      const { error: messageError } = await supabase
        .from('messages')
        .insert({
          session_id: session.id,
          speaker: 'customer',
          text: message
        });

      if (messageError) throw messageError;

      setSessionId(session.id);
      toast({
        title: "문의 접수 완료",
        description: "상담사와 대화를 시작하세요.",
      });

    } catch (error) {
      console.error('Error submitting inquiry:', error);
      toast({
        title: "접수 실패",
        description: error instanceof Error ? error.message : '알 수 없는 오류',
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // 티켓 제출 후 채팅 인터페이스 표시
  if (sessionId) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b border-border bg-card shadow-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
                  <MessageSquare className="w-6 h-6 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-foreground">고객 상담</h1>
                  <p className="text-sm text-muted-foreground">{name}님의 상담</p>
                </div>
              </div>
              <Button variant="outline" onClick={() => setSessionId(null)}>
                새 문의 작성
              </Button>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-6">
          <div className="max-w-4xl mx-auto h-[calc(100vh-140px)]">
            <Card className="h-full overflow-hidden">
              <ChatInterface 
                sessionId={sessionId}
                onMessagesUpdate={() => {}}
                isCustomerView={true}
              />
            </Card>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">고객 문의</h1>
              <p className="text-sm text-muted-foreground">무엇을 도와드릴까요?</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <Card className="p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">문의하기</h2>
            <p className="text-muted-foreground">
              문의 내용을 작성해주시면 전문 상담사가 빠르게 응답해드리겠습니다.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">이름</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="이름을 입력하세요"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">제목</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="문의 제목을 입력하세요"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="message">문의 내용</Label>
              <Textarea
                id="message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="문의 내용을 상세히 작성해주세요"
                className="min-h-[200px]"
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? '접수 중...' : '문의 접수'}
            </Button>
          </form>
        </Card>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p>문의 접수 후 평균 5분 이내에 상담사가 응답합니다.</p>
        </div>
      </main>
    </div>
  );
};

export default Customer;
