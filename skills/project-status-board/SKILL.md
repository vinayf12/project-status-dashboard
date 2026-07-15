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

1. A `data.json` snapshot, built fresh in-session (no repo needed).
2. A self-contained `out.html` (the board, data baked inline — works inside the
   Claude artifact sandbox, no network calls).
3. A published **artifact** on a stable URL (same link on every refresh).
4. (Optional) A ready-to-paste **Routine** prompt for twice-daily auto-refresh.

**No repository required.** Everything runs from this skill's bundled files and
the user's Slack/Asana connectors. Work in a scratch dir. (A *private* repo is
only needed for the advanced Sync button — see the last section. Never use a
public repo: these boards contain candid client notes.)

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
- **First time:** publish normally, then **give the user the returned artifact
  URL and tell them to keep it** — it's the stable link they'll share, and the
  Routine needs it to republish to the same place.
- **Every later refresh:** publish to that **same URL** (pass it as `url=`) so the
  link never changes — otherwise a NEW link is minted. Use title
  `"<owner> — Project Status"` and a stable favicon (📋).

## Step 7 (optional) — twice-daily auto-refresh, no repo

The board can rebuild itself server-side, twice a day, with the user's computer
off. This needs a **Routine** (a scheduled session) in the Claude Code web app.
Because this skill is installed on the user's account, the Routine can just call
it — **no repository required.** The skill can't create the Routine, but hand the
user this to set up:

- Go to **claude.ai/code → Routines → New**. No repo needed (or attach a private
  one if they keep state there). Pick a cadence — the cron field is read as
  **UTC**, so convert: e.g. `30 2,14 * * *` = 8:00 AM / 8:00 PM in GMT+5:30.
  Paste this, filling in their artifact URL:

```
Use the project-status-board skill to rebuild my board and publish it to this
EXISTING artifact URL (pass it as url= so the link never changes):
<PASTE YOUR ARTIFACT URL>

Re-discover my projects fresh from Slack each run (channels I'm in whose name is
<client>-<6-digit number>-<description>); add new ones, drop channels I've left
or projects that are fully completed (don't drop on a transient error).
Read-only in Slack/Asana — never post.
```

Verify one **Run now** succeeds before relying on it. Keep any old local
scheduled task as a fallback until the Routine has a green run.

---

## Advanced — the "⟳ Sync now" button (Cloudflare Worker)

A button *inside* a Claude artifact can't make network calls, so an in-artifact
"Sync" that anyone can click needs a tiny always-on service. This tier is **not
required** — skip it and the board still auto-refreshes on the Routine schedule;
users just trigger ad-hoc refreshes by asking Claude to "sync my board."

⚠️ **Privacy first:** these boards contain candid client notes. Use a **PRIVATE**
repo, never public. And because GitHub Pages won't serve a private repo, the
**Worker must serve the board itself** (don't rely on Pages).

If the user still wants the button:

1. **Create a PRIVATE GitHub repo** to hold `data.json` + the board files.
2. **Deploy a Cloudflare Worker** (free tier) that:
   - **serves** the live board (`index.html`) and `data.json` directly (Worker
     Static Assets — not GitHub Pages), and
   - exposes `POST /sync` — on hit, writes/updates `sync_request.json`
     (`{ "requested_at": "<ISO>" }`) in the repo via a GitHub token kept in the
     Worker's secrets (server-side — never in the page).
3. The live `index.html` is a `fetch`-based twin of the board that, when opened as
   `?sync=1`, POSTs to `/sync` and shows a confirmation.
4. Set `worker_url` in `data.json` to the Worker's URL and re-bake — the artifact
   now shows **⟳ Sync now**, linking to `<worker_url>/?sync=1`. Anyone with the
   link can click it; it records a request the Routine picks up on its next run.
   (For near-instant pickup, add a second Routine every ~30 min using the same
   prompt, guarded to only rebuild when `sync_request.json` is newer than the
   last publish.)

Note: leave `worker_url` empty and there is simply no button — the recommended
default for anyone not running this infrastructure.
