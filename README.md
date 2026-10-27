# Dungeons & Dismemberment

Playable GitHub Pages build of an adult Gauntlet-style dungeon crawler (**r36 iframe integrity**).

- **Play:** open this branch / Pages site (`?desktop=1` on desktop)
- **Edit:** see [`src/README.md`](src/README.md) — patches + overlays are the source of truth
- **Build:** `python3 src/patches/build.py`

## r36 iframe integrity

- Full-roll i-frames actually cover bile, rot, reaper, and banshee peel (not just `hurtHero`)
- Hazard ticks honor post-hit inv
- Drown grapple pull/damage skips during roll / inv
- Peel no longer strips bone armor in god mode
- Champion Fire / Spectral chunks respect damage-taken mul

## r35 highlights

- **Look** — wetter abattoir chrome, low-HP pulse, louder brand on title
- **Sound** — SFX-forward mix, meatier hits/swings/splats, music ducks under impact
- **Play** — floating damage numbers, full-roll i-frames, wider aim assist, magnet loot, snappier movers
- Keeps **r34 Blood Momentum** (streak power + nursery smash rewards)

## r35g playtest polish

- Title CTA is clickable; desk copy says Click / Enter
- Character select pins Descend + confirm hint in-viewport
- On-screen pad AUTO is off on desktop (`?desktop=1`)
- Fuller desktop help (G / Tab / I / C / T / RMB / skills)
- Crowded fights soften blood + low-HP veil for readability
