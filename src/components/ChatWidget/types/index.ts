/**
 * TypeScript interfaces for ChatWidget component
 */

export interface ChatSession {
  id: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
}

export interface Citation {
  text: string;
  source: string;
  url?: string;
  page?: number;
  chapter?: string;
}

export interface TextSelection {
  text: string;
  range: Range;
  rect: DOMRect;
}

export interface ChatWidgetProps {
  apiSessionEndpoint?: string;
  theme?: 'light' | 'dark';
  title?: string;
  onOpen?: () => void;
  onClose?: () => void;
  onMessage?: (message: ChatMessage) => void;
}

export interface ChatButtonProps {
  onClick: () => void;
  hasSelection?: boolean;
  icon?: string;
  position?: 'bottom-right' | 'bottom-left';
}

export interface SelectionPopoverProps {
  selection: TextSelection;
  onAskAboutSelection: (text: string) => void;
  onClose: () => void;
}

export interface UseSessionPersistenceReturn {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  createSession: () => ChatSession;
  saveMessage: (sessionId: string, message: ChatMessage) => void;
  deleteSession: (sessionId: string) => void;
  loadSession: (sessionId: string) => void;
  clearAllSessions: () => void;
}

export interface UseChatKitSessionReturn {
  clientSecret: string | null;
  isLoading: boolean;
  error: Error | null;
  refreshSession: () => Promise<void>;
}

export interface UseTextSelectionReturn {
  selectedText: string;
  selection: TextSelection | null;
  isSelecting: boolean;
  clearSelection: () => void;
}