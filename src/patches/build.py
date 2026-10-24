#!/usr/bin/env python3
"""Apply r33 play-polish patches onto the frozen r32 base bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PATCHES = SRC / "patches"
ASSETS = ROOT / "assets"
BUILD_ID = "r33p"

PAD_MORE_JS = """\
(function () {
  function boot() {
    const btn = document.getElementById('pad-more');
    if (!btn) return;
    const sync = () => {
      const vpad = document.querySelector('.vpad.touch, .vpad.arcade-primary');
      const menu = document.querySelector('.title-card, .diablo-select, .over-card, .char-select');
      const playing = !!document.querySelector('.vpad') && !menu;
      btn.hidden = !playing;
      btn.classList.toggle('touch-on', playing);
      if (!playing) {
        const pad = document.querySelector('.vpad');
        if (pad) pad.classList.remove('pad-expanded');
        btn.classList.remove('on');
        btn.textContent = 'More';
      }
    };
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const vpad = document.querySelector('.vpad');
      if (!vpad) return;
      const on = vpad.classList.toggle('pad-expanded');
      btn.classList.toggle('on', on);
      btn.textContent = on ? 'Less' : 'More';
    });
    setInterval(sync, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
"""


def sha8(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"patch failed: missing marker for {label}")
    return text.replace(old, new, 1)


def main() -> None:
    js = (SRC / "base-bundle.js").read_text(encoding="utf-8", errors="ignore")
    css = (SRC / "base-bundle.css").read_text(encoding="utf-8", errors="ignore")
    copy = json.loads((SRC / "config" / "copy.json").read_text())
    overlay = (SRC / "overlays" / "r33-polish.css").read_text()
    draw64 = (PATCHES / "draw-64bit.js").read_text().strip()
    taunts = (PATCHES / "dd-taunts-block.js").read_text().strip()

    import re

    m = re.search(
        r"draw\(e,t,n,r,i,a,o\)\{if\(this\.cssW=n,this\.cssH=r,p\.mobile\).*?"
        r"this\.fpsT>=\.5&&\(this\.fps=this\.fpsN/this\.fpsT,this\.fpsN=0,this\.fpsT=0\)\}",
        js,
        flags=re.S,
    )
    if not m:
        raise SystemExit("patch failed: r32 draw() not found")
    js = js[: m.start()] + draw64 + js[m.end() :]

    old_bark = "barkAt(e,t){let n=this.hero;j.bark(e.kind,t,(e.x-n.x)/420,Math.hypot(e.x-n.x,e.y-n.y))}"
    new_bark = (
        "barkAt(e,t){let n=this.hero;j.bark(e.kind,t,(e.x-n.x)/420,Math.hypot(e.x-n.x,e.y-n.y)),"
        "(t===`spot`||t===`attack`||t===`death`)&&ddTaunt(this,e,t)}"
    )
    js = replace_once(js, old_bark, new_bark, "barkAt")

    if "var ddTalk=0,ddTaunts=" in js:
        raise SystemExit("taunts already present")
    mount = "jsx)(l.StrictMode,{children:(0,P.jsx)(vu,{})}));"
    if mount not in js:
        js = js + "\n" + taunts + "\n"
    else:
        js = replace_once(js, mount, mount + taunts, "inject taunts")

    js = replace_once(
        js,
        "Arcade sins. Gauntlet body count. Something still screaming.",
        copy["titleSub"],
        "titleSub",
    )
    js = replace_once(
        js,
        "Pick a sinner. Descend into bile culverts, cyst nurseries, and abattoir floors. Capcom swagger, Gauntlet panic — mop what used to be a face.",
        copy["titleBlurb"],
        "titleBlurb",
    )
    js = replace_once(
        js,
        "Tap or press START to choose your sinner",
        copy["titleStartTouch"],
        "titleStartTouch",
    )
    js = replace_once(
        js,
        "Press Enter or START to choose your sinner",
        copy["titleStartDesk"],
        "titleStartDesk",
    )
    js = replace_once(
        js,
        "Gauntlet rules. Capcom manners. One coin, five sinners, zero mercy.",
        copy["selectSub"],
        "selectSub",
    )
    js = replace_once(
        js,
        "PLEASE INSERT COIN · TAP A SINNER · START TO DESCEND",
        copy["selectCoin"],
        "selectCoin",
    )

    old_pu = (
        "pu=`WASD move · LMB attack/pick up · RMB skill · 1-4 skills · 5-8 belt · R/F quaff · "
        "Shift roll · E magic · V relic ultimate · O relic · G use/travel · B bone-portal recall · "
        "Tab automap · I inventory · C character · T skills · Alt loot labels · P pause · M mute`"
    )
    old_mu = (
        "mu=`Phone: left stick move · A ⚔ attack (hold, auto-aims) · B/X skills · Y ♥ potion · "
        "L roll · R heavy · START pause · SELECT map · tap minimap · ⚑ travel · ↩ recall`"
    )
    js = replace_once(js, old_pu, f"pu=`{copy['keysDesk']}`", "keysDesk")
    js = replace_once(js, old_mu, f"mu=`{copy['keysTouch']}`", "keysTouch")

    js = replace_once(
        js,
        "className:`vpad${n?` touch`:``}`",
        "className:`vpad arcade-primary${n?` touch`:``}`",
        "arcade-primary class",
    )

    js = replace_once(js, "goreK=1;", "goreK=.55;", "goreK field init")
    js = replace_once(js, "this.goreK=1,", "this.goreK=.55,", "goreK reset")
    js = replace_once(js, "mc=420", "mc=260", "gib cap")
    js = replace_once(js, "hc=1600", "hc=900", "part cap")
    js = replace_once(js, "gc=80", "gc=48", "pool cap")
    js = replace_once(
        js,
        "u=(o?c?2.4:3.5:c?1.45:2.15)*l*(1+s*.7)",
        "u=(o?c?1.35:1.9:c?.85:1.15)*l*(1+s*.45)",
        "burst scale",
    )

    old_enemy = "drawEnemy(e,t,n){cc[t.kind];let r=t.r;if(t.meltT>0){"
    new_enemy = (
        "drawEnemy(e,t,n){cc[t.kind];let r=t.r;"
        "e.save(),e.translate(t.x,t.y),e.strokeStyle=`rgba(8,4,4,0.85)`,e.lineWidth=2.4,"
        "e.beginPath(),e.ellipse(0,3,r*1.15,r*.55,0,0,K),e.stroke(),e.restore();"
        "if(t.meltT>0){"
    )
    js = replace_once(js, old_enemy, new_enemy, "enemy silhouette")

    if "build-tag" in js:
        js = js.replace("r32g", "r33p", 1)

    out_css = css + "\n\n/* === r33 polish overlay === */\n" + overlay
    out_js = js

    js_hash = sha8(out_js.encode())
    css_hash = sha8(out_css.encode())
    js_name = f"index-{BUILD_ID}-{js_hash}.js"
    css_name = f"index-{BUILD_ID}-{css_hash}.css"

    ASSETS.mkdir(exist_ok=True)
    for p in ASSETS.glob("index-*.js"):
        p.unlink()
    for p in ASSETS.glob("index-*.css"):
        p.unlink()
    (ASSETS / js_name).write_text(out_js, encoding="utf-8")
    (ASSETS / css_name).write_text(out_css, encoding="utf-8")
    (ASSETS / "pad-more.js").write_text(PAD_MORE_JS, encoding="utf-8")

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🪓</text></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <meta name="theme-color" content="#12060a" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-title" content="Dismemberment" />
    <meta name="description" content="Dungeons &amp; Dismemberment: private adult Gauntlet crawl — bile culverts, cyst nurseries, abattoir floors." />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=IM+Fell+English:ital@0;1&family=Press+Start+2P&display=swap" rel="stylesheet" />
    <title>Dungeons &amp; Dismemberment</title>
    <link rel="manifest" href="./manifest.webmanifest" />
    <link rel="apple-touch-icon" sizes="180x180" href="./icon-180.png" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <script>if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {{ const had = !!navigator.serviceWorker.controller; let done = false; navigator.serviceWorker.addEventListener('controllerchange', () => {{ if (had && !done) {{ done = true; location.reload(); }} }}); addEventListener('load', () => navigator.serviceWorker.register('./sw.js', {{ updateViaCache: 'none' }}).then((r) => r.update()).catch(() => {{}})); }}</script>
    <link rel="stylesheet" crossorigin href="./assets/{css_name}">
    <script type="module" crossorigin src="./assets/{js_name}"></script>
  </head>
  <body>
    <div id="root"></div>
    <button type="button" class="pad-more" id="pad-more" aria-label="More controls" hidden>More</button>
    <script src="./assets/pad-more.js" defer></script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(html, encoding="utf-8")

    sw = f"""// Offline cache for Dungeons & Dismemberment (relative paths; works under /<repo>/ on GitHub Pages)
const CACHE = 'dd-{BUILD_ID}-polish';
const CORE = ["./","./assets/{css_name}","./assets/{js_name}","./assets/pad-more.js","./icon-180.png","./icon-192.png","./icon-512.png","./icon-maskable-512.png","./icon.svg","./index.html","./manifest.webmanifest"]; // voice clips: cached on first play
self.addEventListener('install', (e) => {{ e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', (e) => {{ e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('dd-') && k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener('fetch', (e) => {{
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (r.mode === 'navigate') {{
    e.respondWith(fetch(r.url, {{ cache: 'no-cache', credentials: 'same-origin' }}).then((res) => {{ const cp = res.clone(); caches.open(CACHE).then((c) => c.put('./', cp)); return res; }}).catch(() => caches.match('./')));
    return;
  }}
  if (u.origin === location.origin || u.host.endsWith('fonts.googleapis.com') || u.host.endsWith('fonts.gstatic.com')) {{
    e.respondWith(caches.match(r).then((hit) => hit || fetch(r).then((res) => {{ if (res.ok || res.type === 'opaque') {{ const cp = res.clone(); caches.open(CACHE).then((c) => c.put(r, cp)); }} return res; }})));
  }}
}});
"""
    (ROOT / "sw.js").write_text(sw, encoding="utf-8")

    manifest = {
        "name": "Dungeons & Dismemberment",
        "short_name": "Dismemberment",
        "description": "Private adult Gauntlet crawl - bile, cysts, abattoirs, and bad decisions.",
        "start_url": "./",
        "scope": "./",
        "display": "fullscreen",
        "orientation": "landscape",
        "background_color": "#12060a",
        "theme_color": "#12060a",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {
                "src": "icon-maskable-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
            {"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"},
        ],
    }
    (ROOT / "manifest.webmanifest").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    (ROOT / "README.md").write_text(
        """# Dungeons & Dismemberment

Playable GitHub Pages build of an adult Gauntlet-style dungeon crawler.

- **Play:** open this branch / Pages site
- **Edit:** see [`src/README.md`](src/README.md) - patches + overlays are the source of truth
- **Build:** `python3 src/patches/build.py`
""",
        encoding="utf-8",
    )

    print(f"built assets/{js_name}")
    print(f"built assets/{css_name}")
    print("updated index.html sw.js manifest.webmanifest README.md")


if __name__ == "__main__":
    main()
