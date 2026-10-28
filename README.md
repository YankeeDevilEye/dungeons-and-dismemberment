# Dungeons & Dismemberment

Playable GitHub Pages build of an adult Gauntlet-style dungeon crawler (**r38 portrait Safari**).

- **Play:** open this branch / Pages site (`?desktop=1` on desktop). Phone Safari works in portrait.
- **Edit:** see [`src/README.md`](src/README.md) — patches + overlays are the source of truth
- **Build:** `python3 src/patches/build.py`

## r38 portrait Safari

- Removed landscape-only **TURN THE DEVICE** gate that blocked all taps in portrait
- Manifest orientation is `any` — play portrait or landscape on phone
- Virtual pad + Descend work without rotating the phone

## r37 coin-up crawl

- Crystal dump on the thumb pad (`✦` / E / Q) — no longer keyboard-only
- Panic quaff heals snappier with a brief save-inv
- Soft-start nurseries so the first minutes teach smash-gen fantasy
- Room-clear callout + faster death→rise + stronger RISE CTA
- Crystal dump windup shorter; dump drips a little HP + inv
- Floor-0 coach banner; empty-heal tip points at crystals

## r36 iframe integrity

- Full-roll i-frames cover bile, rot, reaper, peel, grapple
- Hazard ticks honor post-hit inv; champ chunks respect taken mul

## r35 highlights

- Wetter look, SFX-forward mix, damage numbers, aim assist, magnet loot, Blood Momentum
