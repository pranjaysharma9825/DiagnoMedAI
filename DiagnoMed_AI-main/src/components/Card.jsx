import React from "react";

export default function Card({ title, value, color }) {
  return (
    <div className="bg-white shadow rounded-xl p-6 hover:shadow-md transition">
      <h2 className="text-sm text-gray-500">{title}</h2>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}