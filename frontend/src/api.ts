import type { ChatMessage, Conversation, ConversationDetail, DocumentRecord } from "./types";

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail)) {
      return "Check the form and try again.";
    }
  } catch {
    return `Request failed (${response.status}).`;
  }
  return `Request failed (${response.status}).`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function listDocuments(): Promise<DocumentRecord[]> {
  return request("/api/documents");
}

export function uploadDocument(file: File): Promise<DocumentRecord> {
  const body = new FormData();
  body.append("file", file);
  return request("/api/documents", { method: "POST", body });
}

export function deleteDocument(id: string): Promise<void> {
  return request(`/api/documents/${id}`, { method: "DELETE" });
}

export function listConversations(): Promise<Conversation[]> {
  return request("/api/conversations");
}

export function createConversation(): Promise<Conversation> {
  return request("/api/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return request(`/api/conversations/${id}`);
}

export function deleteConversation(id: string): Promise<void> {
  return request(`/api/conversations/${id}`, { method: "DELETE" });
}

export function askQuestion(
  conversationId: string,
  content: string,
  documentIds: string[] | null,
): Promise<{ user_message: ChatMessage; assistant_message: ChatMessage }> {
  return request(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content,
      document_ids: documentIds,
    }),
  });
}
