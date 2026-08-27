import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  ApiError,
  closeMarket,
  createInvite,
  createMarketGroup,
  createMeet,
  createMeetEvent,
  createSwimmer,
  createTeam,
  createVenue,
  listMarketGroups,
  listMeetEvents,
  listMeets,
  listTeams,
  listVenues,
  postTickerUpdate,
  resolveMarketGroup,
} from "../api/client";
import type { CourseType, MarketGroupOut, MeetEventOut, MeetOut, MeetType, TeamOut, VenueOut } from "../api/types";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="admin-section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function ResultLine({ result, error }: { result: string | null; error: string | null }) {
  if (error) return <p className="error">{error}</p>;
  if (result) return <p className="success">{result}</p>;
  return null;
}

export function AdminPage() {
  const [venues, setVenues] = useState<VenueOut[]>([]);
  const [teams, setTeams] = useState<TeamOut[]>([]);
  const [meets, setMeets] = useState<MeetOut[]>([]);
  const [groups, setGroups] = useState<MarketGroupOut[]>([]);

  const refreshVenues = () => listVenues().then(setVenues).catch(() => {});
  const refreshTeams = () => listTeams().then(setTeams).catch(() => {});
  const refreshMeets = () => listMeets().then(setMeets).catch(() => {});
  const refreshGroups = () => listMarketGroups().then(setGroups).catch(() => {});

  useEffect(() => {
    refreshVenues();
    refreshTeams();
    refreshMeets();
    refreshGroups();
  }, []);

  return (
    <div>
      <h1>Admin</h1>
      <InviteSection />
      <VenueSection onCreated={refreshVenues} />
      <TeamSection venues={venues} onCreated={refreshTeams} />
      <SwimmerSection teams={teams} />
      <MeetSection teams={teams} venues={venues} onCreated={refreshMeets} />
      <MeetEventSection meets={meets} />
      <MarketGroupSection teams={teams} meets={meets} onCreated={refreshGroups} />
      <TickerSection meets={meets} />
      <CloseMarketSection groups={groups} onChanged={refreshGroups} />
      <ResolveSection groups={groups} onResolved={refreshGroups} />
    </div>
  );
}

function InviteSection() {
  const [maxUses, setMaxUses] = useState("20");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const invite = await createInvite(Number(maxUses), 90);
      setResult(`Invite code: ${invite.code} (share this with friends)`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create invite">
      <form onSubmit={handleSubmit}>
        <label>
          Max uses
          <input type="number" value={maxUses} onChange={(e) => setMaxUses(e.target.value)} min={1} />
        </label>
        <button type="submit">Create invite</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function VenueSection({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [courseType, setCourseType] = useState<CourseType | "">("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const venue = await createVenue({ name, address: address || null, course_type: courseType || null });
      setResult(`Created venue "${venue.name}"`);
      setName("");
      setAddress("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create venue">
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="DeNunzio Pool" />
        </label>
        <label>
          Address / location
          <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Princeton, NJ" />
        </label>
        <label>
          Course type
          <select value={courseType} onChange={(e) => setCourseType(e.target.value as CourseType | "")}>
            <option value="">Unspecified</option>
            <option value="scy">Short course yards (25yd)</option>
            <option value="scm">Short course meters (25m)</option>
            <option value="lcm">Long course meters (50m)</option>
          </select>
        </label>
        <button type="submit">Create venue</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function TeamSection({ venues, onCreated }: { venues: VenueOut[]; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [shortName, setShortName] = useState("");
  const [location, setLocation] = useState("");
  const [homeVenueId, setHomeVenueId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const team = await createTeam({
        name,
        short_name: shortName,
        location: location || null,
        home_venue_id: homeVenueId || null,
      });
      setResult(`Created team "${team.name}"`);
      setName("");
      setShortName("");
      setLocation("");
      setHomeVenueId("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create team">
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Princeton" />
        </label>
        <label>
          Short name
          <input value={shortName} onChange={(e) => setShortName(e.target.value)} required placeholder="PRIN" />
        </label>
        <label>
          Location
          <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Princeton, NJ" />
        </label>
        <label>
          Home venue
          <select value={homeVenueId} onChange={(e) => setHomeVenueId(e.target.value)}>
            <option value="">None</option>
            {venues.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Create team</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function SwimmerSection({ teams }: { teams: TeamOut[] }) {
  const [teamId, setTeamId] = useState("");
  const [name, setName] = useState("");
  const [classYear, setClassYear] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const swimmer = await createSwimmer(teamId, name, classYear ? Number(classYear) : null);
      setResult(`Added "${swimmer.name}" to the roster`);
      setName("");
      setClassYear("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Add swimmer to roster">
      <form onSubmit={handleSubmit}>
        <label>
          Team
          <select value={teamId} onChange={(e) => setTeamId(e.target.value)} required>
            <option value="" disabled>
              Select a team
            </option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Alex Smith" />
        </label>
        <label>
          Class year (optional)
          <input type="number" value={classYear} onChange={(e) => setClassYear(e.target.value)} placeholder="2027" />
        </label>
        <button type="submit" disabled={!teamId}>
          Add swimmer
        </button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function MeetSection({
  teams,
  venues,
  onCreated,
}: {
  teams: TeamOut[];
  venues: VenueOut[];
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [meetType, setMeetType] = useState<MeetType>("dual");
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const [venueId, setVenueId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Suggest the two teams' home venues first, so the common case (a dual
  // meet at one team's pool) is a top-of-list pick rather than a search.
  const orderedVenues = useMemo(() => {
    const homeVenueIds = [homeTeamId, awayTeamId]
      .map((teamId) => teams.find((t) => t.id === teamId)?.home_venue_id)
      .filter((id): id is string => Boolean(id));
    const suggested = venues.filter((v) => homeVenueIds.includes(v.id));
    const rest = venues.filter((v) => !homeVenueIds.includes(v.id));
    return { suggested, rest };
  }, [teams, venues, homeTeamId, awayTeamId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const meet = await createMeet({
        name,
        meet_type: meetType,
        home_team_id: homeTeamId || null,
        away_team_id: awayTeamId || null,
        venue_id: venueId || null,
        // datetime-local gives a value with no timezone, which JS's Date
        // constructor treats as local time — convert to a real UTC instant
        // before sending, or the stored time silently shifts by the
        // browser's UTC offset (3pm submitted became 10am displayed).
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
      });
      setResult(`Created meet "${meet.name}"`);
      setName("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create meet">
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Princeton vs Harvard" />
        </label>
        <label>
          Type
          <select value={meetType} onChange={(e) => setMeetType(e.target.value as MeetType)}>
            <option value="dual">Dual meet</option>
            <option value="tri">Tri-meet</option>
            <option value="championship">Championship</option>
          </select>
        </label>
        <label>
          Home team (optional)
          <select value={homeTeamId} onChange={(e) => setHomeTeamId(e.target.value)}>
            <option value="">None</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Away team (optional)
          <select value={awayTeamId} onChange={(e) => setAwayTeamId(e.target.value)}>
            <option value="">None</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Venue (optional — type to search)
          <select value={venueId} onChange={(e) => setVenueId(e.target.value)}>
            <option value="">None</option>
            {orderedVenues.suggested.length > 0 && (
              <optgroup label="Suggested (home venue of a selected team)">
                {orderedVenues.suggested.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </optgroup>
            )}
            <optgroup label="All venues">
              {orderedVenues.rest.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </optgroup>
          </select>
        </label>
        <label>
          Date &amp; time (optional)
          <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
        </label>
        <button type="submit">Create meet</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function MeetEventSection({ meets }: { meets: MeetOut[] }) {
  const [meetId, setMeetId] = useState("");
  const [name, setName] = useState("");
  const [eventOrder, setEventOrder] = useState("0");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const event = await createMeetEvent(meetId, name, Number(eventOrder));
      setResult(`Added event "${event.name}"`);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Add an event to a meet">
      <form onSubmit={handleSubmit}>
        <label>
          Meet
          <select value={meetId} onChange={(e) => setMeetId(e.target.value)} required>
            <option value="" disabled>
              Select a meet
            </option>
            {meets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Event name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="200 Free Relay" />
        </label>
        <label>
          Order (lower runs first)
          <input type="number" value={eventOrder} onChange={(e) => setEventOrder(e.target.value)} />
        </label>
        <button type="submit" disabled={!meetId}>
          Add event
        </button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function MarketGroupSection({
  teams,
  meets,
  onCreated,
}: {
  teams: TeamOut[];
  meets: MeetOut[];
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [teamIds, setTeamIds] = useState<string[]>([]);
  const [meetId, setMeetId] = useState("");
  const [meetEventId, setMeetEventId] = useState("");
  const [events, setEvents] = useState<MeetEventOut[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMeetEventId("");
    if (!meetId) {
      setEvents([]);
      return;
    }
    listMeetEvents(meetId).then(setEvents).catch(() => setEvents([]));
  }, [meetId]);

  function toggleTeam(teamId: string) {
    setTeamIds((prev) => (prev.includes(teamId) ? prev.filter((id) => id !== teamId) : [...prev, teamId]));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const group = await createMarketGroup({
        title,
        team_ids: teamIds,
        meet_id: meetId || null,
        meet_event_id: meetEventId || null,
      });
      setResult(`Created "${group.title}" with ${group.markets.length} outcome(s)`);
      setTitle("");
      setTeamIds([]);
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create outcome (what people can bet on)">
      <form onSubmit={handleSubmit}>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="Who wins the meet?" />
        </label>
        <label>
          Teams (one market per team you check)
          <div className="checkbox-list">
            {teams.map((t) => (
              <label key={t.id} className="checkbox-row">
                <input type="checkbox" checked={teamIds.includes(t.id)} onChange={() => toggleTeam(t.id)} />
                {t.name}
              </label>
            ))}
          </div>
        </label>
        <label>
          Meet (optional — scopes this to the whole meet)
          <select value={meetId} onChange={(e) => setMeetId(e.target.value)}>
            <option value="">None</option>
            {meets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        {meetId && (
          <label>
            Event (optional — scopes this to one event instead of the whole meet)
            <select value={meetEventId} onChange={(e) => setMeetEventId(e.target.value)}>
              <option value="">Whole meet</option>
              {events.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <button type="submit" disabled={teamIds.length === 0}>
          Create outcome
        </button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function TickerSection({ meets }: { meets: MeetOut[] }) {
  const [meetId, setMeetId] = useState("");
  const [body, setBody] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await postTickerUpdate(meetId, body);
      setResult("Posted.");
      setBody("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Post ticker update">
      <form onSubmit={handleSubmit}>
        <label>
          Meet
          <select value={meetId} onChange={(e) => setMeetId(e.target.value)} required>
            <option value="" disabled>
              Select a meet
            </option>
            {meets.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Update
          <input
            value={body}
            onChange={(e) => setBody(e.target.value)}
            required
            placeholder="Princeton wins the 200 Free Relay"
          />
        </label>
        <button type="submit" disabled={!meetId}>
          Post
        </button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function CloseMarketSection({ groups, onChanged }: { groups: MarketGroupOut[]; onChanged: () => void }) {
  const [marketId, setMarketId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const market = await closeMarket(marketId);
      setResult(`Market is now ${market.status}`);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Close market (halt trading)">
      <form onSubmit={handleSubmit}>
        <label>
          Market
          <select value={marketId} onChange={(e) => setMarketId(e.target.value)} required>
            <option value="" disabled>
              Select a market
            </option>
            {groups.map((g) => (
              <optgroup key={g.id} label={g.title}>
                {g.markets.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label} ({m.status})
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!marketId}>
          Close market
        </button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function ResolveSection({ groups, onResolved }: { groups: MarketGroupOut[]; onResolved: () => void }) {
  const [groupId, setGroupId] = useState("");
  const [winningMarketId, setWinningMarketId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedGroup = groups.find((g) => g.id === groupId);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const group = await resolveMarketGroup(groupId, winningMarketId);
      setResult(`Resolved "${group.title}" — payouts sent.`);
      onResolved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Resolve outcome">
      <form onSubmit={handleSubmit}>
        <label>
          Outcome group
          <select
            value={groupId}
            onChange={(e) => {
              setGroupId(e.target.value);
              setWinningMarketId("");
            }}
            required
          >
            <option value="" disabled>
              Select a group
            </option>
            {groups
              .filter((g) => g.status !== "resolved")
              .map((g) => (
                <option key={g.id} value={g.id}>
                  {g.title}
                </option>
              ))}
          </select>
        </label>
        {selectedGroup && (
          <label>
            Which outcome won?
            <select value={winningMarketId} onChange={(e) => setWinningMarketId(e.target.value)} required>
              <option value="" disabled>
                Select the winner
              </option>
              {selectedGroup.markets.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        )}
        <button type="submit" disabled={!groupId || !winningMarketId}>
          Resolve &amp; pay out
        </button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}
