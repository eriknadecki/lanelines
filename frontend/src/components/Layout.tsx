import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { SearchBox } from "./SearchBox";
import { TopLoadingBar } from "./TopLoadingBar";

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

function SettingsIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
      <path
        d="M19.4 13a7.97 7.97 0 0 0 0-2l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.99 7.99 0 0 0-1.73-1l-.36-2.54a.5.5 0 0 0-.5-.43h-3.84a.5.5 0 0 0-.5.43l-.36 2.54c-.63.26-1.22.6-1.73 1l-2.39-.96a.5.5 0 0 0-.6.22L2.7 8.78a.5.5 0 0 0 .12.64L4.85 11a7.97 7.97 0 0 0 0 2l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.14.24.42.32.6.22l2.39-.96c.51.4 1.1.74 1.73 1l.36 2.54c.05.25.26.43.5.43h3.84c.24 0 .45-.18.5-.43l.36-2.54c.63-.26 1.22-.6 1.73-1l2.39.96c.24.1.46 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64L19.4 13Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return "nav-link" + (isActive ? " active" : "");
}

export function Layout() {
  const { user, logout } = useAuth();

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
              <Link to="/portfolio" className="username">
                {user.username}
              </Link>
              <Link to="/settings" className="settings-link" aria-label="Settings">
                <SettingsIcon />
              </Link>
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
