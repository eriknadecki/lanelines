export type Side = "yes" | "no";
export type Action = "buy" | "sell";
export type OrderType = "limit" | "market";
export type TimeInForce = "gtc" | "ioc" | "fok";
export type OrderStatus = "open" | "partially_filled" | "filled" | "cancelled" | "not_found";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type UserRole = "user" | "admin";

export interface UserOut {
  id: string;
  email: string;
  username: string;
  role: UserRole;
}

export interface BalanceOut {
  cash_balance_cents: number;
  held_collateral_cents: number;
  available_cents: number;
}

export interface PositionOut {
  market_id: string;
  net_yes_quantity: number;
  avg_cost_cents: number;
  realized_pnl_cents: number;
}

export type MarketStatus = "open" | "paused" | "closed" | "resolved";
export type MarketGroupStatus = "open" | "closed" | "resolved";
export type MarketOutcome = "yes" | "no";

export interface MarketOut {
  id: string;
  label: string;
  team_id: string | null;
  status: MarketStatus;
  resolved_outcome: MarketOutcome | null;
}

export interface MarketGroupOut {
  id: string;
  title: string;
  description: string | null;
  status: MarketGroupStatus;
  close_at: string | null;
  meet_id: string | null;
  meet_event_id: string | null;
  markets: MarketOut[];
}

export interface PriceLevelOut {
  price_cents: number;
  total_quantity: number;
}

export interface BookSnapshotOut {
  market_id: string;
  bids: PriceLevelOut[];
  asks: PriceLevelOut[];
}

export interface OrderOut {
  id: string;
  market_id: string;
  side: Side;
  action: Action;
  order_type: OrderType;
  time_in_force: TimeInForce;
  limit_price_cents: number | null;
  quantity: number;
  filled_quantity: number;
  status: OrderStatus;
  collateral_cents: number;
  created_at: string;
}

export type MeetType = "dual" | "tri" | "championship" | "invite";

export type MarketCategory = "trending" | "live" | "dual_tri" | "invite" | "championship" | "event_result";
export type MeetStatus = "scheduled" | "live" | "completed";
export type MeetEventStatus = "scheduled" | "in_progress" | "completed";

export interface MeetOut {
  id: string;
  name: string;
  meet_type: MeetType;
  home_team_id: string | null;
  away_team_id: string | null;
  scheduled_at: string | null;
  status: MeetStatus;
  venue_id: string | null;
}

export interface MeetEventOut {
  id: string;
  meet_id: string;
  name: string;
  event_order: number;
  status: MeetEventStatus;
  scheduled_at: string | null;
}

export interface TickerUpdateOut {
  id: string;
  meet_id: string;
  meet_event_id: string | null;
  author_id: string;
  body: string;
  created_at: string;
}

export type TeamDivision = "D1" | "D2" | "D3";

export type TeamConference =
  | "America East Conference" | "American Athletic Conference" | "Atlantic 10 Conference" | "Atlantic Coast Conference" | "Atlantic Sun Conference" | "Big 12 Conference" | "Big East Conference" | "Big Ten Conference" | "Big West Conference" | "Coastal Athletic Association" | "Horizon League" | "Ivy League" | "Metro Atlantic Athletic Conference" | "Mid-American Conference" | "Missouri Valley Conference" | "Mountain West Conference" | "Northeast Conference" | "Pac-12 Conference" | "Patriot League" | "Southeastern Conference" | "Southern Conference" | "Summit League" | "Sun Belt Conference" | "West Coast Conference" | "Mountain Pacific Sports Federation" | "Metropolitan Swimming Conference"
  | "California Collegiate Athletic Association" | "Central Atlantic Collegiate Conference" | "Conference Carolinas" | "East Coast Conference" | "Great Lakes Intercollegiate Athletic Conference" | "Great Lakes Valley Conference" | "Great Midwest Athletic Conference" | "Lone Star Conference" | "Mountain East Conference" | "Northeast-10 Conference" | "Northern Sun Intercollegiate Conference" | "Peach Belt Conference" | "Pennsylvania State Athletic Conference" | "Rocky Mountain Athletic Conference" | "South Atlantic Conference" | "Sunshine State Conference" | "Appalachian Swimming Conference" | "New South Intercollegiate Swim Conference" | "Pacific Coast Swim Conference"
  | "Allegheny Mountain Collegiate Conference" | "American Rivers Conference" | "American Southwest Conference" | "Atlantic East Conference" | "Centennial Conference" | "City University of New York Athletic Conference" | "Coast to Coast Athletic Conference" | "College Conference of Illinois and Wisconsin" | "Collegiate Conference of the South" | "Conference of New England" | "Empire 8" | "Great Northeast Athletic Conference" | "Heartland Collegiate Athletic Conference" | "Landmark Conference" | "Liberty League" | "Little East Conference" | "Michigan Intercollegiate Athletic Association" | "Middle Atlantic Conferences" | "Midwest Conference" | "Minnesota Intercollegiate Athletic Conference" | "New England Collegiate Conference" | "New England Small College Athletic Conference" | "New England Women's and Men's Athletic Conference" | "New Jersey Athletic Conference" | "North Atlantic Conference" | "North Coast Athletic Conference" | "Northwest Conference" | "Ohio Athletic Conference" | "Old Dominion Athletic Conference" | "Presidents' Athletic Conference" | "Skyline Conference" | "Southern Athletic Association" | "Southern California Intercollegiate Athletic Conference" | "Southern Collegiate Athletic Conference" | "State University of New York Athletic Conference" | "United East Conference" | "University Athletic Association" | "USA South Athletic Conference" | "Wisconsin Intercollegiate Athletic Conference";

export interface TeamOut {
  id: string;
  name: string;
  short_name: string;
  location: string | null;
  home_venue_id: string | null;
  division: TeamDivision | null;
  conference: TeamConference | null;
}

export interface VenueOut {
  id: string;
  name: string;
  address: string | null;
}

export interface SwimmerOut {
  id: string;
  team_id: string;
  name: string;
  class_standing: string | null;
}

export interface MarketSearchResult {
  id: string;
  label: string;
  group_title: string;
  status: MarketStatus;
}

export interface MeetSearchResult {
  id: string;
  name: string;
  meet_type: MeetType;
}

export interface TeamSearchResult {
  id: string;
  name: string;
  short_name: string;
}

export interface SwimmerSearchResult {
  id: string;
  name: string;
  team_name: string;
}

export interface SearchResultsOut {
  markets: MarketSearchResult[];
  meets: MeetSearchResult[];
  teams: TeamSearchResult[];
  swimmers: SwimmerSearchResult[];
}

export interface InviteCheckOut {
  valid: boolean;
  reason: string | null;
}

export interface InviteOut {
  code: string;
  max_uses: number;
  uses_count: number;
  expires_at: string | null;
}

// WebSocket event payloads (see backend app/ws/events.py)
export type WsEvent =
  | { type: "book_update"; market_id: string; bids: PriceLevelOut[]; asks: PriceLevelOut[]; sequence: number }
  | { type: "trade"; market_id: string; price_cents: number; quantity: number; executed_at: string; sequence: number }
  | { type: "order_update"; order_id: string; status: OrderStatus; filled_quantity: number }
  | { type: "balance_update"; cash_balance_cents: number; available_cents: number }
  | {
      type: "market_resolved";
      market_id: string;
      market_group_id: string;
      winning_market_id: string;
      resolved_outcome: MarketOutcome;
    }
  | { type: "ticker_update"; meet_id: string; meet_event_id: string | null; body: string; created_at: string };
