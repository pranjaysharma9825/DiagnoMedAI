import React, { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_API_URL;

export default function RecentPatients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecent = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/doctor/cases`);
        if (res.ok) {
          const data = await res.json();
          // Get last 3 cases
          const recent = data.slice(0, 3).map((c) => {
            // Determine status based on analysis
            let status = "Pending";
            let statusColor = "text-yellow-600";

            if (c.analysis_output && c.analysis_output.length > 0) {
              status = "Diagnosed";
              statusColor = "text-green-600";
            } else if (c.cnn_output) {
              status = "In Progress";
              statusColor = "text-blue-600";
            }

            return {
              name: c.patient_name || "Anonymous",
              age: c.age ? `${c.age}y` : "N/A",
              conditions: c.cnn_output || "Awaiting Analysis",
              status,
              statusColor
            };
          });
          setPatients(recent);
        }
      } catch (err) {
        console.error("Failed to fetch recent patients:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRecent();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (patients.length === 0) {
    return (
      <section className="mt-8">
        <p className="text-center text-gray-500">No recent patients.</p>
      </section>
    );
  }

  return (
    <section className="mt-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {patients.map((p, idx) => (
          <div key={idx} className="bg-white shadow rounded-xl p-6">
            <p className="font-medium text-gray-900">{p.name}</p>
            <p className="text-sm text-gray-500">{p.age} · {p.conditions}</p>
            <span className={`${p.statusColor} text-sm font-semibold`}>{p.status}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
