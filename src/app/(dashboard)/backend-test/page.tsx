
"use client";

import { useState } from "react";
import { useApiClient } from "@/lib/api-client";

export default function BackendTestPage() {
  const api = useApiClient();

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [success, setSuccess] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    setResult("");
    setSuccess(false);

    try {
      const data = await api<unknown>("/api/v1/users/me");

      setResult(JSON.stringify(data, null, 2));
      setSuccess(true);
    } catch (error) {
      setResult(
        error instanceof Error ? error.message : "Unknown error"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-2xl space-y-5 p-8">
      <h1 className="text-2xl font-bold">
        Ashu Backend Connection Test
      </h1>

      <p>
        Test your existing Clerk login against the FastAPI backend.
      </p>

      <button
        onClick={testConnection}
        disabled={loading}
        className="rounded-lg bg-blue-600 px-5 py-3 text-white disabled:opacity-50"
      >
        {loading ? "Testing..." : "Test Backend Connection"}
      </button>

      {result && (
        <div className="rounded-lg border p-4">
          <h2 className="mb-3 font-semibold">
            {success ? "Connection Successful" : "Connection Error"}
          </h2>
          <pre className="overflow-auto whitespace-pre-wrap text-sm">
            {result}
          </pre>
        </div>
      )}
    </main>
  );
}
