import { Message } from "../../hooks/useChat";
import ToolCallBadge from "./ToolCallBadge";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>

        {/* Agent badge */}
        {!isUser && message.agent_used && (
          <span className="text-xs text-gray-400 ml-1">
            {message.agent_used.replace("_", " ")}
          </span>
        )}

        {/* Tool calls */}
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <ToolCallBadge toolCalls={message.tool_calls} />
        )}

        {/* Message bubble */}
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-white text-gray-800 border border-gray-100 rounded-bl-sm shadow-sm"
        }`}>
          {message.content}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-gray-400 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}