import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { appointmentAPI, Doctor } from "../../lib/api";

export default function Appointments() {
  const [doctors, setDoctors]     = useState<Doctor[]>([]);
  const [slots, setSlots]         = useState<string[]>([]);
  const [loading, setLoading]     = useState(false);
  const [message, setMessage]     = useState("");
  const [step, setStep]           = useState<"doctors" | "slots" | "confirm" | "done">("doctors");

  const [form, setForm] = useState({
    patient_name:  "",
    patient_phone: "",
    patient_email: "",
    doctor_id:     0,
    doctor_name:   "",
    date:          "",
    time_slot:     "",
    reason:        "",
  });

  useEffect(() => {
    appointmentAPI.getDoctors().then(res => setDoctors(res.doctors));
  }, []);

  const fetchSlots = async () => {
    if (!form.doctor_id || !form.date) return;
    setLoading(true);
    const res = await appointmentAPI.getSlots(form.doctor_id, form.date);
    setSlots(res.available_slots || []);
    setStep("slots");
    setLoading(false);
  };

  const bookAppointment = async () => {
    setLoading(true);
    try {
      const res = await appointmentAPI.bookAppointment({
        patient_name:  form.patient_name,
        patient_phone: form.patient_phone,
        patient_email: form.patient_email,
        doctor_id:     form.doctor_id,
        date:          form.date,
        time_slot:     form.time_slot,
        reason:        form.reason,
      });
      setMessage(`✅ ${res.message} — Appointment ID: #${res.appointment_id}`);
      setStep("done");
    } catch {
      setMessage("❌ Booking failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 shadow-sm">
        <Link to="/chat" className="text-gray-500 hover:text-gray-700">←</Link>
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">M</div>
        <h1 className="font-semibold text-gray-900">Book Appointment</h1>
      </header>

      <div className="max-w-lg mx-auto p-4 space-y-4">

        {/* Done state */}
        {step === "done" && (
          <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-center">
            <div className="text-4xl mb-3">✅</div>
            <p className="text-green-800 font-medium">{message}</p>
            <button onClick={() => { setStep("doctors"); setMessage(""); setForm({ ...form, time_slot: "", date: "" }); }}
              className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-xl text-sm font-medium hover:bg-blue-700">
              Book Another
            </button>
          </div>
        )}

        {/* Step 1: Patient info + Doctor selection */}
        {step === "doctors" && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-3">
              <h2 className="font-semibold text-gray-800">Your Information</h2>
              <input placeholder="Full Name *" value={form.patient_name}
                onChange={e => setForm({ ...form, patient_name: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
              <input placeholder="Phone Number *" value={form.patient_phone}
                onChange={e => setForm({ ...form, patient_phone: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
              <input placeholder="Email (optional)" value={form.patient_email}
                onChange={e => setForm({ ...form, patient_email: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
            </div>

            <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-3">
              <h2 className="font-semibold text-gray-800">Select Doctor</h2>
              <div className="grid gap-2">
                {doctors.map(d => (
                  <button key={d.id} onClick={() => setForm({ ...form, doctor_id: d.id, doctor_name: d.name })}
                    className={`text-left p-3 rounded-xl border text-sm transition-all ${
                      form.doctor_id === d.id
                        ? "border-blue-400 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}>
                    <div className="font-medium text-gray-800">{d.name}</div>
                    <div className="text-gray-500 text-xs">{d.department} • ₹{d.fee} • {d.available_days}</div>
                  </button>
                ))}
              </div>

              <input type="date" value={form.date}
                onChange={e => setForm({ ...form, date: e.target.value })}
                min={new Date().toISOString().split("T")[0]}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />

              <input placeholder="Reason for visit" value={form.reason}
                onChange={e => setForm({ ...form, reason: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />

              <button onClick={fetchSlots}
                disabled={!form.doctor_id || !form.date || !form.patient_name || !form.patient_phone || loading}
                className="w-full bg-blue-600 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors">
                {loading ? "🔄 Checking availability..." : "Check Available Slots →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Slot selection */}
        {step === "slots" && (
          <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-3">
            <div className="flex items-center gap-2">
              <button onClick={() => setStep("doctors")} className="text-gray-500 hover:text-gray-700">←</button>
              <h2 className="font-semibold text-gray-800">Available Slots — {form.date}</h2>
            </div>
            {slots.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-4">No slots available for this date.</p>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                {slots.map(slot => (
                  <button key={slot} onClick={() => { setForm({ ...form, time_slot: slot }); setStep("confirm"); }}
                    className="border border-gray-200 rounded-xl py-2 text-sm hover:border-blue-400 hover:bg-blue-50 transition-all">
                    {slot}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Confirmation */}
        {step === "confirm" && (
          <div className="bg-white rounded-2xl p-4 border border-gray-200 space-y-4">
            <div className="flex items-center gap-2">
              <button onClick={() => setStep("slots")} className="text-gray-500 hover:text-gray-700">←</button>
              <h2 className="font-semibold text-gray-800">Confirm Appointment</h2>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Patient</span><span className="font-medium">{form.patient_name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Doctor</span><span className="font-medium">{form.doctor_name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Date</span><span className="font-medium">{form.date}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Time</span><span className="font-medium">{form.time_slot}</span></div>
              {form.reason && <div className="flex justify-between"><span className="text-gray-500">Reason</span><span className="font-medium">{form.reason}</span></div>}
            </div>
            <button onClick={bookAppointment} disabled={loading}
              className="w-full bg-green-600 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-green-700 disabled:opacity-40 transition-colors">
              {loading ? "📝 Booking..." : "✅ Confirm Booking"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}