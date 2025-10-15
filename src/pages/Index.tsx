import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { ChatInterface } from '@/components/ChatInterface';
import { AIAnalysisPanel } from '@/components/AIAnalysisPanel';
import { TicketList } from '@/components/TicketList';
import { Headphones, Shield, Database, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface Message {
  id: string;
  speaker: 'agent' | 'customer';
  text: string;
  created_at: string;
}

const Index = () => {
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const navigate = useNavigate();

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
                <h1 className="text-2xl font-bold text-foreground">상담사 콘솔</h1>
                <p className="text-sm text-muted-foreground">AI 기반 상담 지원 시스템</p>
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
              <Button onClick={() => navigate('/customer')} variant="outline">
                <ExternalLink className="w-4 h-4 mr-2" />
                고객 페이지
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {!selectedTicketId ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">
            {/* Ticket List */}
            <div className="lg:col-span-1">
              <TicketList
                selectedTicketId={selectedTicketId}
                onSelectTicket={setSelectedTicketId}
              />
            </div>

            {/* Empty State */}
            <div className="lg:col-span-2">
              <Card className="h-full flex items-center justify-center p-12">
                <div className="text-center">
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Headphones className="w-10 h-10 text-primary" />
                  </div>
                  <h2 className="text-2xl font-semibold mb-2">티켓을 선택하세요</h2>
                  <p className="text-muted-foreground">
                    왼쪽 목록에서 티켓을 선택하면 상담을 시작할 수 있습니다.
                  </p>
                </div>
              </Card>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-180px)]">
            {/* Ticket List - Narrower */}
            <div className="lg:col-span-1">
              <TicketList
                selectedTicketId={selectedTicketId}
                onSelectTicket={setSelectedTicketId}
              />
            </div>

            {/* Chat Interface */}
            <div className="lg:col-span-2">
              <Card className="h-full overflow-hidden">
                <ChatInterface 
                  sessionId={selectedTicketId} 
                  onMessagesUpdate={setMessages}
                />
              </Card>
            </div>

            {/* AI Analysis Panel */}
            <div className="lg:col-span-1">
              <Card className="h-full overflow-hidden">
                <AIAnalysisPanel 
                  sessionId={selectedTicketId}
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
            {selectedTicketId && (
              <div className="text-muted-foreground">
                티켓: {selectedTicketId.slice(0, 8)}...
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Index;