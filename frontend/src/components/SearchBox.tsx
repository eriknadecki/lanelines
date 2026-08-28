import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { search } from "../api/client";
import type { SearchResultsOut } from "../api/types";

export function SearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultsOut | null>(null);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults(null);
      return;
    }
    const timer = window.setTimeout(() => {
      search(trimmed)
        .then((r) => {
          setResults(r);
          setOpen(true);
        })
        .catch(() => setResults(null));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function go(path: string) {
    navigate(path);
    setOpen(false);
    setQuery("");
    setResults(null);
  }

  const hasResults =
    !!results &&
    (results.markets.length > 0 ||
      results.meets.length > 0 ||
      results.teams.length > 0 ||
      results.swimmers.length > 0);

  return (
    <div className="search-box" ref={containerRef}>
      <input
        type="search"
        placeholder="Search meets, markets, swimmers..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results && setOpen(true)}
      />
      {open && results && (
        <div className="search-dropdown">
          {!hasResults && <p className="muted search-empty">No results</p>}
          {results.markets.length > 0 && (
            <div className="search-group">
              <h4>Markets</h4>
              {results.markets.map((m) => (
                <button key={m.id} type="button" onClick={() => go(`/markets/${m.id}`)}>
                  {m.label} <span className="muted">— {m.group_title}</span>
                </button>
              ))}
            </div>
          )}
          {results.meets.length > 0 && (
            <div className="search-group">
              <h4>Meets</h4>
              {results.meets.map((m) => (
                <button key={m.id} type="button" onClick={() => go(`/meets/${m.id}`)}>
                  {m.name}
                </button>
              ))}
            </div>
          )}
          {results.teams.length > 0 && (
            <div className="search-group">
              <h4>Teams</h4>
              {results.teams.map((t) => (
                <div key={t.id} className="search-static">
                  {t.name}
                </div>
              ))}
            </div>
          )}
          {results.swimmers.length > 0 && (
            <div className="search-group">
              <h4>Swimmers</h4>
              {results.swimmers.map((s) => (
                <div key={s.id} className="search-static">
                  {s.name} <span className="muted">— {s.team_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
