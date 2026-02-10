import React from "react";
import { User } from "lucide-react";

export default function PatientProfile() {
  return (
    <div className="max-w-5xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold !text-gray-900">My Profile</h1>
        <p className="!text-gray-600">
          Manage your personal information and account settings.
        </p>
      </div>

      {/* Profile Card */}
      <div className="bg-white rounded-2xl shadow-md p-6 space-y-6">
        {/* Top section with avatar */}
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 flex items-center justify-center rounded-full !bg-blue-100">
            <User className="w-8 h-8 !text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold !text-gray-900">John Doe</h2>
            <p className="!text-gray-600">Patient • New Delhi, India</p>
            <p className="text-sm !text-gray-500">Joined: Jan 2025</p>
          </div>
        </div>

        {/* Personal Information */}
        <div className="border-t pt-4">
          <h3 className="text-lg font-semibold !text-gray-800 mb-3">
            Personal Information
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-2 gap-x-6 !text-gray-700">
            <p>
              <span className="font-medium">Full Name:</span> John Doe
            </p>
            <p>
              <span className="font-medium">Email:</span> john.doe@example.com
            </p>
            <p>
              <span className="font-medium">Phone:</span> +91 98765 43210
            </p>
            <p>
              <span className="font-medium">Age:</span> 30 years
            </p>
            <p>
              <span className="font-medium">Blood Group:</span> B+
            </p>
            <p>
              <span className="font-medium">Allergies:</span> None
            </p>
            <p>
              <span className="font-medium">Chronic Conditions:</span>
              Hypertension, Diabetes
            </p>
          </div>
        </div>

        {/* Account Settings */}
        <div className="border-t pt-4 mt-6">
          <h3 className="text-lg font-semibold !text-gray-800 mb-3">
            Account Settings
          </h3>
          <div className="flex flex-wrap gap-4">
            <button className="px-5 py-2 !bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              Edit Profile
            </button>
            <button className="px-5 py-2 bg-gray-200 !text-gray-700 rounded-lg hover:bg-gray-300 transition">
              Change Password
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
