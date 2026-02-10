import React, { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_API_URL;

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/doctor/cases`);
        if (res.ok) {
          const data = await res.json();
          // Transform case data to patient format
          const patientList = data.map((c, i) => ({
            id: c.id || i,
            name: c.patient_name || "Anonymous",
            age: c.age || "N/A",
            condition: c.cnn_output || c.analysis_output?.split(",")[0] || "Pending",
            lastVisit: c.created_at ? new Date(c.created_at).toLocaleDateString() : "N/A"
          }));
          setPatients(patientList);
        }
      } catch (err) {
        console.error("Failed to fetch patients:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPatients();
  }, []);

  const filtered = patients.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 min-w-screen bg-gray-50">
      <h2 className="text-2xl font-bold text-gray-800">Patients</h2>

      <input
        type="text"
        placeholder="Search patients..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mt-4 mb-6 border px-3 py-2 rounded-lg w-1/3 bg-white text-gray-900 border-gray-300"
      />

      {filtered.length === 0 ? (
        <p className="text-center text-gray-500 py-10">No patients found.</p>
      ) : (
        <table className="w-full bg-white shadow rounded-lg overflow-hidden">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3 text-gray-700">Name</th>
              <th className="p-3 text-gray-700">Age</th>
              <th className="p-3 text-gray-700">Condition</th>
              <th className="p-3 text-gray-700">Last Visit</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr
                key={p.id}
                className="border-t hover:bg-gray-50"
              >
                <td className="p-3 text-gray-900">{p.name}</td>
                <td className="p-3 text-gray-900">{p.age}</td>
                <td className="p-3 text-gray-900">{p.condition}</td>
                <td className="p-3 text-gray-900">{p.lastVisit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}