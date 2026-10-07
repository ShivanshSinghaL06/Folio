import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
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
import { About } from "./About";
import type { ChatMessage, Citation, Conversation, DocumentRecord } from "./types";

const SUGGESTIONS = [
  "Summarize the main points",
  "What dates or deadlines are mentioned?",
  "List the key obligations",
];

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

function FolioMark({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="#18181b" />
      <rect x="13.6" y="6.4" width="11.2" height="15.2" rx="1.8" fill="#ffffff" opacity="0.32" />
      <path
        fill="#ffffff"
        d="M8.1 11h6.7l3.7 3.6v8.4c0 .9-.7 1.6-1.6 1.6H8.1c-.9 0-1.6-.7-1.6-1.6v-10.4c0-.9.7-1.6 1.6-1.6z"
      />
      <path fill="#d4d4d8" d="M14.8 11v2.7c0 .5.4.9.9.9h2.8z" />
      <path d="M9.1 17.5h5.3M9.1 20.2h3.5" stroke="#18181b" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

function IconPlus() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 3.25v9.5M3.25 8h9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function IconClose() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function IconSend() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 12.5V3.5M4.5 7 8 3.5 11.5 7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconPaperclip() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M6.2 8.6 10 4.8a2.1 2.1 0 0 1 3 3L7.4 13.4a3.2 3.2 0 0 1-4.5-4.5l5.5-5.5"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IconMenu() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedDocument, setSelectedDocument] = useState("all");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSource, setOpenSource] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [path, setPath] = useState(() => window.location.pathname);
  const fileRef = useRef<HTMLInputElement>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const readyDocuments = documents.filter((document) => document.status === "ready");
  const activeTitle = useMemo(
    () => conversations.find((conversation) => conversation.id === activeId)?.title ?? "New chat",
    [conversations, activeId],
  );

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

  useEffect(() => {
    const syncPath = () => setPath(window.location.pathname);
    window.addEventListener("popstate", syncPath);
    return () => window.removeEventListener("popstate", syncPath);
  }, []);

  function navigate(href: string) {
    window.history.pushState({}, "", href);
    setPath(window.location.pathname);
    setSidebarOpen(false);
  }

  useEffect(() => {
    if (messages.length === 0 && !asking) {
      return;
    }
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, asking]);

  function resizeComposer(element: HTMLTextAreaElement) {
    element.style.height = "0px";
    element.style.height = `${Math.min(element.scrollHeight, 160)}px`;
  }

  async function openConversation(id: string) {
    setError(null);
    const detail = await getConversation(id);
    setActiveId(detail.id);
    setMessages(detail.messages);
    setOpenSource(null);
    setSidebarOpen(false);
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
      setOpenSource(null);
      setSidebarOpen(false);
      composerRef.current?.focus();
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

  async function submitQuestion(content: string) {
    if (!content || busy) {
      return;
    }
    setBusy(true);
    setAsking(true);
    setError(null);
    setDraft("");
    if (composerRef.current) {
      composerRef.current.style.height = "48px";
    }
    const optimisticId = `local-${Date.now()}`;
    setMessages((current) => [
      ...current,
      {
        id: optimisticId,
        role: "user",
        content,
        citations: [],
        created_at: new Date().toISOString(),
      },
    ]);
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
      setMessages((current) => [
        ...current.filter((message) => message.id !== optimisticId),
        result.user_message,
        result.assistant_message,
      ]);
      setOpenSource(null);
      await refreshLibrary();
    } catch (reason: unknown) {
      setMessages((current) => current.filter((message) => message.id !== optimisticId));
      setDraft(content);
      setError(reason instanceof Error ? reason.message : "The question could not be answered.");
    } finally {
      setBusy(false);
      setAsking(false);
    }
  }

  function onAsk(event: FormEvent) {
    event.preventDefault();
    void submitQuestion(draft.trim());
  }

  return (
    <div className="app">
      <aside className={sidebarOpen ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <FolioMark className="mark" />
          <div className="brand-copy">
            <strong>Folio</strong>
            <span>Ask your documents</span>
          </div>
        </div>
        <button type="button" className="ghost" onClick={() => void onNewChat()}>
          <IconPlus />
          New chat
        </button>

        <p className="section-label">Chats</p>
        <div className="scroll-list threads">
          {conversations.length === 0 ? <p className="hint">No chats yet.</p> : null}
          {conversations.map((conversation) => (
            <div key={conversation.id} className={conversation.id === activeId ? "thread active" : "thread"}>
              <button
                type="button"
                className="thread-main"
                onClick={() =>
                  void openConversation(conversation.id).catch((reason: unknown) => {
                    setError(reason instanceof Error ? reason.message : "The chat could not be opened.");
                  })
                }
              >
                {conversation.title}
              </button>
              <button type="button" className="icon-btn" aria-label="Delete chat" onClick={() => void onDeleteChat(conversation.id)}>
                <IconClose />
              </button>
            </div>
          ))}
        </div>

        <p className="section-label">Documents</p>
        <button type="button" className="ghost" onClick={() => fileRef.current?.click()} disabled={busy}>
          <IconPlus />
          Add document
        </button>
        <div className="scroll-list">
          {documents.length === 0 ? <p className="hint">PDF and Word files.</p> : null}
          {documents.map((document) => (
            <div key={document.id} className="doc">
              <div className="doc-main">
                <strong>{document.filename}</strong>
                <span className={document.status === "failed" ? "meta failed" : "meta"}>
                  {document.status === "ready"
                    ? `${document.chunk_count} passages`
                    : document.error_message || document.status}
                </span>
              </div>
              <button type="button" className="icon-btn" aria-label={`Remove ${document.filename}`} onClick={() => void onDeleteDocument(document.id)}>
                <IconClose />
              </button>
            </div>
          ))}
        </div>
        <a
          href="/about"
          className={path === "/about" ? "nav-link active" : "nav-link"}
          aria-current={path === "/about" ? "page" : undefined}
          onClick={(event) => {
            event.preventDefault();
            navigate("/about");
          }}
        >
          About
        </a>
      </aside>
      {sidebarOpen ? <button type="button" className="backdrop" aria-label="Close menu" onClick={() => setSidebarOpen(false)} /> : null}

      <section className="thread-col">
        <div className="mobile-bar">
          <button type="button" className="menu-btn" aria-label="Open menu" onClick={() => setSidebarOpen(true)}>
            <IconMenu />
          </button>
          <strong>{path === "/about" ? "About" : activeTitle}</strong>
        </div>

        {path === "/about" ? (
          <div className="viewport">
            <About onNavigate={navigate} />
          </div>
        ) : null}

        {path === "/about" ? null : <div className="viewport">
          <div className="column">
            {error ? (
              <p className="banner" role="alert">
                {error}
              </p>
            ) : null}
            {messages.length === 0 && !asking ? (
              <div className="welcome">
                <FolioMark className="welcome-mark" />
                <h1>How can I help with your documents?</h1>
                <p className="empty-copy">
                  {readyDocuments.length === 0
                    ? "Add a PDF or Word file, then ask about a clause, date, or term."
                    : "Answers stay tied to the page or section they came from."}
                </p>
                <div className="suggestions">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => {
                        setDraft(suggestion);
                        composerRef.current?.focus();
                      }}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {messages.map((message) =>
              message.role === "user" ? (
                <article key={message.id} className="message user">
                  <div className="user-bubble">
                    <p>{message.content}</p>
                  </div>
                </article>
              ) : (
                <article key={message.id} className="message assistant">
                  <FolioMark className="avatar" />
                  <div>
                    <div className="assistant-body">
                      <p>{message.content}</p>
                    </div>
                    {message.citations.length > 0 ? (
                      <div className="sources">
                        {message.citations.map((citation) => {
                          const key = `${message.id}:${citation.index}`;
                          const where = locationLabel(citation);
                          return (
                            <div key={key} className="source">
                              <button
                                type="button"
                                className="source-toggle"
                                aria-expanded={openSource === key}
                                onClick={() => setOpenSource((current) => (current === key ? null : key))}
                              >
                                <span className="source-index">[{citation.index}]</span>
                                <span className="source-name">
                                  {citation.document_name}
                                  {where ? ` · ${where}` : ""}
                                </span>
                                <span className={citation.cited_inline ? "pill cited" : "pill"}>
                                  {citation.cited_inline ? "Cited" : "Retrieved"}
                                </span>
                              </button>
                              {openSource === key ? <blockquote>{citation.excerpt}</blockquote> : null}
                            </div>
                          );
                        })}
                      </div>
                    ) : null}
                  </div>
                </article>
              ),
            )}
            {asking ? (
              <article className="message assistant" aria-live="polite">
                <FolioMark className="avatar" />
                <p className="pending dots">Looking through your documents</p>
              </article>
            ) : null}
            <div ref={endRef} />
          </div>
        </div>}

        {path === "/about" ? null : <form className="composer-wrap" onSubmit={onAsk}>
          <div className="composer">
            <textarea
              ref={composerRef}
              value={draft}
              rows={1}
              placeholder="Ask about your documents"
              onChange={(event) => {
                setDraft(event.target.value);
                resizeComposer(event.target);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submitQuestion(draft.trim());
                }
              }}
            />
            <div className="composer-bar">
              <button type="button" className="attach" aria-label="Add document" disabled={busy} onClick={() => fileRef.current?.click()}>
                <IconPaperclip />
              </button>
              <select className="scope" value={selectedDocument} aria-label="Search in" onChange={(event) => setSelectedDocument(event.target.value)}>
                <option value="all">All documents</option>
                {readyDocuments.map((document) => (
                  <option key={document.id} value={document.id}>
                    {document.filename}
                  </option>
                ))}
              </select>
              <button type="submit" className="send" aria-label="Send" disabled={busy || draft.trim().length === 0}>
                <IconSend />
              </button>
            </div>
          </div>
          <p className="disclaimer">Folio cites the passage an answer came from. Check the source before you rely on it.</p>
        </form>}
        <input
          ref={fileRef}
          type="file"
          hidden
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            void onUpload(file);
          }}
        />
      </section>
    </div>
  );
}
