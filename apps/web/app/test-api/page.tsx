"use client";

import { useEffect, useState } from "react";
import { getUsers } from "@/lib/api/users";
import type { User } from "@/types/api";

export default function TestApiPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchUsers() {
      try {
        setLoading(true);
        setError(null);

        const data = await getUsers();

        setUsers(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to connect to the API",
        );
      } finally {
        setLoading(false);
      }
    }

    fetchUsers();
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "40px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1>JobForge API Test</h1>

      {loading && <p>Connecting to API...</p>}

      {error && (
        <div>
          <p style={{ color: "red" }}>
            API Error: {error}
          </p>

          <p>
            Make sure the FastAPI backend is running on
            http://localhost:8000
          </p>
        </div>
      )}

      {!loading && !error && (
        <div>
          <p>API connection successful.</p>

          <p>Users found: {users.length}</p>

          {users.length > 0 && (
            <ul>
              {users.map((user) => (
                <li key={user.id}>
                  {user.full_name || "Unnamed user"} — {user.email}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </main>
  );
}