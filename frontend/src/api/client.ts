import { beginRequest, endRequest } from "./loadingIndicator";
import type {
  BalanceOut,
  BookSnapshotOut,
  InviteCheckOut,
  InviteOut,
  MarketGroupOut,
  MarketOut,
  MeetEventOut,
  MeetOut,
  OrderOut,
  PositionOut,
  SearchResultsOut,
  SwimmerOut,
  TeamOut,
  TickerUpdateOut,
  TokenResponse,
  UserOut,
  VenueOut,
} from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

const ACCESS_TOKEN_KEY = "lanelines.access_token";
const REFRESH_TOKEN_KEY = "lanelines.refresh_token";

// "Remember me" decides which storage tokens live in: localStorage survives
// closing the browser (up to the refresh token's lifetime), sessionStorage
// is cleared when the tab/browser closes. Only one of the two ever holds a
// live pair at a time, so reads just check both.
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY) ?? sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: TokenResponse, remember: boolean = true): void {
  const store = remember ? localStorage : sessionStorage;
  const other = remember ? sessionStorage : localStorage;
  store.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  store.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  other.removeItem(ACCESS_TOKEN_KEY);
  other.removeItem(REFRESH_TOKEN_KEY);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// De-duped so several requests failing at once (e.g. a REST call and a
// WebSocket reconnect right as the access token expires) trigger one
// refresh, not a stampede of them.
let pendingRefresh: Promise<boolean> | null = null;

function refreshAccessTokenOnce(): Promise<boolean> {
  if (!pendingRefresh) {
    pendingRefresh = refreshAccessToken().finally(() => {
      pendingRefresh = null;
    });
  }
  return pendingRefresh;
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) return false;
    const tokens = (await response.json()) as TokenResponse;
    const remember = localStorage.getItem(REFRESH_TOKEN_KEY) !== null;
    setTokens(tokens, remember);
    return true;
  } catch {
    return false;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}, isRetry = false): Promise<T> {
  beginRequest();
  try {
    return await apiFetchInner<T>(path, options, isRetry);
  } finally {
    endRequest();
  }
}

async function apiFetchInner<T>(path: string, options: RequestInit, isRetry: boolean): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401 && token && !isRetry && path !== "/api/v1/auth/refresh") {
    if (await refreshAccessTokenOnce()) {
      return apiFetchInner<T>(path, options, true);
    }
    clearTokens();
  }

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

// --- venues / teams / swimmers / meets (public reads) ---
export const listVenues = () => apiFetch<VenueOut[]>("/api/v1/venues");
export const listTeams = () => apiFetch<TeamOut[]>("/api/v1/teams");
export const listSwimmers = (teamId: string) => apiFetch<SwimmerOut[]>(`/api/v1/teams/${teamId}/swimmers`);
export const listMeets = () => apiFetch<MeetOut[]>("/api/v1/meets");
export const getMeet = (meetId: string) => apiFetch<MeetOut>(`/api/v1/meets/${meetId}`);
export const listMeetEvents = (meetId: string) => apiFetch<MeetEventOut[]>(`/api/v1/meets/${meetId}/events`);
export const getMeetTicker = (meetId: string) => apiFetch<TickerUpdateOut[]>(`/api/v1/meets/${meetId}/ticker`);
export const search = (q: string) => apiFetch<SearchResultsOut>(`/api/v1/search?q=${encodeURIComponent(q)}`);

// --- admin ---
export const createInvite = (max_uses: number, expires_in_days: number | null) =>
  apiFetch<InviteOut>("/api/v1/admin/invites", { method: "POST", body: JSON.stringify({ max_uses, expires_in_days }) });

export interface CreateVenueRequest {
  name: string;
  address?: string | null;
}

export const createVenue = (payload: CreateVenueRequest) =>
  apiFetch<VenueOut>("/api/v1/admin/venues", { method: "POST", body: JSON.stringify(payload) });

export interface CreateTeamRequest {
  name: string;
  short_name: string;
  location?: string | null;
  home_venue_id?: string | null;
}

export const createTeam = (payload: CreateTeamRequest) =>
  apiFetch<TeamOut>("/api/v1/admin/teams", { method: "POST", body: JSON.stringify(payload) });

export const createSwimmer = (teamId: string, name: string, class_standing: string | null) =>
  apiFetch<SwimmerOut>(`/api/v1/admin/teams/${teamId}/swimmers`, {
    method: "POST",
    body: JSON.stringify({ name, class_standing }),
  });

export const deleteSwimmer = (teamId: string, swimmerId: string) =>
  apiFetch<void>(`/api/v1/admin/teams/${teamId}/swimmers/${swimmerId}`, { method: "DELETE" });

export async function uploadRosterCsv(teamId: string, file: File): Promise<SwimmerOut[]> {
  beginRequest();
  try {
    const token = getAccessToken();
    const headers = new Headers();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/v1/admin/teams/${teamId}/swimmers/upload-csv`, {
      method: "POST",
      headers,
      body: formData,
    });
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
    return (await response.json()) as SwimmerOut[];
  } finally {
    endRequest();
  }
}

export const deleteVenue = (venueId: string) => apiFetch<void>(`/api/v1/admin/venues/${venueId}`, { method: "DELETE" });

export const deleteTeam = (teamId: string) => apiFetch<void>(`/api/v1/admin/teams/${teamId}`, { method: "DELETE" });

export interface CreateMeetRequest {
  name: string;
  meet_type: "dual" | "tri" | "championship";
  home_team_id?: string | null;
  away_team_id?: string | null;
  scheduled_at?: string | null;
  venue_id?: string | null;
}

export const createMeet = (payload: CreateMeetRequest) =>
  apiFetch<MeetOut>("/api/v1/admin/meets", { method: "POST", body: JSON.stringify(payload) });

export const deleteMeet = (meetId: string) => apiFetch<void>(`/api/v1/admin/meets/${meetId}`, { method: "DELETE" });

export const createMeetEvent = (meetId: string, name: string, event_order: number) =>
  apiFetch<MeetEventOut>(`/api/v1/admin/meets/${meetId}/events`, {
    method: "POST",
    body: JSON.stringify({ name, event_order }),
  });

export const deleteMeetEvent = (meetId: string, eventId: string) =>
  apiFetch<void>(`/api/v1/admin/meets/${meetId}/events/${eventId}`, { method: "DELETE" });

export const postTickerUpdate = (meetId: string, body: string, meet_event_id?: string | null) =>
  apiFetch<TickerUpdateOut>(`/api/v1/admin/meets/${meetId}/ticker`, {
    method: "POST",
    body: JSON.stringify({ body, meet_event_id }),
  });

export interface CreateMarketGroupRequest {
  title: string;
  description?: string | null;
  team_ids: string[];
  close_at?: string | null;
  meet_id?: string | null;
  meet_event_id?: string | null;
}

export const createMarketGroup = (payload: CreateMarketGroupRequest) =>
  apiFetch<MarketGroupOut>("/api/v1/admin/market-groups", { method: "POST", body: JSON.stringify(payload) });

export const deleteMarketGroup = (groupId: string) =>
  apiFetch<void>(`/api/v1/admin/market-groups/${groupId}`, { method: "DELETE" });

export const closeMarket = (marketId: string) =>
  apiFetch<MarketOut>(`/api/v1/admin/markets/${marketId}/close`, { method: "POST" });

export const resolveMarketGroup = (groupId: string, winning_market_id: string) =>
  apiFetch<MarketGroupOut>(`/api/v1/admin/market-groups/${groupId}/resolve`, {
    method: "POST",
    body: JSON.stringify({ winning_market_id }),
  });
