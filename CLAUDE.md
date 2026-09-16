# Sky Clean Air — Project Notes

Site build for Sky Clean Air (skycleanair.com), family-owned HVAC company serving San Diego County (San Ysidro–Fallbrook, some Temecula) and Orange County (San Clemente–Brea) since 2018. See `references/onboarding-info/` for the full client brief.

Design direction: moody dark-navy hero with a glowing cyan/teal gradient (`#2addea` / `#2dd2c7` / `#23d4d7`, pulled from the SCA logo mark), transitioning into clean light sections for trust/credibility content — structurally modeled on `lincoln-plumbing` (see `capri-plumbing/reference-website/lincoln-plumbing`), pulling copy/content from the legacy skycleanair.com site. Antonio for headlines, Inter for body copy.

## Git workflow — standing authorization

The user has authorized automatic git management for this repo. Unless told otherwise for a specific change:

- After making a meaningful set of file changes, stage, commit, and push to `origin main` without asking for confirmation each time.
- Still follow standard git hygiene: review `git status`/`git diff` before staging, write a clear commit message describing the "why," never force-push, never skip hooks, never amend existing commits (always create new ones).
- Still pause and ask before anything destructive or hard-to-reverse (history rewrites, branch deletion, resetting shared history) — auto-push of normal forward commits is in scope; those are not.
- If a commit touches something that looks like it could contain secrets/credentials, stop and flag it instead of pushing.
- Commit only the files relevant to the task just completed — don't sweep up unrelated untracked/modified files sitting in the working tree.

## Notes

- `assets/content/*.mp4` and `*.mov` are gitignored (over GitHub's 100MB limit, not web-optimized). They also turned out to be finished vertical (9:16) social-ad clips with burned-in captions, not clean b-roll — not usable as a hero background loop as originally planned. The hero uses a real client photo (`assets/images/hero-team.jpg`, from `assets/content/IMG_6339.jpeg`) instead.
- Nav links are in-page anchors (`#services`, `#about`, etc.) for now since only the homepage exists — swap to real page routes as each page gets built.
- Phone number is 619-304-8822 (from the onboarding doc) — the live legacy site displays a different number, (858) 346-5551, possibly a tracked marketing line; confirm with the client if the two need to be reconciled.
