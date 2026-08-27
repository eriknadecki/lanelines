import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, checkInvite, signup } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function SignupPage() {
  const { applyTokens } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [inviteCode, setInviteCode] = useState(searchParams.get("code") ?? "");
  const [inviteStatus, setInviteStatus] = useState<"checking" | "valid" | "invalid" | "idle">("idle");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!inviteCode) {
      setInviteStatus("idle");
      return;
    }
    setInviteStatus("checking");
    checkInvite(inviteCode)
      .then((result) => setInviteStatus(result.valid ? "valid" : "invalid"))
      .catch(() => setInviteStatus("invalid"));
  }, [inviteCode]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const tokens = await signup(inviteCode, email, username, password);
      await applyTokens(tokens);
      navigate("/markets");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Signup failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>Join Lanelines</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Invite code
          <input value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} required />
        </label>
        {inviteStatus === "invalid" && <p className="error">That invite code isn't valid.</p>}
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting || inviteStatus === "invalid"}>
          {submitting ? "Creating account..." : "Sign up"}
        </button>
      </form>
    </div>
  );
}
