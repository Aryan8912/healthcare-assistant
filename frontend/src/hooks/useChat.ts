import { useState, useCallback } from "react";
import { chatAPI, documentAPI, ChatResponse, ToolCall } from "../lib/api.ts";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_used?: string;
  tool_calls?: ToolCall[];
  timestamp: Date;
}

export function useChat() {
  const [messages, setMessages]       = useState<Message[]>([]);
  const [sessionId, setSessionId]     = useState<string | undefined>();
  const [isLoading, setIsLoading]     = useState(false);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [activeTools, setActiveTools] = useState<ToolCall[]>([]);

  const sendMessage = useCallback(async (content: string, fileId?: string) => {
    if (!content.trim()) return;

    const userMsg: Message = {
      id:        Date.now().toString(),
      role:      "user",
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setActiveTools([]);

    try {
      const res: ChatResponse = await chatAPI.sendMessage({
        message:    content,
        session_id: sessionId,
        file_id:    fileId,
      });

      if (!sessionId) setSessionId(res.session_id);
      setActiveAgent(res.agent_used);
      setActiveTools(res.tool_calls || []);

      const assistantMsg: Message = {
        id:         Date.now().toString() + "_a",
        role:       "assistant",
        content:    res.response,
        agent_used: res.agent_used,
        tool_calls: res.tool_calls,
        timestamp:  new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [...prev, {
        id:        Date.now().toString() + "_e",
        role:      "assistant",
        content:   "❌ Sorry, something went wrong. Please try again.",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
      setTimeout(() => setActiveTools([]), 3000);
    }
  }, [sessionId]);

  const uploadAndAnalyze = useCallback(async (file: File) => {
    // Step 1 — show uploading message
    const userMsg: Message = {
      id:        Date.now().toString(),
      role:      "user",
      content:   `📎 Uploaded: ${file.name}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setActiveTools([{ tool: "process_document", status: "calling" }]);

    try {
      // Step 2 — upload file
      const uploadRes = await documentAPI.uploadDocument(file);
      const fileId    = uploadRes.file_id;

      // Step 3 — send to document agent via chat
      const res: ChatResponse = await chatAPI.sendMessage({
        message:    `Analyze this uploaded document: ${file.name}`,
        session_id: sessionId,
        file_id:    fileId,
      });

      if (!sessionId) setSessionId(res.session_id);
      setActiveAgent(res.agent_used);
      setActiveTools(res.tool_calls || []);

      setMessages(prev => [...prev, {
        id:         Date.now().toString() + "_a",
        role:       "assistant",
        content:    res.response,
        agent_used: res.agent_used,
        tool_calls: res.tool_calls,
        timestamp:  new Date(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id:        Date.now().toString() + "_e",
        role:      "assistant",
        content:   "❌ Failed to process document. Please try again.",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
      setTimeout(() => setActiveTools([]), 3000);
    }
  }, [sessionId]);

  const clearChat = useCallback(async () => {
    if (sessionId) await chatAPI.clearHistory(sessionId);
    setMessages([]);
    setSessionId(undefined);
    setActiveAgent(null);
    setActiveTools([]);
  }, [sessionId]);

  return { messages, sessionId, isLoading, activeAgent, activeTools, sendMessage, uploadAndAnalyze, clearChat };
}