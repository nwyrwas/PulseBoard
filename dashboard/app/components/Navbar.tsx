"use client";

import { useState, useEffect } from "react";

export default function Navbar() {
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    setLastUpdated(new Date().toLocaleTimeString());
    const interval = setInterval(() => {
      setLastUpdated(new Date().toLocaleTimeString());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="bg-gray-900 border-b border-gray-700 px-6 py-4 flex justify-between items-center">
      <h1 className="text-2xl font-bold text-white">PulseBoard</h1>
      <span className="text-sm text-gray-400">
        Last updated: {lastUpdated || "Loading..."}
      </span>
    </nav>
  );
}
