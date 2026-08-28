import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBalance, getPositions } from "../api/client";
import { useLiveChannels } from "../api/ws";
import type { BalanceOut, PositionOut } from "../api/types";

export function PortfolioPage() {
  const [balance, setBalance] = useState<BalanceOut | null>(null);
  const [positions, setPositions] = useState<PositionOut[] | null>(null);

  useEffect(() => {
    getBalance().then(setBalance).catch(() => {});
    getPositions().then(setPositions).catch(() => {});
  }, []);

  useLiveChannels([], (event) => {
    if (event.type === "balance_update") {
      setBalance((prev) => ({
        cash_balance_cents: event.cash_balance_cents,
        available_cents: event.available_cents,
        held_collateral_cents: prev ? prev.cash_balance_cents - prev.available_cents : 0,
      }));
    } else if (event.type === "order_update" || event.type === "market_resolved") {
      getPositions().then(setPositions).catch(() => {});
    }
  });

  return (
    <div>
      {balance && (
        <div className="balance-summary">
          <div>
            <span className="muted">Cash</span>
            <strong>${(balance.cash_balance_cents / 100).toFixed(2)}</strong>
          </div>
          <div>
            <span className="muted">Held</span>
            <strong>${(balance.held_collateral_cents / 100).toFixed(2)}</strong>
          </div>
          <div>
            <span className="muted">Available</span>
            <strong>${(balance.available_cents / 100).toFixed(2)}</strong>
          </div>
        </div>
      )}

      <h2>Positions</h2>
      {!positions ? (
        <p>Loading...</p>
      ) : positions.length === 0 ? (
        <p className="muted">No open positions.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Market</th>
              <th>Net YES qty</th>
              <th>Avg cost</th>
              <th>Realized P&amp;L</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.market_id}>
                <td>
                  <Link to={`/markets/${p.market_id}`}>{p.market_id.slice(0, 8)}...</Link>
                </td>
                <td>{p.net_yes_quantity}</td>
                <td>{p.avg_cost_cents}c</td>
                <td>${(p.realized_pnl_cents / 100).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
