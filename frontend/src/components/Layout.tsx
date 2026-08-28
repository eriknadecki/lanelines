import { useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { getBalance } from "../api/client";
import { useLiveChannels } from "../api/ws";
import { useAuth } from "../auth/AuthContext";
import { SearchBox } from "./SearchBox";
import { TopLoadingBar } from "./TopLoadingBar";
import type { BalanceOut } from "../api/types";

function Logo() {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="var(--accent)" />
      <path
        d="M4 11 C 8 8, 12 14, 16 11 C 20 8, 24 14, 28 11"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M4 16 C 8 13, 12 19, 16 16 C 20 13, 24 19, 28 16"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M4 21 C 8 18, 12 24, 16 21 C 20 18, 24 24, 28 21"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return "nav-link" + (isActive ? " active" : "");
}

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
      <TopLoadingBar />
      <header className="topbar">
        <Link to="/markets" className="brand">
          <Logo />
        </Link>
        <nav>
          <NavLink to="/markets" className={navLinkClassName}>
            Markets
          </NavLink>
          <NavLink to="/meets" className={navLinkClassName}>
            Meets
          </NavLink>
          {user && (
            <NavLink to="/portfolio" className={navLinkClassName}>
              Portfolio
            </NavLink>
          )}
          {user?.role === "admin" && (
            <NavLink to="/admin" className={navLinkClassName}>
              Admin
            </NavLink>
          )}
          <SearchBox />
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
