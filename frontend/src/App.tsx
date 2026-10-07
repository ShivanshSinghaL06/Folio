import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  askQuestion,
  createConversation,
  deleteConversation,
  deleteDocument,
  getConversation,
  listConversations,
  listDocuments,
  uploadDocument,
} from "./api";
import type { ChatMessage, Citation, Conversation, DocumentRecord } from "./types";

function locationLabel(citation: Citation): string {
  const parts: string[] = [];
  if (citation.section_title) {
    parts.push(citation.section_title);
  }
  if (citation.page_start != null && citation.page_end != null && citation.page_start !== citation.page_end) {
    parts.push(`pages ${citation.page_start}–${citation.page_end}`);
  } else if (citation.page_start != null) {
    parts.push(`page ${citation.page_start}`);
  }
  return parts.join(" · ");
}

export function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedDocument, setSelectedDocument] = useState("all");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<number | null>(null);

  const readyDocuments = documents.filter((document) => document.status === "ready");
  const latestAssistant = useMemo(
    () => [...messages].reverse().find((message) => message.role === "assistant"),
    [messages],
  );
  const citations = latestAssistant?.citations ?? [];

  async function refreshLibrary() {
    const [docs, chats] = await Promise.all([listDocuments(), listConversations()]);
    setDocuments(docs);
    setConversations(chats);
  }

  useEffect(() => {
    refreshLibrary().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "The API is not reachable.");
    });
  }, []);

  async function openConversation(id: string) {
    setError(null);
    const detail = await getConversation(id);
    setActiveId(detail.id);
    setMessages(detail.messages);
    setActiveCitation(null);
  }

  async function onUpload(file: File | undefined) {
    if (!file) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refreshLibrary();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Upload failed.");
      await refreshLibrary().catch(() => undefined);
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteDocument(id: string) {
    setError(null);
    try {
      await deleteDocument(id);
      if (selectedDocument === id) {
        setSelectedDocument("all");
      }
      await refreshLibrary();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "The document could not be removed.");
    }
  }

  async function onNewChat() {
    setError(null);
    try {
      const created = await createConversation();
      setConversations((current) => [created, ...current]);
      setActiveId(created.id);
      setMessages([]);
      setActiveCitation(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "A new chat could not be started.");
    }
  }

  async function onDeleteChat(id: string) {
    setError(null);
    try {
      await deleteConversation(id);
      if (activeId === id) {
        setActiveId(null);
        setMessages([]);
      }
      await refreshLibrary();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "The chat could not be removed.");
    }
  }

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || busy) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      let conversationId = activeId;
      if (!conversationId) {
        const created = await createConversation();
        conversationId = created.id;
        setActiveId(created.id);
        setConversations((current) => [created, ...current]);
      }
      const documentIds = selectedDocument === "all" ? null : [selectedDocument];
      const result = await askQuestion(conversationId, content, documentIds);
      setDraft("");
      setMessages((current) => [...current, result.user_message, result.assistant_message]);
      setActiveCitation(null);
      await refreshLibrary();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "The question could not be answered.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Document desk</p>
          <h1>Semantic Document Search</h1>
        </div>
        <p className="lede">Ask questions across PDF and Word files. Answers keep the page or section they came from.</p>
      </header>

      {error ? (
        <p className="banner" role="alert">
          {error}
        </p>
      ) : null}

      <main className="layout">
        <aside className="panel library">
          <div className="panel-head">
            <h2>Library</h2>
            <label className="upload">
              Add file
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  event.target.value = "";
                  void onUpload(file).catch((reason: unknown) => {
                    setError(reason instanceof Error ? reason.message : "Upload failed.");
                  });
                }}
              />
            </label>
          </div>
          {documents.length === 0 ? <p className="empty">No documents yet.</p> : null}
          <ul className="doc-list">
            {documents.map((document) => (
              <li key={document.id}>
                <div>
                  <strong>{document.filename}</strong>
                  <span className={`status status-${document.status}`}>{document.status}</span>
                  <p>
                    {document.status === "ready"
                      ? `${document.chunk_count} passages`
                      : document.error_message || "Waiting"}
                  </p>
                </div>
                <button type="button" onClick={() => void onDeleteDocument(document.id)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>

          <div className="panel-head">
            <h2>Chats</h2>
            <button type="button" onClick={() => void onNewChat()}>
              New chat
            </button>
          </div>
          <ul className="chat-list">
            {conversations.map((conversation) => (
              <li key={conversation.id} className={conversation.id === activeId ? "active" : ""}>
                <button
                  type="button"
                  onClick={() =>
                    void openConversation(conversation.id).catch((reason: unknown) => {
                      setError(reason instanceof Error ? reason.message : "The chat could not be opened.");
                    })
                  }
                >
                  {conversation.title}
                </button>
                <button type="button" onClick={() => void onDeleteChat(conversation.id)} aria-label="Delete chat">
                  ×
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="panel conversation">
          <div className="messages">
            {messages.length === 0 ? (
              <p className="empty">Upload a document, then ask about a clause, date, or term.</p>
            ) : null}
            {messages.map((message) => (
              <article key={message.id} className={`bubble ${message.role}`}>
                <p>{message.content}</p>
              </article>
            ))}
          </div>
          <form onSubmit={(event) => void onAsk(event)} className="composer">
            <label>
              Search in
              <select value={selectedDocument} onChange={(event) => setSelectedDocument(event.target.value)}>
                <option value="all">All ready documents</option>
                {readyDocuments.map((document) => (
                  <option key={document.id} value={document.id}>
                    {document.filename}
                  </option>
                ))}
              </select>
            </label>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask a question about the uploaded documents"
              rows={3}
            />
            <button type="submit" disabled={busy || draft.trim().length === 0}>
              {busy ? "Working" : "Ask"}
            </button>
          </form>
        </section>

        <aside className="panel sources">
          <h2>Sources</h2>
          {citations.length === 0 ? <p className="empty">Citations for the latest answer appear here.</p> : null}
          <ol>
            {citations.map((citation) => (
              <li key={`${citation.document_id}-${citation.index}`}>
                <button
                  type="button"
                  className={activeCitation === citation.index ? "open" : ""}
                  onClick={() =>
                    setActiveCitation((current) => (current === citation.index ? null : citation.index))
                  }
                >
                  <span className="index">[{citation.index}]</span>
                  <strong>{citation.document_name}</strong>
                  {locationLabel(citation) ? <em>{locationLabel(citation)}</em> : null}
                  {citation.cited_inline ? <span className="mark">cited</span> : <span className="mark quiet">retrieved</span>}
                </button>
                {activeCitation === citation.index ? <blockquote>{citation.excerpt}</blockquote> : null}
              </li>
            ))}
          </ol>
        </aside>
      </main>
    </div>
  );
}
