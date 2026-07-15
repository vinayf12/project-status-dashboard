---
name: project-status-board
description: >-
  Build a self-updating kanban board of your active client projects, pulled from
  your Slack project channels and cross-checked against Asana. Each project is
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

## Step 1 — Gather config (ask, don't assume)

Ask the user for (or infer, then confirm):
- **Owner name** — shown as the board title (e.g. "Jordan Lee").
- **Projects to track** — either (a) they paste a list of Slack channels /
  project numbers, or (b) find the client project channels they're active in via
  Slack search and confirm the list with them. Don't guess silently.
- **View passphrase** — a simple shared word for the gate (cosmetic only; tell
  them the page source + data are still readable by anyone with the link).

## Step 2 — Scan each project (read-only)

For EACH project, using the Slack and Asana connectors:
- Read recent messages in its Slack channel (`slack_read_channel` by channel_id).
- Cross-check the Asana milestones/tasks referenced for it (deadlines, overdue,
  approvals). The ops/automation posts in the channel usually mirror Asana.
- Decide a **status** — exactly one of:
  `Project Not Started`, `In Progress`, `Waiting for Feedback`, `Stale`.
  Guidance: *Stale* = client silent / no real progress for a while (call out how
  long). *Waiting for Feedback* = delivered, awaiting client reply. *In Progress*
  = active work or scheduled milestones. *Not Started* = kicked off but no work
  and nothing scheduled.
- Write a one-line **note** + 2–4 **bullets** of what's actually happening,
  a `last_activity` date (YYYY-MM-DD), and the **team**.
- **Never post** anything to Slack or Asana. Read only.

## Step 3 — Write data.json

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
- Leave `worker_url` empty unless the user set up the advanced Sync button
  (Step 6). When empty, the board simply has no Sync button.
- If a `manual_note` field exists on a project from a previous run, **preserve it
  verbatim** — never overwrite user notes.

## Step 4 — Bake

```
python3 assets/generate.py data.json assets/template.html out.html
```
`generate.py` validates the JSON and injects it where `__DATA_JSON__` sits.

## Step 5 — Publish the artifact (stable link)

Publish `out.html` as an artifact.
- **First time:** publish normally; save the returned artifact URL somewhere
  durable (in `data.json` as a `_artifact_url` note, or tell the user to keep it).
- **Every later refresh:** publish to that **same URL** so the link never
  changes. Use title `"<owner> — Project Status"` and a stable favicon (📋).

## Step 6 (optional, tell the user it's advanced) — twice-daily auto-refresh

The board can rebuild itself server-side, twice a day, with the user's computer
off. This needs a **Routine** (a scheduled session) in the Claude Code web app —
the skill can't create it, but hand the user this to paste:

- Go to **claude.ai/code → Routines → New**, attach their repo (if any),
  pick a cadence (e.g. cron `30 2,14 * * *` = 8:00 AM / 8:00 PM in GMT+5:30 —
  convert to their zone: the field is read as UTC), and paste:

```
Rebuild the project status board.
1. Read data.json (and sync_request.json if present).
2. For each project: read its Slack channel + cross-check Asana, reclassify
   status (Project Not Started / In Progress / Waiting for Feedback / Stale),
   write a one-line note + 2-4 bullets, last_activity, and keep the team.
   Preserve any existing manual_note field verbatim.
3. Write data.json with updated_at = current UTC time.
4. Run: python3 assets/generate.py data.json assets/template.html out.html
5. Publish out.html to the SAME existing artifact URL (do not create a new one).
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
