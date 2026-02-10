import React from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";

const data = [
  { month: "Jan", patients: 120 },
  { month: "Feb", patients: 200 },
  { month: "Mar", patients: 150 },
  { month: "Apr", patients: 250 },
  { month: "May", patients: 180 },
  { month: "Jun", patients: 300 },
];

export default function PatientChart() {
  return (
    <section className=" bg-white dark:bg-panel-dark shadow rounded-xl p-6 w-full">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-text-light">
        Patient Trends
      </h3>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-700" />
            <XAxis dataKey="month" stroke="#374151" className="dark:stroke-text-light dark:text-text-light" />
            <YAxis stroke="#374151" className="dark:stroke-text-light dark:text-text-light" />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(42, 37, 89, 0.9)",
                borderRadius: "0.5rem",
                border: "none",
                color: "#e0e0e0",
              }}
              itemStyle={{ color: "#e0e0e0" }}
            />
            <Line
              type="monotone"
              dataKey="patients"
              stroke="#3b82f6" // primary
              strokeWidth={3}
              dot={{ stroke: "#90cdf4", strokeWidth: 2, fill: "#3b82f6" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
