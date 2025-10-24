/**
 * API client for backend communication
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export interface MessageAttachment {
  type?: string;
  url?: string;
  name?: string;
}

export interface StartConversationRequest {
  organizationId?: string;
  customerId?: string;
  metadata?: Record<string, unknown>;
  message: {
    body: string;
    attachments?: MessageAttachment[];
  };
}

export interface AIResponseSummary {
  id: string;
  status: string;
  confidence: number;
  requiresApproval: boolean;
  provider?: string;
  model?: string;
  generatedAt?: string;
}

export interface Message {
  id: string;
  conversationId: string;
  senderType: string;
  body: string;
  sequence: number;
  createdAt: string;
  attachments: MessageAttachment[];
  senderUserId?: string;
  aiResponse?: AIResponseSummary;
}

export interface Conversation {
  id: string;
  organizationId?: string;
  customerId?: string;
  externalCustomerRef?: string;
  status: string;
  channel: string;
  priority: string;
  startedAt: string;
  lastActivityAt: string;
  pendingApprovalResponseId?: string;
  endedAt?: string;
  metadata: Record<string, unknown>;
}

export interface ConversationResponse {
  conversation: Conversation;
  messages: Message[];
  pendingApproval: boolean;
}

export interface PendingApproval {
  conversationId: string;
  aiResponseId: string;
  customerMessage: string;
  proposedResponse: string;
  confidence: number;
  waitingSince: string;
  priority: string;
}

export interface ApprovalActionRequest {
  action: 'approved' | 'modified' | 'rejected';
  agentId: string;
  submittedText?: string;
  notes?: string;
}

export interface ApprovalActionResponse {
  success: boolean;
  message: string;
  conversationId: string;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = BACKEND_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // Conversation endpoints
  async startConversation(
    request: StartConversationRequest
  ): Promise<ConversationResponse> {
    return this.request<ConversationResponse>('/v1/conversations', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getConversation(conversationId: string): Promise<ConversationResponse> {
    return this.request<ConversationResponse>(
      `/v1/conversations/${conversationId}`
    );
  }

  // Approval endpoints
  async listPendingApprovals(
    organizationId: string
  ): Promise<PendingApproval[]> {
    return this.request<PendingApproval[]>(
      `/v1/approvals/pending?organization_id=${organizationId}`
    );
  }

  async approveResponse(
    aiResponseId: string,
    request: ApprovalActionRequest
  ): Promise<ApprovalActionResponse> {
    return this.request<ApprovalActionResponse>(
      `/v1/approvals/${aiResponseId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }
}

export const apiClient = new APIClient();
