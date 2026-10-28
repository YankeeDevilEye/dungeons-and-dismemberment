# Editable source for Dungeons & Dismemberment

This repo ships a Vite-built game on `gh-pages`. The original app source is not in git; the playable core lives in `src/base-bundle.js` (snapshot of the last known-good r32 build).

**Edit here, not the minified file by hand:**

| Path | Purpose |
| --- | --- |
| `src/base-bundle.js` / `src/base-bundle.css` | Frozen game core (r32) |
| `src/patches/build.py` | Applies r33–r38 patches |
| `src/patches/dd-taunts-block.js` | Enemy spot/swing/death taunts + TTS |
| `src/patches/draw-64bit.js` | 640×480 world buffer upscale |
| `src/overlays/r34-awesome.css` | Title, pad, fantasy, blood-heat CSS |
| `src/overlays/r35-feel.css` | Flesh & Thunder look pass + select pin / crowded HUD |
| `src/overlays/r37-feel.css` | Crystal pad, low-HP heal pulse, rise CTA |
| `src/config/copy.json` | Title / select / controls copy |

## Build

```bash
python3 src/patches/build.py
```

Writes hashed assets under `assets/`, and updates `index.html`, `sw.js`, and `manifest.webmanifest`.

Serve locally:

```bash
python3 -m http.server 8765
```
