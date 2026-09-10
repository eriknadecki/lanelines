import { useState, type FormEvent } from "react";
import { ApiError, changePassword } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type SubmitStatus = "idle" | "pending" | "success" | "error";

// Same button-as-status-indicator pattern as AdminPage: click → pending
// label → button itself turns green/red with the result, then reverts.
function useSubmitStatus(revertMs = 2200) {
  const [status, setStatus] = useState<SubmitStatus>("idle");
  const [message, setMessage] = useState<string | null>(null);

  function start() {
    setStatus("pending");
    setMessage(null);
  }
  function succeed(msg: string) {
    setStatus("success");
    setMessage(msg);
    window.setTimeout(() => setStatus("idle"), revertMs);
  }
  function fail(msg: string) {
    setStatus("error");
    setMessage(msg);
    window.setTimeout(() => setStatus("idle"), revertMs + 1200);
  }

  return { status, message, start, succeed, fail };
}

function SubmitButton({ status, message, idleLabel }: { status: SubmitStatus; message: string | null; idleLabel: string }) {
  const label =
    status === "pending" ? "Working..." : status === "success" || status === "error" ? (message ?? idleLabel) : idleLabel;
  const className = "submit-button" + (status === "success" ? " success" : status === "error" ? " error" : "");
  return (
    <button type="submit" className={className} disabled={status === "pending"}>
      {label}
    </button>
  );
}

function ChangePasswordForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { status, message, start, succeed, fail } = useSubmitStatus();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      fail("Passwords don't match");
      return;
    }
    start();
    try {
      await changePassword(currentPassword, newPassword);
      succeed("Password updated");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      fail(err instanceof ApiError ? err.message : "Failed to update password");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Current password
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
      </label>
      <label>
        New password
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          minLength={8}
          required
        />
      </label>
      <label>
        Confirm new password
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          minLength={8}
          required
        />
      </label>
      <SubmitButton status={status} message={message} idleLabel="Change password" />
    </form>
  );
}

export function SettingsPage() {
  const { user } = useAuth();

  return (
    <div>
      <h1>Settings</h1>
      <section className="admin-section">
        <h2>Account</h2>
        <p className="muted">
          {user?.username} — {user?.email}
        </p>
      </section>
      <section className="admin-section">
        <h2>Change password</h2>
        <ChangePasswordForm />
      </section>
    </div>
  );
}
