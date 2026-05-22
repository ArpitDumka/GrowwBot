export type SampleQuestion = {
  id: string;
  text: string;
  scheme_id: string;
};

export type BootstrapResponse = {
  title: string;
  title_suffix: string;
  disclaimer: string;
  ephemeral_hint: string;
  welcome_message?: string;
  input_placeholder?: string;
  client_timeout_hint_seconds: number;
  sample_questions: SampleQuestion[];
};

export type ChatResponse = {
  trace_id: string;
  outcome: "ANSWERED" | "REFUSED" | "NOT_FOUND" | "ERROR";
  answer: string;
  citation_url?: string | null;
  last_updated?: string | null;
  disclaimer: string;
  used_llm?: boolean;
  suggested_replies?: string[] | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  traceId?: string;
  error?: boolean;
  createdAt?: number;
  suggestedReplies?: string[];
};

export type StoredMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  traceId?: string;
  error?: boolean;
  createdAt: number;
  suggestedReplies?: string[];
};

export type ChatSession = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: StoredMessage[];
};
