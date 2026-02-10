import React, { useState, useEffect } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Loader2 } from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_API_URL;
const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#6366F1", "#8B5CF6"];

export default function DiagnosisDistribution() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDistribution = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/doctor/diagnosis-distribution`);
        if (res.ok) {
          const dist = await res.json();
          setData(dist);
        }
      } catch (err) {
        console.error("Failed to fetch distribution:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDistribution();
  }, []);

  if (loading) {
    return (
      <div className="bg-white shadow rounded-xl p-6 w-full flex justify-center items-center h-72">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Check if we have any data
  const hasData = data.some(d => d.value > 0);

  return (
    <div className="bg-white shadow rounded-xl p-6 w-full">
      <h2 className="text-lg font-bold text-gray-700 mb-4">Diagnosis Distribution</h2>
      <div className="h-72">
        {!hasData ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            No diagnosis data yet. Submit patient cases to see distribution.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}