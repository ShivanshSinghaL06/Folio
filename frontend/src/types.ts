export type DocumentRecord = {
  id: string;
  filename: string;
  media_type: string;
  status: string;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
};

export type Citation = {
  index: number;
  document_id: string;
  document_name: string;
  page_start: number | null;
  page_end: number | null;
  section_title: string | null;
  excerpt: string;
  cited_inline: boolean;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
};

export type Conversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = Conversation & {
  messages: ChatMessage[];
};
