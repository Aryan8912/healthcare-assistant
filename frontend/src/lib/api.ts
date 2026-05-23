/**
 * api.ts — All backend API calls for MedAssist Healthcare Assistant
 */

const BASE_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : "http://localhost:8000/api";

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  agent_used: string;
  intent: string;
  tool_calls: ToolCall[];
}

export interface ToolCall {
  tool: string;
  status: string;
}

export interface Doctor {
  id: number;
  name: string;
  department: string;
  specialization: string;
  experience: number;
  available_days: string;
  available_time: string;
  fee: number;
  languages: string;
}

export interface Appointment {
  id: number;
  patient: string;
  doctor: string;
  department: string;
  date: string;
  time_slot: string;
  status: string;
  reason: string;
}

export interface BookAppointmentRequest {
  patient_name: string;
  patient_phone: string;
  patient_email?: string;
  doctor_id: number;
  date: string;
  time_slot: string;
  reason?: string;
}

export const chatAPI = {
  sendMessage: async (req: ChatRequest): Promise<ChatResponse> => {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error("Chat request failed");
    return res.json();
  },

  getHistory: async (session_id: string) => {
    const res = await fetch(`${BASE_URL}/chat/history/${session_id}`);
    if (!res.ok) throw new Error("Failed to get history");
    return res.json();
  },

  clearHistory: async (session_id: string) => {
    const res = await fetch(`${BASE_URL}/chat/history/${session_id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to clear history");
    return res.json();
  },
};

export const appointmentAPI = {
  getDoctors: async (): Promise<{ total: number; doctors: Doctor[] }> => {
    const res = await fetch(`${BASE_URL}/doctors`);
    if (!res.ok) throw new Error("Failed to get doctors");
    return res.json();
  },

  getSlots: async (doctor_id: number, date: string) => {
    const res = await fetch(
      `${BASE_URL}/appointments/slots?doctor_id=${doctor_id}&date=${date}`
    );
    if (!res.ok) throw new Error("Failed to get slots");
    return res.json();
  },

  bookAppointment: async (req: BookAppointmentRequest) => {
    const res = await fetch(`${BASE_URL}/appointments/book`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error("Failed to book appointment");
    return res.json();
  },

  getAppointment: async (id: number): Promise<Appointment> => {
    const res = await fetch(`${BASE_URL}/appointments/${id}`);
    if (!res.ok) throw new Error("Failed to get appointment");
    return res.json();
  },

  cancelAppointment: async (id: number) => {
    const res = await fetch(`${BASE_URL}/appointments/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to cancel appointment");
    return res.json();
  },

  getHistory: async (phone: string) => {
    const res = await fetch(`${BASE_URL}/appointments/history/${phone}`);
    if (!res.ok) throw new Error("Failed to get appointment history");
    return res.json();
  },
};

export const documentAPI = {
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Failed to upload document");
    return res.json();
  },

  analyzeDocument: async (file_id: string) => {
    const res = await fetch(`${BASE_URL}/documents/analyze/${file_id}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to analyze document");
    return res.json();
  },

  listDocuments: async () => {
    const res = await fetch(`${BASE_URL}/documents/list`);
    if (!res.ok) throw new Error("Failed to list documents");
    return res.json();
  },
};