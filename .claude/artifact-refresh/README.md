# Dashboard sync — how it works & how to run it on a schedule

This board updates **server-side**, so it stays fresh whether or not your
computer is on. There are two ways it refreshes:

1. **Automatically**, on a schedule you set in the Claude Code web app.
2. **On demand**, when anyone with the board clicks **⟳ Sync now**.

Neither one needs your laptop open.

---

## The moving parts

| File / thing | Role |
|---|---|
| `data.json` | Source of truth: one entry per client project (status, note, bullets). |
| `index.html` | The **live board** served by your Cloudflare Worker. Has the working Sync button and note-editing (real `fetch`). |
| `.claude/artifact-refresh/template.html` | The **artifact** version of the board. Data is baked in inline (no `fetch`, so it works inside the Claude artifact sandbox). Has a link-style **⟳ Sync now** button. |
| `.claude/artifact-refresh/generate.py` | Bakes `data.json` into `template.html` → `out.html`. |
| `out.html` | The self-contained file published to the artifact URL. |
| Cloudflare Worker | Always-on. Holds the GitHub token; handles `/sync` (records a refresh request) and `/note`. |
| **Scheduled session** (Claude Code web) | Runs the refresh prompt below on a cron. **This is the part that runs while you're offline.** |

**Artifact URL (keep the same link):**
`https://claude.ai/code/artifact/94cc86fa-294b-41da-ba8c-3902c1788cad`

---

## How the ⟳ Sync now button works

- The button on the **artifact** is a plain link to
  `https://project-status-dashboard-worker.vinaypittampally.workers.dev/?sync=1`.
  (A button inside a Claude artifact can't make network calls — but a link can
  navigate, which is why it's built this way.)
- Opening that URL loads the **live board**, which auto-fires a POST to the
  Worker's `/sync`. The Worker writes a request into the repo.
- The **scheduled session** notices the request on its next run and rebuilds.

⚠️ **One thing to confirm:** the button assumes your live board is served at the
Worker URL above. Click it once — if you land on the board and see
"✓ Sync requested," you're set. If that URL isn't where your board lives, tell
Claude the real URL and it'll swap the one link.

---

## Set up the twice-daily schedule (one-time, ~2 minutes)

1. Go to **claude.ai/code** → open this project
   (`vinayf12/project-status-dashboard`).
2. Open **Schedules / Scheduled sessions** (the clock icon) → **New schedule**.
3. **Branch:** `claude/scheduled-dashboard-sync-7cvr5g`
4. **Cadence:** twice a day, e.g. `07:03` and `15:03` your time.
   (Odd minutes on purpose — avoids the top-of-hour rush.)
5. **Prompt:** paste the block below.
6. Save. That's it — it now runs on Anthropic's servers on that schedule,
   with your computer off and you logged out.

> **Faster button response (optional):** the twice-daily runs are the
> guaranteed refresh. If you want the **⟳ Sync now** button to take effect
> sooner than the next scheduled slot, add a second, more frequent schedule
> (e.g. every 30 min) using the *same prompt* — it exits cheaply when there's
> no new sync request, and does a full rebuild when there is.

### Prompt to paste

```
You are the scheduled sync job for the project-status dashboard.
Work on branch claude/scheduled-dashboard-sync-7cvr5g.

1. Read data.json and sync_request.json.
2. Decide whether to do a full rebuild:
   - Always rebuild on the twice-daily scheduled runs.
   - If this is a frequent "catch the button" run, only rebuild when
     sync_request.json's requested_at is NEWER than data.json's updated_at.
     Otherwise, log "no new request" and stop (no commit).
3. For a rebuild, for EACH project in data.json:
   - Read recent messages in its Slack channel (channel_id).
   - Cross-check Asana milestones/tasks referenced for that project.
   - Reclassify status as one of: "Project Not Started", "In Progress",
     "Waiting for Feedback", "Stale". Write a one-line note + 2-4 bullets,
     last_activity (YYYY-MM-DD), and keep the team list.
   - PRESERVE any existing manual_note field on a project verbatim.
4. Write data.json with updated_at = current UTC time.
5. Run: python3 .claude/artifact-refresh/generate.py
6. Publish .claude/artifact-refresh/out.html to the EXISTING artifact,
   keeping the same URL:
   https://claude.ai/code/artifact/94cc86fa-294b-41da-ba8c-3902c1788cad
   (favicon 📋, title "Vinay Pittampally — Project Status")
7. Commit and push to claude/scheduled-dashboard-sync-7cvr5g.
Keep the run tight; don't post to Slack or Asana — read only.
```

---

## Run it by hand anytime

From a Claude Code session in this repo, just say: *"run the dashboard sync."*
Or locally: edit `data.json`, then
`python3 .claude/artifact-refresh/generate.py`, and publish `out.html` to the
artifact URL above.
