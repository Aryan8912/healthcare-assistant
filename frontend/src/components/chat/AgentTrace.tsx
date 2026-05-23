const AGENT_INFO: Record<string, { label: string; color: string; bg: string; emoji: string }> = {
  appointment_agent: { label: "Appointment Agent", color: "text-blue-700",   bg: "bg-blue-50 border-blue-200",   emoji: "📅" },
  rag_agent:         { label: "Medical Q&A Agent", color: "text-green-700",  bg: "bg-green-50 border-green-200", emoji: "🔍" },
  summary_agent:     { label: "Summary Agent",     color: "text-purple-700", bg: "bg-purple-50 border-purple-200",emoji: "🧠" },
  document_agent:    { label: "Document Agent",    color: "text-orange-700", bg: "bg-orange-50 border-orange-200",emoji: "📄" },
  general:           { label: "Assistant",          color: "text-gray-700",   bg: "bg-gray-50 border-gray-200",   emoji: "🤖" },
};

interface Props {
  agent: string | null;
  isLoading: boolean;
}

export default function AgentTrace({ agent, isLoading }: Props) {
  if (!agent && !isLoading) return null;

  const info = agent ? (AGENT_INFO[agent] || AGENT_INFO.general) : AGENT_INFO.general;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${info.bg} ${info.color}`}>
      <span>{info.emoji}</span>
      <span>{isLoading ? `${info.label} is thinking` : info.label}</span>
      {isLoading && (
        <span className="flex gap-0.5">
          <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: "0ms" }} />
          <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: "150ms" }} />
          <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: "300ms" }} />
        </span>
      )}
    </div>
  );
}