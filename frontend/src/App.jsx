
import { useState, useRef, useEffect } from "react";
import axios from "axios";

import {
  Database,
  Send,
  Bot,
  User,
  Code,
  Table,
  Loader2,
  Sparkles,
  Trash2,
  AlertCircle,
  Copy,
  Check,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  MessageSquare,
  Pencil,
} from "lucide-react";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

const API_URL = "https://textsql-d6io.onrender.com";
const PAGE_SIZE = 10;


// ==================================================
// FORMAT CHAT DATE
// ==================================================

function formatChatDate(dateString) {
  if (!dateString) return "";

  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}


// ==================================================
// FORMAT DATABASE VALUES
// ==================================================

function formatCellValue(column, value) {
  if (value === null || value === undefined) {
    return "NULL";
  }

  const columnName = column.toLowerCase();

  if (
    ["salary", "sale_amount", "total_sales"].includes(columnName)
  ) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(value));
  }

  if (columnName === "performance_rating") {
    return Number(value).toFixed(2);
  }

  if (typeof value === "number") {
    return new Intl.NumberFormat("en-IN").format(value);
  }

  return String(value);
}


// ==================================================
// RESULTS TABLE
// ==================================================

function ResultsTable({ data }) {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");
  const [currentPage, setCurrentPage] = useState(1);

  const columns = data?.columns || [];
  const rows = data?.rows || [];

  const sortedRows = [...rows].sort((a, b) => {
    if (!sortColumn) return 0;

    const first = a[sortColumn];
    const second = b[sortColumn];

    if (first == null) return second == null ? 0 : 1;
    if (second == null) return -1;

    let comparison;

    if (
      typeof first === "number" &&
      typeof second === "number"
    ) {
      comparison = first - second;
    } else {
      comparison = String(first).localeCompare(
        String(second),
        undefined,
        {
          numeric: true,
          sensitivity: "base",
        }
      );
    }

    return sortDirection === "asc"
      ? comparison
      : -comparison;
  });

  const totalPages = Math.max(
    1,
    Math.ceil(sortedRows.length / PAGE_SIZE)
  );

  const safePage = Math.min(currentPage, totalPages);
  const startIndex = (safePage - 1) * PAGE_SIZE;

  const visibleRows = sortedRows.slice(
    startIndex,
    startIndex + PAGE_SIZE
  );

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection((previous) =>
        previous === "asc" ? "desc" : "asc"
      );
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }

    setCurrentPage(1);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">

      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Table size={17} className="text-blue-400" />
          <span className="text-sm font-semibold">
            Query Results
          </span>
        </div>

        <span className="text-xs text-slate-400">
          {rows.length} rows
        </span>
      </div>

      {rows.length > 0 ? (
        <div className="overflow-auto max-h-[420px]">
          <table className="w-full text-sm text-left">
            <thead className="sticky top-0 z-10 bg-slate-800 text-slate-300">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    className="px-4 py-3 font-medium whitespace-nowrap"
                  >
                    <button
                      onClick={() => handleSort(column)}
                      className="flex items-center gap-2 hover:text-blue-400 transition"
                    >
                      {column}

                      <span className="text-blue-400">
                        {sortColumn === column
                          ? sortDirection === "asc"
                            ? "↑"
                            : "↓"
                          : "↕"}
                      </span>
                    </button>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {visibleRows.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className="border-t border-slate-800 hover:bg-slate-800/60 transition"
                >
                  {columns.map((column) => (
                    <td
                      key={column}
                      className="px-4 py-3 whitespace-nowrap text-slate-300"
                    >
                      {formatCellValue(column, row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="p-4 text-sm text-slate-400">
          No records found.
        </p>
      )}

      {rows.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-t border-slate-800">
          <span className="text-xs text-slate-400">
            Showing {startIndex + 1}–
            {Math.min(startIndex + PAGE_SIZE, rows.length)}
            {" "}of {rows.length} rows
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                setCurrentPage((page) => Math.max(1, page - 1))
              }
              disabled={safePage === 1}
              className="px-3 py-1.5 rounded-lg bg-slate-800 text-sm hover:bg-slate-700 disabled:opacity-40"
            >
              Previous
            </button>

            <span className="text-xs text-slate-400">
              Page {safePage} of {totalPages}
            </span>

            <button
              onClick={() =>
                setCurrentPage((page) =>
                  Math.min(totalPages, page + 1)
                )
              }
              disabled={safePage === totalPages}
              className="px-3 py-1.5 rounded-lg bg-slate-800 text-sm hover:bg-slate-700 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}

      <div className="px-4 py-3 border-t border-slate-800 text-xs text-slate-400 flex flex-wrap gap-4">
        <span>
          Execution time: {data?.execution_time_ms ?? "N/A"} ms
        </span>

        {data?.truncated && (
          <span className="text-amber-400">
            Results limited to 100 rows.
          </span>
        )}
      </div>
    </div>
  );
}


// ==================================================
// MAIN APPLICATION
// ==================================================

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedIndex, setCopiedIndex] = useState(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatSessions, setChatSessions] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(true);

  const messagesEndRef = useRef(null);


  // ==================================================
  // LOAD SAVED CHATS
  // ==================================================

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setHistoryLoading(true);

        const response = await axios.get(
          `${API_URL}/chat-history`
        );

        const savedChats = response.data.chats || [];

        const formattedChats = savedChats.map((chat) => {
          const chatMessages = chat.messages || [];

          const lastAssistantMessage = [...chatMessages]
            .reverse()
            .find((message) => message.role === "assistant");

          return {
            id: chat.chat_id,
            title: chat.title,
            messages: chatMessages,
            createdAt: chat.created_at,
            updatedAt: chat.updated_at,

            conversationId:
              lastAssistantMessage?.type === "clarification"
                ? lastAssistantMessage.conversationId || null
                : null,
          };
        });

        setChatSessions(formattedChats);

      } catch (error) {
        console.error("Unable to load chat history:", error);
        setError("Unable to load saved conversations.");
      } finally {
        setHistoryLoading(false);
      }
    };

    fetchHistory();
  }, []);


  // ==================================================
  // AUTO SCROLL
  // ==================================================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);


  // ==================================================
  // SAVE CURRENT CHAT IN SIDEBAR
  // ==================================================

  const saveCurrentChat = () => {
    if (messages.length === 0) return;

    const chatId = activeChatId || crypto.randomUUID();

    const firstQuestion = messages.find(
      (message) => message.role === "user"
    );

    const chatTitle = firstQuestion
      ? firstQuestion.content.slice(0, 35)
      : "New conversation";

    const chat = {
      id: chatId,
      title: chatTitle,
      messages,
      conversationId,
      updatedAt: new Date().toISOString(),
    };

    setChatSessions((previous) => [
      chat,
      ...previous.filter((item) => item.id !== chatId),
    ]);
  };


  // ==================================================
  // START NEW CHAT
  // ==================================================

  const startNewChat = () => {
    saveCurrentChat();

    setMessages([]);
    setQuestion("");
    setConversationId(null);
    setActiveChatId(null);
    setError("");
    setCopiedIndex(null);
  };


  // ==================================================
  // OPEN PREVIOUS CHAT
  // ==================================================

  const openChat = (chat) => {
    if (activeChatId === chat.id) return;

    saveCurrentChat();

    setMessages(chat.messages || []);
    setConversationId(chat.conversationId || null);
    setActiveChatId(chat.id);

    setQuestion("");
    setError("");
    setCopiedIndex(null);
  };


  // ==================================================
  // DELETE CHAT
  // ==================================================

  const handleDeleteChat = async (chatId) => {
    try {
      await axios.delete(
        `${API_URL}/chat-history/${chatId}`
      );

      setChatSessions((previous) =>
        previous.filter((chat) => chat.id !== chatId)
      );

      if (activeChatId === chatId) {
        setMessages([]);
        setConversationId(null);
        setActiveChatId(null);
        setQuestion("");
        setError("");
        setCopiedIndex(null);
      }

    } catch (error) {
      console.error("Unable to delete chat:", error);
      setError("Unable to delete this conversation.");
    }
  };


  // ==================================================
  // RENAME CHAT
  // ==================================================

  const handleRenameChat = async (chat) => {
    const newTitle = window.prompt(
      "Enter a new chat title:",
      chat.title
    );

    if (newTitle === null) return;

    const trimmedTitle = newTitle.trim();

    if (!trimmedTitle) {
      setError("Chat title cannot be empty.");
      return;
    }

    if (trimmedTitle.length > 200) {
      setError("Chat title cannot exceed 200 characters.");
      return;
    }

    try {
      await axios.post(`${API_URL}/chat-history`, {
        chat_id: chat.id,
        title: trimmedTitle,
        messages: chat.messages,
      });

      const updatedAt = new Date().toISOString();

      setChatSessions((previous) =>
        previous.map((item) =>
          item.id === chat.id
            ? {
                ...item,
                title: trimmedTitle,
                updatedAt,
              }
            : item
        )
      );

      setError("");

    } catch (error) {
      console.error("Unable to rename chat:", error);
      setError("Unable to rename this conversation.");
    }
  };


  // ==================================================
  // COPY SQL
  // ==================================================

  const handleCopySQL = async (sql, index) => {
    try {
      await navigator.clipboard.writeText(sql);

      setCopiedIndex(index);

      setTimeout(() => {
        setCopiedIndex((previous) =>
          previous === index ? null : previous
        );
      }, 2000);

    } catch {
      setError("Unable to copy SQL. Please try again.");
    }
  };


  // ==================================================
  // SEND QUESTION OR CLARIFICATION
  // ==================================================

  const handleSend = async () => {
    if (!question.trim() || loading) return;

    const userMessage = question.trim();
    const chatId = activeChatId || crypto.randomUUID();

    setActiveChatId(chatId);
    setQuestion("");
    setError("");
    setLoading(true);

    const updatedMessages = [
      ...messages,
      {
        role: "user",
        content: userMessage,
      },
    ];

    setMessages(updatedMessages);

    try {
      let response;

      if (conversationId) {
        response = await axios.post(`${API_URL}/chat`, {
          conversation_id: conversationId,
          answer: userMessage,
        });
      } else {
        response = await axios.post(`${API_URL}/chat`, {
          question: userMessage,
        });
      }

      const result = response.data;

      let updatedConversationId = null;

      if (result.status === "needs_clarification") {
        updatedConversationId = result.conversation_id;

        updatedMessages.push({
          role: "assistant",
          type: "clarification",
          content: result.clarification,
          conversationId: updatedConversationId,
        });

      } else if (result.status === "success") {
        updatedMessages.push({
          role: "assistant",
          type: "result",
          content: "Your query was executed successfully!",
          sql: result.sql,
          data: result.data,
        });

      } else {
        throw new Error(
          result.message || "Something went wrong."
        );
      }

      setMessages([...updatedMessages]);
      setConversationId(updatedConversationId);

      const firstQuestion = updatedMessages.find(
        (message) => message.role === "user"
      );

      const chatTitle = firstQuestion
        ? firstQuestion.content.slice(0, 35)
        : "New conversation";

      // SAVE CHAT TO SUPABASE

      try {
        await axios.post(`${API_URL}/chat-history`, {
          chat_id: chatId,
          title: chatTitle,
          messages: updatedMessages,
        });

        const updatedAt = new Date().toISOString();

        setChatSessions((previous) => [
          {
            id: chatId,
            title: chatTitle,
            messages: [...updatedMessages],
            conversationId: updatedConversationId,
            updatedAt,
          },
          ...previous.filter((chat) => chat.id !== chatId),
        ]);

      } catch (saveError) {
        console.error("Unable to save conversation:", saveError);

        setError(
          "Your query worked, but the conversation could not be saved."
        );
      }

    } catch (err) {
      const errorMessage =
        err.response?.data?.message ||
        err.message ||
        "Unable to connect to the backend.";

      setError(errorMessage);

    } finally {
      setLoading(false);
    }
  };


  // ==================================================
  // KEYBOARD INPUT
  // ==================================================

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleSend();
    }
  };


  // ==================================================
  // USER INTERFACE
  // ==================================================

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">

      {/* SIDEBAR */}

      {sidebarOpen && (
        <aside className="w-64 shrink-0 bg-slate-900 border-r border-slate-800 min-h-screen p-4 flex flex-col">

          {/* LOGO */}

          <div className="flex items-center gap-2 mb-8">
            <div className="bg-blue-600 p-2 rounded-xl">
              <Database size={22} />
            </div>

            <div>
              <h1 className="text-xl font-bold">
                TextSQL
              </h1>

              <p className="text-xs text-slate-400">
                AI Database Assistant
              </p>
            </div>
          </div>


          {/* NEW CHAT */}

          <button
            onClick={startNewChat}
            className="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-500 rounded-xl py-3 text-sm font-semibold transition"
          >
            <Plus size={18} />
            New Chat
          </button>


          {/* RECENT CHATS */}

          <div className="mt-8">

            <p className="text-xs font-semibold text-slate-500 mb-3">
              RECENT CHATS
            </p>

            <div className="space-y-2">

              {chatSessions.map((chat) => (
                <div
                  key={chat.id}
                  className={`rounded-lg transition ${
                    activeChatId === chat.id
                      ? "bg-slate-800"
                      : "hover:bg-slate-800"
                  }`}
                >

                  <div className="flex items-center gap-1">

                    {/* OPEN CHAT */}

                    <button
                      onClick={() => openChat(chat)}
                      className="flex-1 min-w-0 text-left flex items-center gap-2 p-3 text-sm text-slate-300"
                    >
                      <MessageSquare
                        size={16}
                        className="shrink-0"
                      />

                      <span className="truncate">
                        {chat.title}
                      </span>
                    </button>


                    {/* RENAME CHAT */}

                    <button
                      onClick={() => handleRenameChat(chat)}
                      className="p-2 text-slate-500 hover:text-blue-400 transition"
                      title="Rename conversation"
                    >
                      <Pencil size={14} />
                    </button>


                    {/* DELETE CHAT */}

                    <button
                      onClick={() => handleDeleteChat(chat.id)}
                      className="p-2 mr-1 text-slate-500 hover:text-red-400 transition"
                      title="Delete conversation"
                    >
                      <Trash2 size={15} />
                    </button>

                  </div>


                  {/* CHAT TIMESTAMP */}

                  <p className="text-[10px] text-slate-500 px-10 pb-2">
                    {formatChatDate(chat.updatedAt)}
                  </p>

                </div>
              ))}

            </div>

            {historyLoading ? (
              <div className="flex items-center gap-2 text-xs text-slate-500 mt-3">
                <Loader2
                  size={14}
                  className="animate-spin"
                />
                Loading conversations...
              </div>
            ) : chatSessions.length === 0 ? (
              <p className="text-xs text-slate-600 mt-3">
                No previous chats yet.
              </p>
            ) : null}

          </div>


          {/* SIDEBAR FOOTER */}

          <div className="mt-auto pt-4 border-t border-slate-800">
            <p className="text-xs text-slate-500">
              TextSQL - AI Database Assistant
            </p>
          </div>

        </aside>
      )}


      {/* MAIN CONTENT */}

      <div className="flex-1 min-w-0 flex flex-col">

        {/* HEADER */}

        <header className="border-b border-slate-800 bg-slate-900 px-4 md:px-6 py-4">

          <div className="max-w-6xl mx-auto flex items-center justify-between">

            <div className="flex items-center gap-3">

              <button
                onClick={() =>
                  setSidebarOpen((previous) => !previous)
                }
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 transition"
                title="Toggle sidebar"
              >
                {sidebarOpen ? (
                  <PanelLeftClose size={20} />
                ) : (
                  <PanelLeftOpen size={20} />
                )}
              </button>

              <div className="bg-blue-600 p-2 rounded-xl">
                <Database size={22} />
              </div>

              <div>
                <h1 className="text-xl font-bold">
                  TextSQL
                </h1>

                <p className="text-xs text-slate-400">
                  AI Database Assistant
                </p>
              </div>

            </div>

            <button
              onClick={startNewChat}
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
            >
              <Trash2 size={17} />
              <span className="hidden sm:inline">
                Clear chat
              </span>
            </button>

          </div>

        </header>


        {/* CHAT AREA */}

        <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-8 flex flex-col">

          {/* WELCOME SCREEN */}

          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-16">

              <div className="bg-blue-600/10 border border-blue-500/20 rounded-2xl p-5 mb-6">
                <Sparkles
                  size={40}
                  className="text-blue-400"
                />
              </div>

              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ask your database anything.
              </h2>

              <p className="text-slate-400 max-w-lg mb-8">
                Convert natural language into SQL queries,
                clarify ambiguous questions, and get instant
                database results.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">

                {[
                  "Show all employees",
                  "Show employees earning more than 60000",
                  "Show total sales by employee",
                  "Show the best employees",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setQuestion(suggestion)}
                    className="text-left p-4 rounded-xl border border-slate-800 bg-slate-900 hover:border-blue-500 hover:bg-slate-800 transition text-sm"
                  >
                    <Sparkles
                      size={16}
                      className="text-blue-400 mb-2"
                    />
                    {suggestion}
                  </button>
                ))}

              </div>

            </div>
          )}


          {/* CHAT MESSAGES */}

          <div className="flex-1 space-y-6">

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >

                {message.role === "assistant" && (
                  <div className="w-9 h-9 shrink-0 rounded-xl bg-blue-600 flex items-center justify-center">
                    <Bot size={20} />
                  </div>
                )}

                <div className="max-w-[90%] md:max-w-[80%] min-w-0">

                  {/* USER MESSAGE */}

                  {message.role === "user" && (
                    <div className="bg-blue-600 px-4 py-3 rounded-2xl rounded-tr-sm">

                      <div className="flex items-center gap-2 mb-1 text-blue-100 text-xs">
                        <User size={13} />
                        You
                      </div>

                      <p className="text-sm">
                        {message.content}
                      </p>

                    </div>
                  )}


                  {/* ASSISTANT MESSAGE */}

                  {message.role === "assistant" && (
                    <div className="space-y-3">

                      <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm p-4">

                        <p className="text-sm text-slate-200">
                          {message.content}
                        </p>

                        {message.type === "clarification" && (
                          <div className="mt-3 flex items-center gap-2 text-xs text-blue-400">
                            <Sparkles size={14} />
                            Please provide more details.
                          </div>
                        )}

                      </div>


                      {/* SQL RESULT */}

                      {message.type === "result" && (
                        <>

                          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">

                            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">

                              <div className="flex items-center gap-2">
                                <Code
                                  size={17}
                                  className="text-blue-400"
                                />

                                <span className="text-sm font-semibold">
                                  Generated SQL
                                </span>
                              </div>

                              <button
                                onClick={() =>
                                  handleCopySQL(message.sql, index)
                                }
                                className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                              >
                                {copiedIndex === index ? (
                                  <>
                                    <Check
                                      size={14}
                                      className="text-green-400"
                                    />
                                    <span className="text-green-400">
                                      Copied!
                                    </span>
                                  </>
                                ) : (
                                  <>
                                    <Copy size={14} />
                                    <span>Copy SQL</span>
                                  </>
                                )}
                              </button>

                            </div>

                            <div className="overflow-x-auto text-sm">
                              <SyntaxHighlighter
                                language="sql"
                                style={vscDarkPlus}
                                customStyle={{
                                  margin: 0,
                                  padding: "20px",
                                  background: "#0f172a",
                                  fontSize: "13px",
                                  lineHeight: "1.7",
                                  whiteSpace: "pre-wrap",
                                  overflowWrap: "anywhere",
                                  wordBreak: "break-word",
                                }}
                                wrapLongLines={true}
                              >
                                {message.sql}
                              </SyntaxHighlighter>
                            </div>

                          </div>

                          <ResultsTable data={message.data} />

                        </>
                      )}

                    </div>
                  )}

                </div>

              </div>
            ))}


            {/* LOADING */}

            {loading && (
              <div className="flex items-center gap-3">

                <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center">
                  <Bot size={20} />
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center gap-2 text-sm text-slate-400">

                  <Loader2
                    size={16}
                    className="animate-spin text-blue-400"
                  />

                  Thinking...

                </div>

              </div>
            )}

            <div ref={messagesEndRef} />

          </div>


          {/* ERROR MESSAGE */}

          {error && (
            <div className="mb-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex gap-2">

              <AlertCircle
                size={18}
                className="shrink-0"
              />

              {error}

            </div>
          )}


          {/* MESSAGE INPUT */}

          <div className="sticky bottom-0 pt-4 pb-3 bg-slate-950">

            <div className="flex items-end gap-3 bg-slate-900 border border-slate-700 rounded-2xl p-3 focus-within:border-blue-500 transition">

              <textarea
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                onKeyDown={handleKeyDown}
                placeholder={
                  conversationId
                    ? "Type your clarification answer..."
                    : "Ask your database a question..."
                }
                rows={1}
                disabled={loading}
                className="flex-1 bg-transparent outline-none resize-none text-sm text-white placeholder-slate-500 px-2 py-2 max-h-32"
              />

              <button
                onClick={handleSend}
                disabled={!question.trim() || loading}
                className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white p-3 rounded-xl transition"
                title="Send message"
              >
                {loading ? (
                  <Loader2
                    size={19}
                    className="animate-spin"
                  />
                ) : (
                  <Send size={19} />
                )}
              </button>

            </div>

            <p className="text-center text-xs text-slate-600 mt-3">
              TextSQL can make mistakes. Always review generated SQL.
            </p>

          </div>

        </main>

      </div>

    </div>
  );
}

export default App;
