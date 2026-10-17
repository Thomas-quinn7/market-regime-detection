# Server-side record of the freeze pushes

Two files captured from GitHub on 2026-10-17 by the desk review (model-validator lane), from Thomas's
laptop, with the `gh` CLI authenticated as Thomas-quinn7. The exact `gh` command lines were not
recorded; the content matches the REST endpoints below. Copied here unchanged on 2026-10-17 by the
reopen lane (`/opt/hmm-agent/reviews/audit/`, file mtimes 2026-10-17 13:53:30Z kept).

| File | What it is | sha256 |
|---|---|---|
| `github_events_2026-10-17.json` | GitHub Events API for the repo (`GET /repos/Thomas-quinn7/market-regime-detection/events`): every PushEvent with its server-side `created_at` (UTC) and the `before` and `head` commits | `426ecf661c9b6a3d0109930e9749318b6305271735d13e3a2fbba13cc6aa1916` |
| `ci_runs_2026-10-17.txt` | GitHub Actions run list: one CI run per pushed head, with its server-side creation time (UTC), head commit, status and title | `5b51787ce6c05c20895020c7db7ab635d4e8355fd17f2285a86c547179a162cb` |

Why they are kept: they are the only record not under Thomas's control of when each holdout freeze
commit reached the public repository, as opposed to when it was committed locally. The Events API
keeps about 90 days of history, so the 13-14 October 2026 pushes drop out of it around 11-12 January
2027; after that these files are the only copy. Actions run logs also expire after 90 days.

Limits: a file in the repo is only as trustworthy as the repo. To anchor these copies independently,
the desk review recommends Wayback Machine snapshots of the four freeze commit pages and their
Actions runs, and OpenTimestamps on the four freeze hashes (which proves existence by the stamping
date, not by 13-14 October). Neither has been done yet; both are Thomas's.

How to read them: for each holdout, find the PushEvent whose `head` is the freeze commit or a
descendant of it and whose `before` is not; its `created_at` is when the freeze became public. The
desk review's model-validator report (Q1) tabulates the four holdouts from these files.
