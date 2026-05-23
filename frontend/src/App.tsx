import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Chat from "./pages/patient/Chat.tsx";
import Appointments from "./pages/patient/Appointments.tsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/appointments" element={<Appointments />} />
      </Routes>
    </BrowserRouter>
  );
}