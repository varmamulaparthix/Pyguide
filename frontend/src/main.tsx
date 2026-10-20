import { ChangeEvent, KeyboardEvent as ReactKeyboardEvent, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Archive, ChevronLeft, Copy, Download, FileCode2, FileText, FolderOpen, LogOut, Menu, MoreHorizontal, Paperclip, Pencil, Plus, Search, Send, Settings, Trash2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./style.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
type Attachment = { id: string; name: string; type: string; size: number };
type Chat = { id: string; title: string; created_at: string };
type Message = { id?: string; role: "user" | "assistant"; content: string; created_at: string; attachment_names?: string[] };

async function api(path: string, options: RequestInit = {}, token = localStorage.getItem("token") || "") {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const requestOptions = path.endsWith("/ask")
    ? { ...options, headers, signal: options.signal ?? AbortSignal.timeout(60_000) }
    : { ...options, headers };
  let response: Response;
  try {
    response = await fetch(`${API}${path}`, requestOptions);
  } catch (reason: any) {
    if (reason?.name === "TimeoutError" || reason?.name === "AbortError") {
      throw new Error("The response took too long. Your message was not sent again automatically; please retry once.");
    }
    throw new Error("Cannot reach PyGuide backend. Start FastAPI on port 8000, then try again.");
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(body.detail) ? body.detail.map((item: { msg?: string }) => item.msg || "Invalid input").join(" ") : body.detail;
    throw new Error(typeof detail === "string" ? detail : "Request failed. Please try again.");
  }
  return body;
}

function sizeLabel(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [chats, setChats] = useState<Chat[]>([]);
  const [active, setActive] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [attachmentMenu, setAttachmentMenu] = useState(false);
  const [online, setOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [chatMenu, setChatMenu] = useState<Chat | null>(null);
  const [chatMenuPosition, setChatMenuPosition] = useState({ top: 0, left: 0 });
  const [showFiles, setShowFiles] = useState(false);
  const [storedFiles, setStoredFiles] = useState<Attachment[]>([]);
  const [fileMenu, setFileMenu] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [archivedChats, setArchivedChats] = useState<Chat[]>([]);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const loadChats = async (search = query) => {
    if (!token) return;
    setChats(await api(`/chats?q=${encodeURIComponent(search)}`));
  };
  const loadFiles = async () => {
    if (!token) return;
    setStoredFiles(await api("/attachments"));
  };

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API}/health`, { signal: AbortSignal.timeout(5_000) });
        if (!response.ok) throw new Error("Health check failed");
        const data = await response.json();
        if (mounted) setOnline(data.status === "online");
      } catch {
        if (mounted) setOnline(false);
      }
    };
    void checkHealth();
    const interval = window.setInterval(() => void checkHealth(), 10_000);
    return () => { mounted = false; window.clearInterval(interval); };
  }, []);
  useEffect(() => { Promise.all([loadChats(), loadFiles()]).catch((reason) => setError(reason.message)); }, [token]);
  useEffect(() => {
    const close = (event: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(event.target as Node)) setAttachmentMenu(false); };
    const escape = (event: globalThis.KeyboardEvent) => { if (event.key === "Escape") setAttachmentMenu(false); };
    window.addEventListener("mousedown", close); window.addEventListener("keydown", escape);
    return () => { window.removeEventListener("mousedown", close); window.removeEventListener("keydown", escape); };
  }, []);

  const openChat = async (chat: Chat) => {
    try {
      setActive(chat); setMessages(await api(`/chats/${chat.id}/messages`)); setSidebarOpen(false);
    } catch (reason: any) { setError(reason.message); }
  };
  const newChat = () => {
    setActive(null); setMessages([]); setText(""); setAttachments([]); setError(""); setSidebarOpen(false);
  };
  const renameChat = async (chat: Chat) => {
    const title = window.prompt("Rename conversation", chat.title)?.trim();
    if (!title || title === chat.title) return;
    try { await api(`/chats/${chat.id}`, { method: "PATCH", body: JSON.stringify({ title }) }); await loadChats(); if (active?.id === chat.id) setActive({ ...chat, title }); } catch (reason: any) { setError(reason.message); }
  };
  const archiveChat = async (chat: Chat) => {
    try { await api(`/chats/${chat.id}/archive`, { method: "PATCH", body: JSON.stringify({ archived: true }) }); setChatMenu(null); if (active?.id === chat.id) { setActive(null); setMessages([]); } await loadChats(); } catch (reason: any) { setError(reason.message); }
  };
  const openSettings = async () => {
    try { setArchivedChats(await api("/chats?archived=true")); setShowSettings(true); } catch (reason: any) { setError(reason.message); }
  };
  const restoreChat = async (chat: Chat) => {
    try { await api(`/chats/${chat.id}/archive`, { method: "PATCH", body: JSON.stringify({ archived: false }) }); setArchivedChats((items) => items.filter((item) => item.id !== chat.id)); await loadChats(); } catch (reason: any) { setError(reason.message); }
  };
  const deleteArchivedChat = async (chat: Chat) => {
    if (!window.confirm(`Delete “${chat.title}” permanently?`)) return;
    try { await api(`/chats/${chat.id}`, { method: "DELETE" }); setArchivedChats((items) => items.filter((item) => item.id !== chat.id)); } catch (reason: any) { setError(reason.message); }
  };
  const deleteChat = async (chat: Chat) => {
    if (!window.confirm(`Delete “${chat.title}”? This permanently removes its messages.`)) return;
    try { await api(`/chats/${chat.id}`, { method: "DELETE" }); setChatMenu(null); if (active?.id === chat.id) { setActive(null); setMessages([]); } await loadChats(); } catch (reason: any) { setError(reason.message); }
  };
  const saveEditedMessage = async () => {
    const content = editingText.trim();
    if (!content || !editingMessageId) return;
    try {
      setLoading(true); setError("");
      await api(`/messages/${editingMessageId}/edit-and-ask`, { method: "POST", body: JSON.stringify({ content }) });
      if (active) setMessages(await api(`/chats/${active.id}/messages`));
      setEditingMessageId(null); setEditingText("");
      void loadChats();
    } catch (reason: any) { setError(reason.message); } finally { setLoading(false); }
  };
  const authenticate = async (login: boolean) => {
    setError("");
    if (!email.includes("@")) return setError("Enter a valid email address.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    try {
      const result = await api(`/auth/${login ? "login" : "register"}`, { method: "POST", body: JSON.stringify({ email, password }) }, "");
      localStorage.setItem("token", result.token); setToken(result.token);
    } catch (reason: any) { setError(reason.message); }
  };
  const selectFiles = () => { setAttachmentMenu(false); inputRef.current?.click(); };
  const openFiles = async () => {
    try { await loadFiles(); setShowFiles(true); setSidebarOpen(false); } catch (reason: any) { setError(reason.message); }
  };
  const deleteStoredFile = async (attachment: Attachment) => {
    if (!window.confirm(`Delete ${attachment.name}? This cannot be undone.`)) return;
    try { await api(`/attachments/${attachment.id}`, { method: "DELETE" }); setStoredFiles((items) => items.filter((item) => item.id !== attachment.id)); setAttachments((items) => items.filter((item) => item.id !== attachment.id)); } catch (reason: any) { setError(reason.message); }
  };
  const downloadStoredFile = async (attachment: Attachment) => {
    try {
      const response = await fetch(`${API}/attachments/${attachment.id}/download`, { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });
      if (!response.ok) throw new Error("The file could not be downloaded.");
      const url = URL.createObjectURL(await response.blob()); const link = document.createElement("a"); link.href = url; link.download = attachment.name; link.click(); URL.revokeObjectURL(url);
    } catch (reason: any) { setError(reason.message); }
  };
  const uploadFiles = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;
    if (attachments.length + files.length > 8) return setError("You can attach up to 8 files.");
    const form = new FormData(); files.forEach((file) => form.append("files", file));
    try {
      setLoading(true); setError("");
      const uploaded: Attachment[] = await api("/attachments", { method: "POST", body: form });
      setAttachments((items) => [...items, ...uploaded]);
      setStoredFiles((items) => [...uploaded, ...items]);
    } catch (reason: any) { setError(reason.message); } finally { setLoading(false); }
  };
  const removeAttachment = async (attachment: Attachment) => {
    setAttachments((items) => items.filter((item) => item.id !== attachment.id));
    try { await api(`/attachments/${attachment.id}`, { method: "DELETE" }); } catch (reason: any) { setError(reason.message); }
  };
  const send = async () => {
    const content = text.trim();
    if (!content) return setError("Write a Python question before sending.");
    if (loading) return;
    if (!online) return setError("PyGuide backend is offline. Start the backend, wait for the Online label, then send your message.");
    let chat = active;
    let selected: Attachment[] = [];
    let pendingMessageId = "";
    try {
      if (!chat) {
        chat = await api("/chats", { method: "POST", body: JSON.stringify({ title: "New chat" }) });
        setActive(chat);
      }
      if (!chat) return;
      selected = attachments;
      setText(""); setAttachments([]); setError(""); setLoading(true);
      pendingMessageId = crypto.randomUUID();
      setMessages((items) => [...items, { id: pendingMessageId, role: "user", content, attachment_names: selected.map((item) => item.name), created_at: new Date().toISOString() }]);
      const result = await api(`/chats/${chat.id}/ask`, { method: "POST", body: JSON.stringify({ content, attachment_ids: selected.map((item) => item.id) }) });
      setMessages((items) => [...items.map((message) => message.id === pendingMessageId ? { ...message, id: result.user_message_id || message.id } : message), { id: result.assistant_message_id, role: "assistant", content: result.content, created_at: new Date().toISOString() }]);
      void loadChats().catch((reason: any) => setError(reason.message));
    } catch (reason: any) { setMessages((items) => items.filter((message) => message.id !== pendingMessageId)); setError(reason.message); setText(content); setAttachments(selected); } finally { setLoading(false); }
  };
  const onInputKey = (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); }
  };

  if (!token) return <div className="login-shell"><section className="login"><div className="login-logo"><FileCode2 /> <b>PyGuide</b></div><h1>Welcome back</h1><p>Sign in to continue learning Python.</p><input type="email" placeholder="Email address" value={email} onChange={(event) => setEmail(event.target.value)} /><input type="password" placeholder="Password (minimum 8 characters)" value={password} onChange={(event) => setPassword(event.target.value)} /><button onClick={() => authenticate(true)}>Log in</button><button className="secondary" onClick={() => authenticate(false)}>Create account</button>{error && <p className="form-error">{error}</p>}</section></div>;

  return <div className={`app ${sidebarCollapsed ? "sidebar-is-collapsed" : ""}`}>
    <aside className={`${sidebarOpen ? "open " : ""}${sidebarCollapsed ? "collapsed" : ""}`}>
      <div className="brand"><div className="brand-mark"><FileCode2 /></div><div className="sidebar-label"><b>PyGuide</b><small>Python Learning Assistant</small></div><button className="icon collapse" title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"} onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}><ChevronLeft /></button></div>
      <button className="new" onClick={newChat}><Plus /> New Chat</button>
      <nav><button onClick={() => { setActive(null); setMessages([]); }}><FileText /> Home</button><button onClick={() => setText("Explain a Python concept with a simple example.")}><Search /> Explore</button><button onClick={openFiles}><FolderOpen /> Files <span>{storedFiles.length}</span></button><button onClick={openSettings}><Settings /> Settings</button></nav>
      <div className="recent"><h4>Recent Chats</h4>{chats.length ? chats.map((chat) => <div key={chat.id} className={active?.id === chat.id ? "chat-row selected" : "chat-row"}><button className="chat" onClick={() => openChat(chat)}><FileText /><span>{chat.title}</span></button><button className="chat-more" title={`More actions for ${chat.title}`} onClick={(event) => { event.stopPropagation(); const rect = event.currentTarget.getBoundingClientRect(); setChatMenuPosition({ top: Math.min(rect.top, window.innerHeight - 164), left: Math.min(rect.right + 8, window.innerWidth - 170) }); setChatMenu(chat); }}><MoreHorizontal /></button></div>) : <p>No conversations yet.</p>}</div>
      <footer><div className="avatar">{(email || "P").slice(0, 1).toUpperCase()}</div><div><b>{email || "PyGuide user"}</b><small>Signed in</small></div><button className="icon" title="Log out" onClick={() => { localStorage.removeItem("token"); setToken(""); }}><LogOut /></button></footer>
    </aside>
    {sidebarOpen && <button className="backdrop" aria-label="Close sidebar" onClick={() => setSidebarOpen(false)} />}
    <main>
      <header><button className="icon sidebar-toggle" title="Expand sidebar" onClick={() => { setSidebarCollapsed(false); setSidebarOpen(true); }}><Menu /></button><div className="header-title"><h2>PyGuide <i className={online ? "online" : "offline"}>{online ? "● Online" : "● Offline"}</i></h2><small>Python Learning Assistant &nbsp;|&nbsp; Ask anything about Python, coding, or errors</small></div><label className="search"><Search /><input value={query} onChange={(event) => { setQuery(event.target.value); loadChats(event.target.value).catch((reason) => setError(reason.message)); }} placeholder="Search chats..." /></label><button className="icon" title="Settings" onClick={openSettings}><Settings /></button></header>
      <section className="messages">
        {!active && !messages.length ? <div className="welcome"><h1>Let’s make Python click.</h1><p>Learn Python step by step. Ask questions, explore examples, and understand your code.</p><div><button onClick={() => setText("Explain Python variables with examples.")}>Explain a Python concept</button><button onClick={() => setText("Write a beginner Python program.")}>Write a beginner program</button></div></div> :
          messages.map((message, index) => <article key={message.id || index} className={message.role}><div className="bubble">{editingMessageId === message.id ? <div className="edit-message"><textarea value={editingText} onChange={(event) => setEditingText(event.target.value)} autoFocus /><div><button className="save-edit" onClick={saveEditedMessage} disabled={loading || !editingText.trim()}>Save & regenerate</button><button onClick={() => { setEditingMessageId(null); setEditingText(""); }}>Cancel</button></div></div> : <><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>{message.attachment_names?.length ? <div className="sent-attachments">{message.attachment_names.map((name) => <span key={name}><Paperclip />{name}</span>)}</div> : null}<div className="message-footer"><small>{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small>{message.role === "user" && message.id && !loading && <button title="Edit message" onClick={() => { setEditingMessageId(message.id || null); setEditingText(message.content); }}><Pencil /></button>}<button title="Copy message" onClick={() => navigator.clipboard.writeText(message.content)}><Copy /></button></div></>}</div></article>)}
        {loading && <article className="assistant"><div className="typing"><span /><span /><span /> Working…</div></article>}
      </section>
      <div className="composer-wrap">
        {attachments.length > 0 && <div className="attachment-list">{attachments.map((attachment) => <div className="attachment-chip" key={attachment.id}><Paperclip /><span><b>{attachment.name}</b><small>{sizeLabel(attachment.size)}</small></span><button title={`Remove ${attachment.name}`} onClick={() => removeAttachment(attachment)}><X /></button></div>)}</div>}
        <div className="composer">
          <div className="attachment-control" ref={menuRef}><button className="attach-button" aria-label="Add attachment" aria-expanded={attachmentMenu} onClick={() => setAttachmentMenu((open) => !open)}><Plus /></button>{attachmentMenu && <div className="attachment-menu" role="menu"><button role="menuitem" onClick={selectFiles}><Paperclip /><span>Add photos & files<small>Upload from computer</small></span></button><button role="menuitem" onClick={selectFiles}><FileCode2 /><span>Upload code file<small>Python, JSON, text, and more</small></span></button><button role="menuitem" disabled={!attachments.length} onClick={() => setAttachments([])}><Trash2 /><span>Clear attachments<small>Remove selected files</small></span></button></div>}</div>
          <input ref={inputRef} className="native-file-input" type="file" multiple accept=".py,.txt,.md,.pdf,.csv,.json,.log,.png,.jpg,.jpeg,.webp" onChange={uploadFiles} />
          <textarea value={text} disabled={loading} onChange={(event) => setText(event.target.value)} onKeyDown={onInputKey} placeholder="Ask anything about Python, coding, errors, or any topic..." />
          <button className="send" aria-label="Send message" title="Send message" disabled={loading || !text.trim()} onClick={send}><Send /></button>
        </div>
      </div>
      {error && <div className="error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError("")}><X /></button></div>}
      {chatMenu && <div className="chat-menu-layer" onMouseDown={() => setChatMenu(null)}><div className="chat-popover-fixed" style={{ top: chatMenuPosition.top, left: chatMenuPosition.left }} onMouseDown={(event) => event.stopPropagation()}><button onClick={() => { renameChat(chatMenu); setChatMenu(null); }}>Rename</button><button onClick={() => archiveChat(chatMenu)}><Archive /> Archive</button><button className="delete" onClick={() => deleteChat(chatMenu)}><Trash2 /> Delete</button></div></div>}
      {showFiles && <div className="modal-backdrop" onMouseDown={() => setShowFiles(false)}><section className="modal files-modal" onMouseDown={(event) => event.stopPropagation()}><div className="modal-head"><div><h2>Files</h2><p>Stored attachments for your account</p></div><button className="icon" onClick={() => setShowFiles(false)}><X /></button></div>{storedFiles.length ? <div className="file-list">{storedFiles.map((file) => <div className="file-row" key={file.id}><FileText /><div><b>{file.name}</b><small>{sizeLabel(file.size)} · {file.type || "file"}</small></div><div className="file-actions"><button className="icon" title="Download" onClick={() => downloadStoredFile(file)}><Download /></button><button className="icon" title="More file actions" onClick={() => setFileMenu(fileMenu === file.id ? null : file.id)}><MoreHorizontal /></button>{fileMenu === file.id && <div className="file-popover"><button onClick={() => deleteStoredFile(file)}><Trash2 /> Delete file</button></div>}</div></div>)}</div> : <p className="empty">No uploaded files yet. Use the plus button beside the message box.</p>}</section></div>}
      {showSettings && <div className="modal-backdrop" onMouseDown={() => setShowSettings(false)}><section className="modal settings-modal" onMouseDown={(event) => event.stopPropagation()}><div className="modal-head"><div><h2>Settings</h2><p>Account, connection, and conversation management</p></div><button className="icon" onClick={() => setShowSettings(false)}><X /></button></div><div className="settings-row"><span>Signed-in account</span><b>{email || "Current account"}</b></div><div className="settings-row"><span>Backend connection</span><b className={online ? "good" : "bad"}>{online ? "Online" : "Offline"}</b></div><div className="settings-row"><span>File support</span><b>Code, text, PDF, CSV, JSON, logs</b></div><section className="archived-section"><h3>Archived chats</h3>{archivedChats.length ? archivedChats.map((chat) => <div className="archived-row" key={chat.id}><span>{chat.title}</span><button onClick={() => restoreChat(chat)}>Restore</button><button className="trash" title="Delete permanently" onClick={() => deleteArchivedChat(chat)}><Trash2 /></button></div>) : <p>No archived chats.</p>}</section><button className="danger" onClick={() => { localStorage.removeItem("token"); setToken(""); }}>Log out</button></section></div>}
    </main>
  </div>;
}

createRoot(document.getElementById("root")!).render(<App />);
