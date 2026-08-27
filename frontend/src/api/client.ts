import type {
  BalanceOut,
  BookSnapshotOut,
  InviteCheckOut,
  InviteOut,
  MarketGroupOut,
  MarketOut,
  MeetOut,
  OrderOut,
  PositionOut,
  TeamOut,
  TickerUpdateOut,
  TokenResponse,
  UserOut,
} from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

const ACCESS_TOKEN_KEY = "lanelines.access_token";
const REFRESH_TOKEN_KEY = "lanelines.refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// --- auth ---
export const checkInvite = (code: string) => apiFetch<InviteCheckOut>(`/api/v1/invites/${code}`);

export const signup = (invite_code: string, email: string, username: string, password: string) =>
  apiFetch<TokenResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify({ invite_code, email, username, password }),
  });

export const login = (email: string, password: string) =>
  apiFetch<TokenResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });

export const getMe = () => apiFetch<UserOut>("/api/v1/me");
export const getBalance = () => apiFetch<BalanceOut>("/api/v1/me/balance");
export const getPositions = () => apiFetch<PositionOut[]>("/api/v1/me/positions");

// --- markets ---
export const listMarketGroups = () => apiFetch<MarketGroupOut[]>("/api/v1/markets");
export const getMarket = (marketId: string) => apiFetch<MarketOut>(`/api/v1/markets/${marketId}`);
export const getMarketBook = (marketId: string, depth = 10) =>
  apiFetch<BookSnapshotOut>(`/api/v1/markets/${marketId}/book?depth=${depth}`);

// --- orders ---
export interface SubmitOrderRequest {
  market_id: string;
  side: "yes" | "no";
  action: "buy" | "sell";
  order_type?: "limit" | "market";
  quantity: number;
  price_cents?: number;
  time_in_force?: "gtc" | "ioc" | "fok";
}

export const submitOrder = (payload: SubmitOrderRequest) =>
  apiFetch<OrderOut>("/api/v1/orders", { method: "POST", body: JSON.stringify(payload) });

export const cancelOrder = (orderId: string) => apiFetch<OrderOut>(`/api/v1/orders/${orderId}`, { method: "DELETE" });

export const listMyOrders = (marketId?: string) =>
  apiFetch<OrderOut[]>(`/api/v1/orders${marketId ? `?market_id=${marketId}` : ""}`);

// --- meets ---
export const listTeams = () => apiFetch<TeamOut[]>("/api/v1/teams");
export const listMeets = () => apiFetch<MeetOut[]>("/api/v1/meets");
export const getMeet = (meetId: string) => apiFetch<MeetOut>(`/api/v1/meets/${meetId}`);
export const getMeetTicker = (meetId: string) => apiFetch<TickerUpdateOut[]>(`/api/v1/meets/${meetId}/ticker`);

// --- admin ---
export const createInvite = (max_uses: number, expires_in_days: number | null) =>
  apiFetch<InviteOut>("/api/v1/admin/invites", { method: "POST", body: JSON.stringify({ max_uses, expires_in_days }) });

export const createTeam = (name: string, short_name: string) =>
  apiFetch<TeamOut>("/api/v1/admin/teams", { method: "POST", body: JSON.stringify({ name, short_name }) });

export interface CreateMeetRequest {
  name: string;
  meet_type: "dual" | "championship";
  home_team_id?: string | null;
  away_team_id?: string | null;
  scheduled_at?: string | null;
  venue?: string | null;
}

export const createMeet = (payload: CreateMeetRequest) =>
  apiFetch<MeetOut>("/api/v1/admin/meets", { method: "POST", body: JSON.stringify(payload) });

export const postTickerUpdate = (meetId: string, body: string, meet_event_id?: string | null) =>
  apiFetch<TickerUpdateOut>(`/api/v1/admin/meets/${meetId}/ticker`, {
    method: "POST",
    body: JSON.stringify({ body, meet_event_id }),
  });

export interface CreateMarketGroupRequest {
  title: string;
  description?: string | null;
  outcomes: string[];
  close_at?: string | null;
  meet_id?: string | null;
  meet_event_id?: string | null;
}

export const createMarketGroup = (payload: CreateMarketGroupRequest) =>
  apiFetch<MarketGroupOut>("/api/v1/admin/market-groups", { method: "POST", body: JSON.stringify(payload) });

export const closeMarket = (marketId: string) =>
  apiFetch<MarketOut>(`/api/v1/admin/markets/${marketId}/close`, { method: "POST" });

export const resolveMarketGroup = (groupId: string, winning_market_id: string) =>
  apiFetch<MarketGroupOut>(`/api/v1/admin/market-groups/${groupId}/resolve`, {
    method: "POST",
    body: JSON.stringify({ winning_market_id }),
  });
