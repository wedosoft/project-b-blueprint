import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Send, User, Headphones } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface Message {
  id: string;
  speaker: 'agent' | 'customer';
  text: string;
  created_at: string;
}

interface ChatInterfaceProps {
  sessionId: string;
  onMessagesUpdate: (messages: Message[]) => void;
  isCustomerView?: boolean;
}

export const ChatInterface = ({ sessionId, onMessagesUpdate, isCustomerView = false }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadMessages();
    
    // 실시간 업데이트 구독
    const channel = supabase
      .channel('messages-changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `session_id=eq.${sessionId}`
        },
        (payload) => {
          const newMessage = payload.new as Message;
          setMessages(prev => [...prev, newMessage]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [sessionId]);

  useEffect(() => {
    onMessagesUpdate(messages);
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true });

    if (error) {
      console.error('Error loading messages:', error);
      toast({
        title: "메시지 로드 실패",
        description: error.message,
        variant: "destructive"
      });
    } else if (data) {
      setMessages(data as Message[]);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);
    const messageText = inputText;
    setInputText('');

    try {
      const { error } = await supabase
        .from('messages')
        .insert({
          session_id: sessionId,
          speaker: isCustomerView ? 'customer' : 'agent',
          text: messageText
        });

      if (error) throw error;

      // 상태를 in_progress로 업데이트
      await supabase
        .from('sessions')
        .update({ status: 'in_progress' })
        .eq('id', sessionId);

    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: "메시지 전송 실패",
        description: error instanceof Error ? error.message : '알 수 없는 오류',
        variant: "destructive"
      });
      setInputText(messageText);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-card">
      <div className="border-b border-border p-4 bg-muted/30">
        <h2 className="text-lg font-semibold">대화 내역</h2>
        <p className="text-sm text-muted-foreground">
          {isCustomerView ? '고객 문의' : '상담사 응답 입력'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.speaker === 'agent' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[80%] ${msg.speaker === 'agent' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              <Badge variant={msg.speaker === 'agent' ? 'default' : 'secondary'} className="w-fit">
                {msg.speaker === 'agent' ? '상담사' : '고객'}
              </Badge>
              <Card className={`p-3 ${
                msg.speaker === 'agent' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-secondary text-secondary-foreground'
              }`}>
                <p className="whitespace-pre-wrap break-words">{msg.text}</p>
              </Card>
              <span className="text-xs text-muted-foreground">
                {new Date(msg.created_at).toLocaleTimeString('ko-KR')}
              </span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border p-4 bg-muted/30">
        <div className="flex gap-2">
          <Textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isCustomerView ? '메시지를 입력하세요...' : '상담사 응답을 입력하세요...'}
            className="min-h-[60px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!inputText.trim() || isLoading}
            size="icon"
            className="self-end h-[60px] w-[60px]"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};