import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { useChat } from "../../hooks/useChat.ts";
import MessageBubble from "../../components/chat/MessageBubble.tsx";
import ToolCallBadge from "../../components/chat/ToolCallBadge.tsx";
import AgentTrace from "../../components/chat/AgentTrace.tsx";

const SUGGESTIONS = [
  "Show me all available doctors",
  "What are the symptoms of diabetes?",
  "Book an appointment with a cardiologist",
  "What departments are available?",
];

export default function Chat() {
  const { messages, isLoading, activeAgent, activeTools, sendMessage, uploadAndAnalyze, clearChat } = useChat();
  const [input, setInput]         = useState("");
  const [uploading, setUploading] = useState(false);
  const bottomRef                 = useRef<HTMLDivElement>(null);
  const fileRef                   = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    await uploadAndAnalyze(file);
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">M</div>
          <div>
            <h1 className="font-semibold text-gray-900 text-sm">MedAssist AI</h1>
            <p className="text-xs text-green-500 font-medium">● Online</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/appointments" className="text-xs bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg font-medium hover:bg-blue-100 transition-colors">
            📅 Appointments
          </Link>
          <button onClick={clearChat} className="text-xs text-gray-500 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            🗑️ Clear
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <div className="text-center">
              <div className="text-5xl mb-3">🏥</div>
              <h2 className="text-xl font-semibold text-gray-800 mb-1">MedAssist Healthcare AI</h2>
              <p className="text-gray-500 text-sm">Book appointments, get medical info, analyze documents</p>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full max-w-md">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => sendMessage(s)}
                  className="text-left text-xs bg-white border border-gray-200 rounded-xl px-3 py-2.5 text-gray-600 hover:border-blue-300 hover:bg-blue-50 transition-all">
                  {s}
                </button>
              ))}
            </div>
            {/* Document upload hint */}
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span>📎</span>
              <span>Click the attachment icon below to upload a PDF or image for analysis</span>
            </div>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="max-w-[80%] flex flex-col gap-1 items-start">
                  <AgentTrace agent={activeAgent} isLoading={isLoading} />
                  {activeTools.length > 0 && <ToolCallBadge toolCalls={activeTools} />}
                  <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <div className="max-w-2xl mx-auto">
          {/* Upload hint */}
          <div className="flex items-center gap-2 mb-2">
            <button onClick={() => fileRef.current?.click()} disabled={uploading || isLoading}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-blue-600 px-2 py-1 rounded-lg hover:bg-blue-50 transition-colors">
              <span>{uploading ? "⏳" : "📎"}</span>
              <span>{uploading ? "Uploading..." : "Upload PDF or Image"}</span>
            </button>
            <span className="text-xs text-gray-300">•</span>
            <span className="text-xs text-gray-400">Supports lab reports, prescriptions, X-rays</span>
          </div>

          <div className="flex items-end gap-2">
            <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" className="hidden" onChange={handleFileUpload} />
            <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Ask about appointments, medical questions, or upload a document..."
              rows={1}
              className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 bg-gray-50" />
            <button onClick={handleSend} disabled={isLoading || !input.trim()}
              className="bg-blue-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0">
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}