import { ToolCall } from "../../lib/api.ts";

const TOOL_INFO: Record<string, { label: string; doing: string; done: string; emoji: string; color: string; doneColor: string }> = {
  fetch_slots:            { label: "Slots",         doing: "Fetching available slots...",   done: "Slots fetched ✓",          emoji: "🔄", color: "bg-blue-100 text-blue-700 border-blue-200",     doneColor: "bg-blue-50 text-blue-500 border-blue-100" },
  book_appointment:       { label: "Booking",       doing: "Booking appointment...",        done: "Appointment confirmed ✓",   emoji: "📝", color: "bg-green-100 text-green-700 border-green-200",   doneColor: "bg-green-50 text-green-500 border-green-100" },
  cancel_appointment:     { label: "Cancelling",    doing: "Cancelling appointment...",     done: "Appointment cancelled ✓",   emoji: "❌", color: "bg-red-100 text-red-700 border-red-200",         doneColor: "bg-red-50 text-red-500 border-red-100" },
  modify_appointment:     { label: "Rescheduling",  doing: "Rescheduling appointment...",   done: "Appointment rescheduled ✓", emoji: "🔁", color: "bg-yellow-100 text-yellow-700 border-yellow-200", doneColor: "bg-yellow-50 text-yellow-500 border-yellow-100" },
  retrieve_appointments:  { label: "History",       doing: "Retrieving appointments...",    done: "History retrieved ✓",       emoji: "📖", color: "bg-purple-100 text-purple-700 border-purple-200", doneColor: "bg-purple-50 text-purple-500 border-purple-100" },
  get_doctors:            { label: "Doctors",       doing: "Fetching doctors...",           done: "Doctors fetched ✓",         emoji: "👨‍⚕️", color: "bg-indigo-100 text-indigo-700 border-indigo-200", doneColor: "bg-indigo-50 text-indigo-500 border-indigo-100" },
  retrieve_documents:     { label: "Documents",     doing: "Retrieving documents...",       done: "Documents retrieved ✓",     emoji: "📄", color: "bg-orange-100 text-orange-700 border-orange-200", doneColor: "bg-orange-50 text-orange-500 border-orange-100" },
  search_knowledge_base:  { label: "Knowledge",     doing: "Searching knowledge base...",   done: "Knowledge retrieved ✓",     emoji: "🔍", color: "bg-teal-100 text-teal-700 border-teal-200",       doneColor: "bg-teal-50 text-teal-500 border-teal-100" },
  summarize_conversation: { label: "Summary",       doing: "Generating summary...",         done: "Summary generated ✓",       emoji: "🧠", color: "bg-pink-100 text-pink-700 border-pink-200",       doneColor: "bg-pink-50 text-pink-500 border-pink-100" },
  process_document:       { label: "Analyzing",     doing: "Analyzing document...",         done: "Document analyzed ✓",       emoji: "📊", color: "bg-amber-100 text-amber-700 border-amber-200",   doneColor: "bg-amber-50 text-amber-500 border-amber-100" },
  add_to_knowledge_base:  { label: "Indexing",      doing: "Adding to knowledge base...",   done: "Added to knowledge base ✓", emoji: "📚", color: "bg-cyan-100 text-cyan-700 border-cyan-200",       doneColor: "bg-cyan-50 text-cyan-500 border-cyan-100" },
};

interface Props {
  toolCalls: ToolCall[];
}

export default function ToolCallBadge({ toolCalls }: Props) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 my-1.5">
      {toolCalls.map((tc, i) => {
        const info   = TOOL_INFO[tc.tool] || { doing: tc.tool, done: `${tc.tool} ✓`, emoji: "⚙️", color: "bg-gray-100 text-gray-700 border-gray-200", doneColor: "bg-gray-50 text-gray-500 border-gray-100" };
        const isDone = tc.status === "done";

        return (
          <span key={i} className={`
            inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-300
            ${isDone ? info.doneColor : info.color}
          `}>
            {/* Spinner or emoji */}
            {!isDone ? (
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                <span>{info.doing}</span>
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <span>{info.emoji}</span>
                <span>{info.done}</span>
              </span>
            )}
          </span>
        );
      })}
    </div>
  );
}