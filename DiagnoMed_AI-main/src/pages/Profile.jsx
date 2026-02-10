import React from "react";
import { User } from "lucide-react"; // ✅ Import user icon

export default function Profile() {
  return (
    <main className="p-6 w-full space-y-6">
      {/* Header */}
      <header className="bg-white p-6 rounded-2xl shadow border border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="text-gray-600 mt-1">
          Manage your Personal Information and Account Settings.
        </p>
      </header>

      {/* Combined Profile Card */}
      <section className="bg-white p-6 rounded-2xl shadow border border-gray-200 space-y-6">
        {/* Doctor Overview */}
        <div className="flex items-center gap-6">
          {/* Profile Icon */}
          <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center shadow">
            <User className="w-10 h-10 text-white" /> {/* ✅ Vector instead of MD */}
          </div>

          <div>
            <h2 className="text-xl font-semibold text-gray-900">Dr. Yash</h2>
            <p className="text-gray-600">Cardiologist • New Delhi, India</p>
            <p className="text-gray-500 text-sm">Joined: Jan 2025</p>
          </div>
        </div>

        <hr className="border-gray-200" />

        {/* Personal Info */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Personal Information
          </h3>
          <ul className="space-y-3 text-gray-700">
            <li>
              <span className="font-medium">Full Name:</span> Dr. XYZ
            </li>
            <li>
              <span className="font-medium">Email:</span> dr.xyz@example.com
            </li>
            <li>
              <span className="font-medium">Phone:</span> +91 98765 43210
            </li>
            <li>
              <span className="font-medium">Date of Birth:</span> 12 March 1980
            </li>
            <li>
              <span className="font-medium">Specialization:</span> Cardiology
            </li>
            <li>
              <span className="font-medium">Experience:</span> 15+ years
            </li>
            <li>
              <span className="font-medium">Hospital:</span> AIIMS Delhi
            </li>
            <li>
              <span className="font-medium">License No.:</span> MED123456
            </li>
          </ul>
        </div>

        <hr className="border-gray-200" />

        {/* Account Settings */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Account Settings
          </h3>
          <div className="space-x-4">
            <button className="px-5 py-2 rounded-lg !bg-blue-600 hover:bg-blue-700 text-white font-medium transition">
              Edit Profile
            </button>
            <button className="px-5 py-2 rounded-lg !bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium transition">
              Change Password
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
