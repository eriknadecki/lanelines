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
  deleteMarketGroup,
  deleteMeet,
  deleteMeetEvent,
  deleteSwimmer,
  deleteTeam,
  deleteVenue,
  listMarketGroups,
  listMeetEvents,
  listMeets,
  listSwimmers,
  listTeams,
  listVenues,
  postTickerUpdate,
  resolveMarketGroup,
  uploadRosterCsv,
} from "../api/client";
import type {
  MarketGroupOut,
  MeetEventOut,
  MeetOut,
  MeetType,
  SwimmerOut,
  TeamOut,
  VenueOut,
} from "../api/types";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="admin-section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

type SubmitStatus = "idle" | "pending" | "success" | "error";

// The submit button itself is the feedback surface: click it, it shows a
// pending label, then turns green with a short confirmation or red with the
// backend's error, then reverts so the form is ready for the next action.
function useSubmitStatus(revertMs = 2200) {
  const [status, setStatus] = useState<SubmitStatus>("idle");
  const [message, setMessage] = useState<string | null>(null);

  function start() {
    setStatus("pending");
    setMessage(null);
  }
  function succeed(msg: string) {
    setStatus("success");
    setMessage(msg);
    window.setTimeout(() => setStatus("idle"), revertMs);
  }
  function fail(msg: string) {
    setStatus("error");
    setMessage(msg);
    window.setTimeout(() => setStatus("idle"), revertMs + 1200);
  }

  return { status, message, start, succeed, fail };
}

function SubmitButton({
  status,
  message,
  idleLabel,
  pendingLabel = "Working...",
  disabled,
}: {
  status: SubmitStatus;
  message: string | null;
  idleLabel: string;
  pendingLabel?: string;
  disabled?: boolean;
}) {
  const label =
    status === "pending" ? pendingLabel : status === "success" || status === "error" ? (message ?? idleLabel) : idleLabel;
  const className = "submit-button" + (status === "success" ? " success" : status === "error" ? " error" : "");
  return (
    <button type="submit" className={className} disabled={disabled || status === "pending"}>
      {label}
    </button>
  );
}

const FILL_REQUIRED_MESSAGE = "Fill in required fields";

// Client-side validation for required fields: replaces the browser's native
// "fill this in" popup with a red border on the empty field(s), driven by
// the same submit-button-turns-red mechanism used for backend errors.
function useValidation() {
  const [invalid, setInvalid] = useState<Set<string>>(new Set());

  function check(fields: Record<string, string>): boolean {
    const missing = new Set<string>();
    for (const [key, value] of Object.entries(fields)) {
      if (!value.trim()) missing.add(key);
    }
    setInvalid(missing);
    return missing.size === 0;
  }

  function fieldClass(key: string): string | undefined {
    return invalid.has(key) ? "input-invalid" : undefined;
  }

  return { check, fieldClass };
}

function FieldLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <span>
      {children}
      {required && <span className="required-asterisk"> *</span>}
    </span>
  );
}

// Deletion is guarded server-side (a 409 means something still references
// this row), so on failure the button itself turns red and shows the
// backend's explanation rather than trying to predict what's deletable.
function DeleteButton({ onDelete, onDeleted }: { onDelete: () => Promise<void>; onDeleted: () => void }) {
  const [status, setStatus] = useState<"idle" | "pending" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function handleClick() {
    setStatus("pending");
    setMessage(null);
    try {
      await onDelete();
      onDeleted();
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof ApiError ? err.message : "Failed to delete");
      window.setTimeout(() => setStatus("idle"), 3500);
    }
  }

  return (
    <button
      type="button"
      className={"delete-button" + (status === "error" ? " error" : "")}
      onClick={handleClick}
      disabled={status === "pending"}
    >
      {status === "pending" ? "Deleting..." : status === "error" ? message : "Delete"}
    </button>
  );
}

const ADMIN_SECTIONS = [
  { id: "invites", label: "Invites" },
  { id: "venues", label: "Venues" },
  { id: "teams", label: "Teams" },
  { id: "roster", label: "Roster" },
  { id: "meets", label: "Meets" },
  { id: "meet-events", label: "Meet events" },
  { id: "outcomes", label: "Outcomes (markets)" },
  { id: "ticker", label: "Ticker updates" },
  { id: "close-market", label: "Close market" },
  { id: "resolve", label: "Resolve outcome" },
] as const;

type AdminSectionId = (typeof ADMIN_SECTIONS)[number]["id"];

export function AdminPage() {
  const [activeSection, setActiveSection] = useState<AdminSectionId>("venues");
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
      <div className="admin-layout">
        <nav className="admin-sidebar">
          {ADMIN_SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              className={"admin-sidebar-item" + (activeSection === s.id ? " active" : "")}
              onClick={() => setActiveSection(s.id)}
            >
              {s.label}
            </button>
          ))}
        </nav>
        <div className="admin-content">
          {activeSection === "invites" && <InviteSection />}
          {activeSection === "venues" && (
            <VenueSection venues={venues} onCreated={refreshVenues} onDeleted={refreshVenues} />
          )}
          {activeSection === "teams" && (
            <TeamSection teams={teams} venues={venues} onCreated={refreshTeams} onDeleted={refreshTeams} />
          )}
          {activeSection === "roster" && <SwimmerSection teams={teams} />}
          {activeSection === "meets" && (
            <MeetSection
              meets={meets}
              teams={teams}
              venues={venues}
              onCreated={refreshMeets}
              onDeleted={refreshMeets}
            />
          )}
          {activeSection === "meet-events" && <MeetEventSection meets={meets} />}
          {activeSection === "outcomes" && (
            <MarketGroupSection
              teams={teams}
              meets={meets}
              groups={groups}
              onCreated={refreshGroups}
              onDeleted={refreshGroups}
            />
          )}
          {activeSection === "ticker" && <TickerSection meets={meets} />}
          {activeSection === "close-market" && <CloseMarketSection groups={groups} onChanged={refreshGroups} />}
          {activeSection === "resolve" && <ResolveSection groups={groups} onResolved={refreshGroups} />}
        </div>
      </div>
    </div>
  );
}

function InviteSection() {
  const [maxUses, setMaxUses] = useState("20");
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const submit = useSubmitStatus();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submit.start();
    try {
      const invite = await createInvite(Number(maxUses), 90);
      setInviteCode(invite.code);
      submit.succeed("Invite created.");
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create invite">
      <form onSubmit={handleSubmit}>
        <label className="field-full">
          Max uses
          <input type="number" value={maxUses} onChange={(e) => setMaxUses(e.target.value)} min={1} />
        </label>
        <SubmitButton status={submit.status} message={submit.message} idleLabel="Create invite" pendingLabel="Creating..." />
      </form>
      {inviteCode && (
        <p className="muted">
          Invite code: <code>{inviteCode}</code> (share this with friends)
        </p>
      )}
    </Section>
  );
}

function VenueSection({
  venues,
  onCreated,
  onDeleted,
}: {
  venues: VenueOut[];
  onCreated: () => void;
  onDeleted: () => void;
}) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const submit = useSubmitStatus();
  const validation = useValidation();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validation.check({ name })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await createVenue({ name, address: address || null });
      submit.succeed("Venue created.");
      setName("");
      setAddress("");
      onCreated();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create venue">
      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Name</FieldLabel>
          <input
            className={validation.fieldClass("name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="DeNunzio Pool"
          />
        </label>
        <label>
          Address / location
          <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Princeton, NJ" />
        </label>
        <SubmitButton status={submit.status} message={submit.message} idleLabel="Create venue" pendingLabel="Creating..." />
      </form>
      <ul className="entity-list">
        {venues.map((v) => (
          <li key={v.id}>
            <span>
              {v.name}
              {v.address ? ` — ${v.address}` : ""}
            </span>
            <DeleteButton onDelete={() => deleteVenue(v.id)} onDeleted={onDeleted} />
          </li>
        ))}
      </ul>
    </Section>
  );
}

function TeamSection({
  teams,
  venues,
  onCreated,
  onDeleted,
}: {
  teams: TeamOut[];
  venues: VenueOut[];
  onCreated: () => void;
  onDeleted: () => void;
}) {
  const [name, setName] = useState("");
  const [shortName, setShortName] = useState("");
  const [location, setLocation] = useState("");
  const [homeVenueId, setHomeVenueId] = useState("");
  const submit = useSubmitStatus();
  const validation = useValidation();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validation.check({ name, shortName })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await createTeam({
        name,
        short_name: shortName,
        location: location || null,
        home_venue_id: homeVenueId || null,
      });
      submit.succeed("Team created.");
      setName("");
      setShortName("");
      setLocation("");
      setHomeVenueId("");
      onCreated();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create team">
      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Name</FieldLabel>
          <input
            className={validation.fieldClass("name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Princeton"
          />
        </label>
        <label>
          <FieldLabel required>Short name</FieldLabel>
          <input
            className={validation.fieldClass("shortName")}
            value={shortName}
            onChange={(e) => setShortName(e.target.value)}
            placeholder="PRIN"
          />
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
        <SubmitButton status={submit.status} message={submit.message} idleLabel="Create team" pendingLabel="Creating..." />
      </form>
      <ul className="entity-list">
        {teams.map((t) => (
          <li key={t.id}>
            <span>
              {t.name} ({t.short_name})
            </span>
            <DeleteButton onDelete={() => deleteTeam(t.id)} onDeleted={onDeleted} />
          </li>
        ))}
      </ul>
    </Section>
  );
}

function SwimmerSection({ teams }: { teams: TeamOut[] }) {
  const [teamId, setTeamId] = useState("");
  const [name, setName] = useState("");
  const [classStanding, setClassStanding] = useState("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [roster, setRoster] = useState<SwimmerOut[]>([]);
  const addSubmit = useSubmitStatus();
  const csvSubmit = useSubmitStatus();
  const addValidation = useValidation();

  const refreshRoster = () => {
    if (!teamId) {
      setRoster([]);
      return;
    }
    listSwimmers(teamId).then(setRoster).catch(() => setRoster([]));
  };

  useEffect(refreshRoster, [teamId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!addValidation.check({ name })) {
      addSubmit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    addSubmit.start();
    try {
      await createSwimmer(teamId, name, classStanding || null);
      addSubmit.succeed("Swimmer added.");
      setName("");
      setClassStanding("");
      refreshRoster();
    } catch (err) {
      addSubmit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  async function handleCsvUpload(e: FormEvent) {
    e.preventDefault();
    if (!csvFile) return;
    csvSubmit.start();
    try {
      const added = await uploadRosterCsv(teamId, csvFile);
      csvSubmit.succeed(`${added.length} swimmer(s) added.`);
      setCsvFile(null);
      refreshRoster();
    } catch (err) {
      csvSubmit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Roster">
      <label>
        <FieldLabel required>Team</FieldLabel>
        <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
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

      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Name</FieldLabel>
          <input
            className={addValidation.fieldClass("name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Alex Smith"
          />
        </label>
        <label>
          Class (optional)
          <input value={classStanding} onChange={(e) => setClassStanding(e.target.value)} placeholder="FR" />
        </label>
        <SubmitButton
          status={addSubmit.status}
          message={addSubmit.message}
          idleLabel="Add swimmer"
          pendingLabel="Adding..."
          disabled={!teamId}
        />
      </form>

      <form onSubmit={handleCsvUpload}>
        <label className="field-full">
          Upload roster CSV (column 1: name, column 2: class — e.g. FR/SO/JR/SR)
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <SubmitButton
          status={csvSubmit.status}
          message={csvSubmit.message}
          idleLabel="Upload CSV"
          pendingLabel="Uploading..."
          disabled={!teamId || !csvFile}
        />
      </form>

      <ul className="entity-list">
        {roster.map((s) => (
          <li key={s.id}>
            <span>
              {s.name}
              {s.class_standing ? ` (${s.class_standing})` : ""}
            </span>
            <DeleteButton onDelete={() => deleteSwimmer(teamId, s.id)} onDeleted={refreshRoster} />
          </li>
        ))}
      </ul>
    </Section>
  );
}

function MeetSection({
  meets,
  teams,
  venues,
  onCreated,
  onDeleted,
}: {
  meets: MeetOut[];
  teams: TeamOut[];
  venues: VenueOut[];
  onCreated: () => void;
  onDeleted: () => void;
}) {
  const [name, setName] = useState("");
  const [meetType, setMeetType] = useState<MeetType>("dual");
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const [venueId, setVenueId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const submit = useSubmitStatus();
  const validation = useValidation();

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
    if (!validation.check({ name })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await createMeet({
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
      submit.succeed("Meet created.");
      setName("");
      onCreated();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create meet">
      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Name</FieldLabel>
          <input
            className={validation.fieldClass("name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Princeton vs Harvard"
          />
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
        <SubmitButton status={submit.status} message={submit.message} idleLabel="Create meet" pendingLabel="Creating..." />
      </form>
      <ul className="entity-list">
        {meets.map((m) => (
          <li key={m.id}>
            <span>
              {m.name} ({m.meet_type})
            </span>
            <DeleteButton onDelete={() => deleteMeet(m.id)} onDeleted={onDeleted} />
          </li>
        ))}
      </ul>
    </Section>
  );
}

function MeetEventSection({ meets }: { meets: MeetOut[] }) {
  const [meetId, setMeetId] = useState("");
  const [name, setName] = useState("");
  const [eventOrder, setEventOrder] = useState("0");
  const [events, setEvents] = useState<MeetEventOut[]>([]);
  const submit = useSubmitStatus();
  const validation = useValidation();

  const refreshEvents = () => {
    if (!meetId) {
      setEvents([]);
      return;
    }
    listMeetEvents(meetId).then(setEvents).catch(() => setEvents([]));
  };

  useEffect(refreshEvents, [meetId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validation.check({ meetId, name })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await createMeetEvent(meetId, name, Number(eventOrder));
      submit.succeed("Event added.");
      setName("");
      refreshEvents();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Add an event to a meet">
      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Meet</FieldLabel>
          <select
            className={validation.fieldClass("meetId")}
            value={meetId}
            onChange={(e) => setMeetId(e.target.value)}
          >
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
          <FieldLabel required>Event name</FieldLabel>
          <input
            className={validation.fieldClass("name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="200 Free Relay"
          />
        </label>
        <label>
          Order (lower runs first)
          <input type="number" value={eventOrder} onChange={(e) => setEventOrder(e.target.value)} />
        </label>
        <SubmitButton
          status={submit.status}
          message={submit.message}
          idleLabel="Add event"
          pendingLabel="Adding..."
          disabled={!meetId}
        />
      </form>
      <ul className="entity-list">
        {events.map((ev) => (
          <li key={ev.id}>
            <span>{ev.name}</span>
            <DeleteButton onDelete={() => deleteMeetEvent(meetId, ev.id)} onDeleted={refreshEvents} />
          </li>
        ))}
      </ul>
    </Section>
  );
}

function MarketGroupSection({
  teams,
  meets,
  groups,
  onCreated,
  onDeleted,
}: {
  teams: TeamOut[];
  meets: MeetOut[];
  groups: MarketGroupOut[];
  onCreated: () => void;
  onDeleted: () => void;
}) {
  const [title, setTitle] = useState("");
  const [teamIds, setTeamIds] = useState<string[]>([]);
  const [meetId, setMeetId] = useState("");
  const [meetEventId, setMeetEventId] = useState("");
  const [events, setEvents] = useState<MeetEventOut[]>([]);
  const submit = useSubmitStatus();
  const validation = useValidation();

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
    if (!validation.check({ title })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      const group = await createMarketGroup({
        title,
        team_ids: teamIds,
        meet_id: meetId || null,
        meet_event_id: meetEventId || null,
      });
      submit.succeed(`Outcome created with ${group.markets.length} market(s).`);
      setTitle("");
      setTeamIds([]);
      onCreated();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create outcome (what people can bet on)">
      <form onSubmit={handleSubmit}>
        <label className="field-full">
          <FieldLabel required>Title</FieldLabel>
          <input
            className={validation.fieldClass("title")}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Who wins the meet?"
          />
        </label>
        <label className="field-full">
          <FieldLabel required>Teams (one market per team you check)</FieldLabel>
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
        <SubmitButton
          status={submit.status}
          message={submit.message}
          idleLabel="Create outcome"
          pendingLabel="Creating..."
          disabled={teamIds.length === 0}
        />
      </form>
      <ul className="entity-list">
        {groups.map((g) => (
          <li key={g.id}>
            <span>
              {g.title} ({g.status})
            </span>
            {g.status !== "resolved" && (
              <DeleteButton onDelete={() => deleteMarketGroup(g.id)} onDeleted={onDeleted} />
            )}
          </li>
        ))}
      </ul>
    </Section>
  );
}

function TickerSection({ meets }: { meets: MeetOut[] }) {
  const [meetId, setMeetId] = useState("");
  const [body, setBody] = useState("");
  const submit = useSubmitStatus();
  const validation = useValidation();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validation.check({ meetId, body })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await postTickerUpdate(meetId, body);
      submit.succeed("Posted.");
      setBody("");
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Post ticker update">
      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Meet</FieldLabel>
          <select
            className={validation.fieldClass("meetId")}
            value={meetId}
            onChange={(e) => setMeetId(e.target.value)}
          >
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
          <FieldLabel required>Update</FieldLabel>
          <input
            className={validation.fieldClass("body")}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Princeton wins the 200 Free Relay"
          />
        </label>
        <SubmitButton
          status={submit.status}
          message={submit.message}
          idleLabel="Post"
          pendingLabel="Posting..."
          disabled={!meetId}
        />
      </form>
    </Section>
  );
}

function CloseMarketSection({ groups, onChanged }: { groups: MarketGroupOut[]; onChanged: () => void }) {
  const [marketId, setMarketId] = useState("");
  const submit = useSubmitStatus();
  const validation = useValidation();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validation.check({ marketId })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await closeMarket(marketId);
      submit.succeed("Market closed.");
      onChanged();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Close market (halt trading)">
      <form onSubmit={handleSubmit}>
        <label className="field-full">
          <FieldLabel required>Market</FieldLabel>
          <select
            className={validation.fieldClass("marketId")}
            value={marketId}
            onChange={(e) => setMarketId(e.target.value)}
          >
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
        <SubmitButton
          status={submit.status}
          message={submit.message}
          idleLabel="Close market"
          pendingLabel="Closing..."
          disabled={!marketId}
        />
      </form>
    </Section>
  );
}

function ResolveSection({ groups, onResolved }: { groups: MarketGroupOut[]; onResolved: () => void }) {
  const [groupId, setGroupId] = useState("");
  const [winningMarketId, setWinningMarketId] = useState("");
  const submit = useSubmitStatus();
  const validation = useValidation();

  const selectedGroup = groups.find((g) => g.id === groupId);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validation.check({ groupId, winningMarketId })) {
      submit.fail(FILL_REQUIRED_MESSAGE);
      return;
    }
    submit.start();
    try {
      await resolveMarketGroup(groupId, winningMarketId);
      submit.succeed("Outcome resolved — payouts sent.");
      onResolved();
    } catch (err) {
      submit.fail(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Resolve outcome">
      <form onSubmit={handleSubmit}>
        <label>
          <FieldLabel required>Outcome group</FieldLabel>
          <select
            className={validation.fieldClass("groupId")}
            value={groupId}
            onChange={(e) => {
              setGroupId(e.target.value);
              setWinningMarketId("");
            }}
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
            <FieldLabel required>Which outcome won?</FieldLabel>
            <select
              className={validation.fieldClass("winningMarketId")}
              value={winningMarketId}
              onChange={(e) => setWinningMarketId(e.target.value)}
            >
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
        <SubmitButton
          status={submit.status}
          message={submit.message}
          idleLabel="Resolve & pay out"
          pendingLabel="Resolving..."
          disabled={!groupId || !winningMarketId}
        />
      </form>
    </Section>
  );
}
