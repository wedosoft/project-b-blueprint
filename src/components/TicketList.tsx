import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, User, MessageSquare } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface Session {
  id: string;
  customer_name: string | null;
  customer_id: string | null;
  title: string | null;
  status: string | null;
  created_at: string;
  updated_at: string | null;
}

interface TicketListProps {
  selectedTicketId: string | null;
  onSelectTicket: (ticketId: string) => void;
}

export const TicketList = ({ selectedTicketId, onSelectTicket }: TicketListProps) => {
  const [tickets, setTickets] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTickets();

    // Realtime subscription
    const channel = supabase
      .channel('sessions-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'sessions'
        },
        () => {
          loadTickets();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const loadTickets = async () => {
    try {
      const { data, error } = await supabase
        .from('sessions')
        .select('*')
        .order('updated_at', { ascending: false, nullsFirst: false })
        .order('created_at', { ascending: false });

      if (error) throw error;
      setTickets(data || []);
    } catch (error) {
      console.error('Error loading tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'in_progress':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'resolved':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'closed':
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const getStatusLabel = (status: string | null) => {
    switch (status) {
      case 'pending':
        return '대기중';
      case 'in_progress':
        return '상담중';
      case 'resolved':
        return '해결완료';
      case 'closed':
        return '종료';
      default:
        return '알 수 없음';
    }
  };

  if (loading) {
    return (
      <Card className="h-full p-4">
        <div className="text-center text-muted-foreground">로딩 중...</div>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <div className="border-b border-border p-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          티켓 목록
          <Badge variant="secondary" className="ml-auto">
            {tickets.length}
          </Badge>
        </h2>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {tickets.length === 0 ? (
            <div className="text-center text-muted-foreground p-8">
              접수된 티켓이 없습니다
            </div>
          ) : (
            tickets.map((ticket) => (
              <Card
                key={ticket.id}
                className={`p-4 cursor-pointer transition-colors hover:bg-muted/50 ${
                  selectedTicketId === ticket.id ? 'bg-muted border-primary' : ''
                }`}
                onClick={() => onSelectTicket(ticket.id)}
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-sm line-clamp-1">
                      {ticket.title || '제목 없음'}
                    </h3>
                    <Badge className={getStatusColor(ticket.status)}>
                      {getStatusLabel(ticket.status)}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      <span>{ticket.customer_name || '고객'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>
                        {formatDistanceToNow(new Date(ticket.created_at), {
                          addSuffix: true,
                          locale: ko
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </Card>
  );
};
