import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMarketGroups } from "../api/client";
import type { MarketCategory, MarketGroupOut, TeamConference, TeamDivision } from "../api/types";
import { TEAM_CONFERENCES, TEAM_DIVISIONS } from "../constants";

const CATEGORY_TABS: { label: string; value: MarketCategory | null }[] = [
  { label: "All", value: null },
  { label: "Trending", value: "trending" },
  { label: "Live", value: "live" },
  { label: "Dual/Tri", value: "dual_tri" },
  { label: "Invite", value: "invite" },
  { label: "Championship", value: "championship" },
  { label: "Event Result", value: "event_result" },
];

export function MarketsListPage() {
  const [category, setCategory] = useState<MarketCategory | null>(null);
  const [division, setDivision] = useState<TeamDivision | "">("");
  const [conference, setConference] = useState<TeamConference | "">("");
  const [groups, setGroups] = useState<MarketGroupOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setGroups(null);
    listMarketGroups({
      category: category ?? undefined,
      division: division || undefined,
      conference: conference || undefined,
    })
      .then(setGroups)
      .catch(() => setError("Failed to load markets"));
  }, [category, division, conference]);

  return (
    <div>
      <h1>Markets</h1>
      <div className="category-bar">
        {CATEGORY_TABS.map((tab) => (
          <button
            key={tab.label}
            type="button"
            className={"category-tab" + (category === tab.value ? " active" : "")}
            onClick={() => setCategory(tab.value)}
          >
            {tab.label}
          </button>
        ))}
        <div className="category-filters">
          <select value={division} onChange={(e) => setDivision(e.target.value as TeamDivision | "")}>
            <option value="">All divisions</option>
            {TEAM_DIVISIONS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <select value={conference} onChange={(e) => setConference(e.target.value as TeamConference | "")}>
            <option value="">All conferences</option>
            {TEAM_CONFERENCES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {!error && !groups && <p>Loading markets...</p>}
      {!error && groups && groups.length === 0 && <p>No markets yet.</p>}
      {groups &&
        groups.map((group) => (
          <div key={group.id} className="market-group-card">
            <h2>{group.title}</h2>
            {group.description && <p className="muted">{group.description}</p>}
            <ul className="market-list">
              {group.markets.map((market) => (
                <li key={market.id}>
                  <Link to={`/markets/${market.id}`}>{market.label}</Link>
                  <span className={`status-badge status-${market.status}`}>{market.status}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
    </div>
  );
}
