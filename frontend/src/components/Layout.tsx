import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { getBalance } from "../api/client";
import { useLiveChannels } from "../api/ws";
import { useAuth } from "../auth/AuthContext";
import type { BalanceOut } from "../api/types";

export function Layout() {
  const { user, logout } = useAuth();
  const [balance, setBalance] = useState<BalanceOut | null>(null);

  useEffect(() => {
    if (!user) return;
    getBalance().then(setBalance).catch(() => {});
  }, [user]);

  useLiveChannels([], (event) => {
    if (event.type === "balance_update") {
      setBalance((prev) => ({
        cash_balance_cents: event.cash_balance_cents,
        available_cents: event.available_cents,
        held_collateral_cents: prev ? prev.cash_balance_cents - prev.available_cents : 0,
      }));
    }
  });

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/markets" className="brand">
          Lanelines
        </Link>
        <nav>
          <Link to="/markets">Markets</Link>
          <Link to="/meets">Meets</Link>
          {user && <Link to="/portfolio">Portfolio</Link>}
          {user?.role === "admin" && <Link to="/admin">Admin</Link>}
        </nav>
        <div className="topbar-right">
          {user ? (
            <>
              {balance && <span className="balance-pill">${(balance.available_cents / 100).toFixed(2)}</span>}
              <span className="username">{user.username}</span>
              <button onClick={logout}>Log out</button>
            </>
          ) : (
            <Link to="/login">Log in</Link>
          )}
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
