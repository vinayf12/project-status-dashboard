---
name: project-status-board
description: >-
  Build a self-updating kanban board of your active client projects. It
  automatically finds your project channels (Slack channels you're in whose name
  carries a 6-digit project number) and cross-checks Asana — no need to list them.
  Each project is
  auto-classified (Not Started / In Progress / Waiting for Feedback / Stale) with
  a short summary, a few bullets, the team, last activity, and a link into its
  Slack channel — then published as a shareable Claude artifact on a stable link.
  Use when someone asks to "build my project status board", "show what's on my
  plate", "make a workload dashboard", or wants a shareable status board that
  refreshes itself. Also covers setting up a twice-daily auto-refresh routine.
---

# Project Status Board

Builds a shareable kanban board of the current user's active client projects and
keeps it fresh. Answers "what's on your plate / what are you working on?" in one
glanceable link.

## What you produce

1. A `data.json` config + snapshot (source of truth).
2. A self-contained `out.html` (the board, data baked inline — works inside the
   Claude artifact sandbox, no network calls).
3. A published **artifact** on a stable URL (same link on every refresh).
4. (Optional) A ready-to-paste **Routine** prompt for twice-daily auto-refresh.

Assets bundled with this skill (in `assets/`):
- `template.html` — the board UI. Contains the placeholder `__DATA_JSON__`.
- `generate.py` — bakes `data.json` into `out.html`.

---

## Step 1 — Ask only what can't be discovered

Ask the user for just two things:
- **Owner name** — shown as the board title (e.g. "Jordan Lee").
- **View passphrase** — a simple shared word for the gate (cosmetic only; tell
  them the page source + data are still readable by anyone with the link).

**Do NOT ask the user to list their projects.** Identify them automatically —
see the next step.

## Step 2 — Identify the projects automatically (the naming format)

Superside client project channels follow a consistent format:

```
<client>-<PROJECT_NUMBER>-<description>
```

- **`<client>`** (a real client/brand name) comes **BEFORE** a **6-digit
  `PROJECT_NUMBER`** (e.g. `224533`). The client-name-then-number shape is the
  reliable signal. Client slug may carry a suffix
  (`wex10-4-…`, `oysterhr-i-…`, `lucidmotor-…`, `dynaparcor-…`).
- **`<description>`** is the project name in slug form.

To build the project list:
1. Find the Slack channels the **current user is a member of** matching the
   pattern above. **Exclude:**
   - channels with no 6-digit project number (e.g. #everyone-can-build, #general),
   - **number-first** channels (the number leads, no real client name before it),
   - temp / test / scratch channels.
2. For each, capture `channel_id`, `channel_name`, and the `project_number`.
3. Derive a clean **`display_name`** = `"Client — Title Case Description"` using
   judgment. Examples:
   - `lucidmotor-252603-bookademopaidads` → `"Lucid Motors — Book a Demo Paid Ads"`
   - `oysterhr-i-199961-brandassetlibrary` → `"OysterHR — Brand Asset Library"`
   - `wex10-4-224533-cont-…-newclaims-paid` → `"Wex — New Claims Paid"`

**Membership is the on/off switch:** if the user has left a channel, drop that
project. Re-discover on every refresh so new channels appear and old ones fall
away automatically. **Transient-error guardrail:** only drop a project when the
channel is genuinely gone (`channel_not_found` *and* not found via search) — never
drop on a one-off API/transient error, or a flaky run would wipe real projects.
(If the user wants to hand-pick or exclude a few, let them — but the default is
auto-discovery, no list required.)

## Step 3 — Scan each project (read-only)

For EACH identified project, using the Slack and Asana connectors:
- Read recent messages in its Slack channel (`slack_read_channel` by channel_id).
- Cross-check the Asana milestones/tasks referenced for it (deadlines, overdue,
  approvals). The ops/automation posts in the channel usually mirror Asana.
- Decide a **status** — exactly one of:
  `Project Not Started`, `In Progress`, `Waiting for Feedback`, `Stale`.
  Guidance: *Stale* = client silent / no real progress for a while (call out how
  long). *Waiting for Feedback* = delivered, awaiting client reply. *In Progress*
  = active work or scheduled milestones. *Not Started* = kicked off but no work
  and nothing scheduled.
- Write a one-line **note** (concise summary) + 2–4 short **details** bullets of
  what's actually happening, a `last_activity` date (YYYY-MM-DD), and the **team**.
- **Drop fully-completed / closed projects** — if the work is delivered and the
  project is wrapped, leave it off the board (it's not "active" anymore).
- **Never post** anything to Slack or Asana. Read only.

## Step 4 — Write data.json

```json
{
  "owner": "Jordan Lee",
  "view_passphrase": "changeme",
  "worker_url": "",
  "updated_at": "<current UTC time, e.g. 2026-07-15T05:26:00Z>",
  "projects": [
    {
      "project_number": "224533",
      "channel_id": "C0AUNGM22DQ",
      "channel_name": "acme-224533-launch-video",
      "display_name": "Acme — Launch Video",
      "status": "In Progress",
      "note": "One-line summary of the current state.",
      "details": ["What happened / next milestone", "Another bullet"],
      "last_activity": "2026-07-15",
      "team": ["Jordan", "Sam", "Alex"]
    }
  ]
}
```
Notes:
- Format is `note` (one summary line) + `details` (2–4 short bullet fragments).
  There are no editable note boxes / `manual_note` fields — the board is read-only.
- Leave `worker_url` empty unless the user set up the advanced Sync button
  (see the advanced section). When empty, the board simply has no Sync button.

## Step 5 — Bake

```
python3 assets/generate.py data.json assets/template.html out.html
```
`generate.py` validates the JSON and injects it where `__DATA_JSON__` sits.

## Step 6 — Publish the artifact (stable link)

Publish `out.html` as an artifact.
- **First time:** publish normally; save the returned artifact URL somewhere
  durable (in `data.json` as a `_artifact_url` note, or tell the user to keep it).
- **Every later refresh:** publish to that **same URL** so the link never
  changes. Use title `"<owner> — Project Status"` and a stable favicon (📋).

## Step 7 (optional, tell the user it's advanced) — twice-daily auto-refresh

The board can rebuild itself server-side, twice a day, with the user's computer
off. This needs a **Routine** (a scheduled session) in the Claude Code web app —
the skill can't create it, but hand the user this to paste:

- Go to **claude.ai/code → Routines → New**, attach their repo (if any),
  pick a cadence (e.g. cron `30 2,14 * * *` = 8:00 AM / 8:00 PM in GMT+5:30 —
  convert to their zone: the field is read as UTC), and paste:

```
Rebuild the project status board.
1. Read data.json (and sync_request.json if present) for config + prior notes.
2. Re-identify my projects: the Slack channels I'm a member of whose name
   contains a 6-digit project number (format <client>-<NNNNNN>-<description>).
   Add channels that are new, drop ones I've left.
3. For each project: read its Slack channel + cross-check Asana, reclassify
   status (Project Not Started / In Progress / Waiting for Feedback / Stale),
   write a one-line note + 2-4 details bullets, last_activity, and the team.
   Drop fully-completed projects and channels I've left (transient-error guarded).
4. Write data.json with updated_at = current UTC time.
5. Run: python3 assets/generate.py data.json assets/template.html out.html
6. Publish out.html to the SAME existing artifact URL (do not create a new one).
Read-only in Slack/Asana — never post.
```

Verify one **Run now** succeeds before relying on it.

---

## Advanced — the "⟳ Sync now" button (Cloudflare Worker)

A button *inside* a Claude artifact can't make network calls, so an in-artifact
"Sync" that anyone can click needs a tiny always-on service. If the user wants it:

1. **Create a GitHub repo** to hold `data.json` + the board files.
2. **Deploy a Cloudflare Worker** (free tier) that:
   - serves the board (`index.html`) and `data.json`, and
   - exposes `POST /sync` — on hit, it writes/updates `sync_request.json`
     (a `{ "requested_at": "<ISO>" }` file) in the repo via a stored GitHub
     token (kept server-side in the Worker's secrets — never in the page).
3. Add a live `index.html` (a `fetch`-based twin of the board) that, when opened
   as `?sync=1`, POSTs to the Worker's `/sync` and shows a confirmation.
4. Set `worker_url` in `data.json` to the Worker's URL and re-bake — the board
   now shows **⟳ Sync now**, linking to `<worker_url>/?sync=1`. Anyone with the
   link can click it; it records a request that the routine picks up on its next
   run. (For near-instant pickup, add a second routine every ~30 min using the
   same prompt, guarded to only rebuild when `sync_request.json` is newer than
   `data.json`.)

This tier is optional. Without it, the board still auto-refreshes on the routine
schedule; users just trigger ad-hoc refreshes by asking Claude to "sync the board."
