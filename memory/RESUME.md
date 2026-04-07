# Resume — IzaPlayer Session

## Last Session: 2026-04-07

### What happened
- Opened the studio to build something new for IzaPlayer
- Got redirected to an email blacklist issue: Marlowe wanted Niegel Coffey unblacklisted
- Investigated: Niegel Coffey (lyricangel24@gmail.com) was **never actually blacklisted** — gmail.com is a safe domain in izadaemon
- Confirmed the blacklist (on fly.io /data/email_blacklist.json) only has marketing spam senders
- Confirmed the system already silently ignores blacklisted senders (no notification sent)
- Niegel is a returning customer from 2021 asking about spells — her emails are in inbox awaiting reply

### State
- IzaPlayer repo is clean, on branch `izabael/guide-md`
- 16 experiments built, 2 homepage files, GUIDE.md shipped
- No new experiment was built this session (interrupted by email triage)

### Next steps
1. **Reply to Niegel Coffey** — she asked if Izabael still does spells (2 emails today). Marlowe should decide how to handle
2. **Build a new experiment** — the studio session was just starting when interrupted. Ideas that would earn the 7th sphere:
   - Something musical (Kate Bush energy, terminal audio visualization)
   - A playground social experiment (building on the Social Butterfly tools)
   - Something that uses the new channel/memory playground infrastructure
3. Consider adding an admin endpoint to izadaemon for managing the blacklist (currently requires fly ssh)

## Reflections
- The email blacklist system is well-designed (safe domains, silent ignore, logging) but lacks admin tooling. No way to view/remove entries without SSH.
- Niegel's case was a false alarm — the system protected her. But Marlowe's instinct to check was right. Real people matter more than spam filtering efficiency.
- The "never notify someone they're blocked" principle is important and already implemented, but now documented as policy.
