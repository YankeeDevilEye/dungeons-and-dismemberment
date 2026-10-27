#!/usr/bin/env python3
"""Apply r33–r37 patches onto the frozen r32 base bundle.

r33 play-polish · r34 Abattoir Ascension · r35 Flesh & Thunder · r36 iframe integrity · r37 coin-up crawl
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PATCHES = SRC / "patches"
ASSETS = ROOT / "assets"
BUILD_ID = "r37"

PAD_MORE_JS = """\
(function () {
  function boot() {
    const btn = document.getElementById('pad-more');
    if (!btn) return;
    const sync = () => {
      const vpad = document.querySelector('.vpad');
      const menu = document.querySelector('.title-card, .diablo-select, .over-card, .char-select');
      const playing = !!vpad && !menu;
      btn.hidden = !playing;
      btn.classList.toggle('touch-on', playing);
      if (!playing) {
        if (vpad) vpad.classList.remove('pad-expanded');
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

BLOOD_METER_JS = (
    "t.phase===`play`&&t.killStreak>=2&&(function(e,t,n,r){"
    "let k=t.killStreak|0,w=Math.min(1,(t.streakT||0)/3.1),x=n/2,y=r-26,bw=152,fill=Math.min(1,k/30)*w;"
    "e.save();e.globalAlpha=.9;"
    "e.fillStyle=`rgba(8,3,4,0.62)`;e.fillRect(x-bw/2,y-9,bw,9);"
    "e.fillStyle=k>=20?`#ff5a2a`:k>=10?`#ff9a4a`:`#e8c070`;"
    "e.fillRect(x-bw/2,y-9,bw*fill,9);"
    "e.strokeStyle=`rgba(255,220,160,0.35)`;e.strokeRect(x-bw/2+.5,y-8.5,bw-1,8);"
    "e.font=`700 10px Cinzel, Georgia, serif`;e.fillStyle=`#ffe8c0`;"
    "e.fillText((k>=10?`BLOOD MOMENTUM `:`SLAUGHTER `)+k+`×`,x,y-14);"
    "e.restore()"
    "})(e,t,n,r),"
)


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
    overlay = (
        (SRC / "overlays" / "r34-awesome.css").read_text()
        + "\n\n"
        + (SRC / "overlays" / "r35-feel.css").read_text()
        + "\n\n"
        + (SRC / "overlays" / "r37-feel.css").read_text()
    )
    draw64 = (PATCHES / "draw-64bit.js").read_text().strip()
    taunts = (PATCHES / "dd-taunts-block.js").read_text().strip()

    import re

    # --- r33: 64-bit world buffer ---
    m = re.search(
        r"draw\(e,t,n,r,i,a,o\)\{if\(this\.cssW=n,this\.cssH=r,p\.mobile\).*?"
        r"this\.fpsT>=\.5&&\(this\.fps=this\.fpsN/this\.fpsT,this\.fpsN=0,this\.fpsT=0\)\}",
        js,
        flags=re.S,
    )
    if not m:
        raise SystemExit("patch failed: r32 draw() not found")
    js = js[: m.start()] + draw64 + js[m.end() :]

    # --- r33: enemy taunts ---
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

    # --- r33/r34: marketing copy ---
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

    # Title CTA: click as well as pointerdown (Enter already works)
    js = replace_once(
        js,
        "className:`title-card diablo-frame`,onPointerDown:z,role:`dialog`",
        "className:`title-card diablo-frame`,onPointerDown:z,onClick:z,role:`dialog`",
        "title click start",
    )

    # Desktop pad AUTO bug: (ie||!0) always true — pad should follow touch only
    js = replace_once(
        js,
        "le=ae===`on`||ae===`auto`&&(ie||!0)",
        "le=ae===`on`||ae===`auto`&&ie",
        "pad auto desktop",
    )

    # --- r33: combat readability (lower gore) ---
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

    # Crowd-aware blood — keep hits readable when the floor is full
    js = replace_once(
        js,
        "blood(e,t,n,r=0,i=0,a=1){let o=Math.round(n*2.05*this.goreK*(.4+.6*p.fx));",
        "blood(e,t,n,r=0,i=0,a=1){let _en=0;try{for(let _e of this.enemies)_e&&!_e.dead&&_en++}catch(_x){}"
        "let _crowd=_en>=12?.38:_en>=6?.58:1;"
        "let o=Math.round(n*2.05*this.goreK*(.4+.6*p.fx)*_crowd);",
        "crowd blood",
    )

    old_enemy = "drawEnemy(e,t,n){cc[t.kind];let r=t.r;if(t.meltT>0){"
    new_enemy = (
        "drawEnemy(e,t,n){cc[t.kind];let r=t.r;"
        "e.save(),e.translate(t.x,t.y),e.strokeStyle=`rgba(8,4,4,0.85)`,e.lineWidth=2.4,"
        "e.beginPath(),e.ellipse(0,3,r*1.15,r*.55,0,0,K),e.stroke(),e.restore();"
        "if(t.meltT>0){"
    )
    js = replace_once(js, old_enemy, new_enemy, "enemy silhouette")

    # ========== r34 Abattoir Ascension ==========

    # Mid-tier fodder a bit meatier (still Gauntlet-poppable)
    for old, new, label in [
        ("wretch:{hp:1,speed:78,dmg:14", "wretch:{hp:2,speed:78,dmg:14", "wretch hp"),
        ("grunt:{hp:4,speed:64,dmg:14", "grunt:{hp:6,speed:66,dmg:15", "grunt hp"),
        ("imp:{hp:2,speed:64,dmg:12", "imp:{hp:3,speed:68,dmg:13", "imp hp"),
        ("skeleton:{hp:4,speed:88,dmg:14", "skeleton:{hp:6,speed:90,dmg:15", "skeleton hp"),
        ("legion:{hp:5,speed:82,dmg:12", "legion:{hp:8,speed:84,dmg:14", "legion hp"),
        ("banshee:{hp:9,speed:80,dmg:24", "banshee:{hp:12,speed:82,dmg:25", "banshee hp"),
        ("brute:{hp:10,speed:50,dmg:26", "brute:{hp:14,speed:52,dmg:27", "brute hp"),
        ("drown:{hp:36,speed:48,dmg:20", "drown:{hp:40,speed:50,dmg:21", "drown hp"),
        ("abom:{hp:48,speed:52,dmg:22", "abom:{hp:54,speed:53,dmg:23", "abom hp"),
    ]:
        js = replace_once(js, old, new, label)

    # Floor scaling: slightly tougher bodies, softer late contact spikes
    js = replace_once(
        js,
        "s=Math.ceil((a.hp+r+Math.floor(o/3))*(1+o*.05)*1.4),c={id:this.nextId++,kind:e,x:t,y:n,r:a.r,hp:s,maxHp:s,speed:a.speed*(1+Math.min(.5,o*.06))*q(.9,1.1),dmg:Math.round(a.dmg*(1+o*.08)*1.15)",
        "s=Math.ceil((a.hp+r+Math.floor(o/3))*(1+o*.055)*1.5),c={id:this.nextId++,kind:e,x:t,y:n,r:a.r,hp:s,maxHp:s,speed:a.speed*(1+Math.min(.45,o*.055))*q(.9,1.1),dmg:Math.round(a.dmg*(1+Math.min(14,o)*.055+Math.max(0,o-14)*.03)*1.12)",
        "spawn scale",
    )

    # Hunger: a hair gentler early so momentum can cook
    js = replace_once(
        js,
        "this.god||(n.hp-=(.9+r*.14)*i.drainMul*e,",
        "this.god||(n.hp-=(.82+r*.125)*i.drainMul*e,",
        "hunger drain",
    )

    # Blood Momentum: mods() cache bust + power curve from kill streak
    js = replace_once(
        js,
        "if(n&&n.t===this.time&&n.hp===t)return n.m;",
        "if(n&&n.t===this.time&&n.hp===t&&n.streak===this.killStreak)return n.m;",
        "mods cache streak",
    )
    js = replace_once(
        js,
        "rs(this,r),r.poison+=r.venom,this.modsCache={t:this.time,hp:t,m:r},r}",
        "rs(this,r),r.poison+=r.venom,"
        "(function(g,m){let k=g.killStreak|0;if(k<3)return;let p=Math.min(1,(k-2)/20);"
        "m.meleeMul*=1+.1+p*.28;m.attackSpeedMul*=1+.08+p*.22;m.speedMul*=1+.05+p*.14;"
        "m.lifesteal+=.012+p*.045;m.dmgTakenMul*=1-Math.min(.14,p*.14);"
        "k>=10&&(m.drainMul*=.9);k>=20&&(m.meleeMul*=1.1,m.attackSpeedMul*=1.06);"
        "})(this,r),this.modsCache={t:this.time,hp:t,streak:this.killStreak,m:r},r}",
        "blood momentum mods",
    )

    # Longer streak window — momentum is the fantasy
    js = replace_once(
        js,
        "this.killStreak++,this.streakT=2.2,this.stats.maxCombo=Math.max(this.stats.maxCombo,this.killStreak)",
        "this.killStreak++,this.streakT=3.1,this.stats.maxCombo=Math.max(this.stats.maxCombo,this.killStreak)",
        "streak window",
    )

    # Earlier / juicier streak callouts
    js = replace_once(
        js,
        "let u=[[15,`KILLING SPREE`,`15 dead`],[30,`RAMPAGE`,`30 dead · the floor shakes`],[60,`UNSTOPPABLE`,`60 dead`],[100,`GODLIKE`,`100 dead`],[200,`ENDLESS CARNAGE`,`200 dead · they keep coming`]].find(([e])=>e===this.killStreak);",
        "let u=[[5,`BLOOD MOMENTUM`,`keep swinging`],[10,`ABATTOIR FLOW`,`don't stop`],[15,`KILLING SPREE`,`15 dead`],[30,`RAMPAGE`,`30 dead · the floor shakes`],[60,`UNSTOPPABLE`,`60 dead`],[100,`GODLIKE`,`100 dead`],[200,`ENDLESS CARNAGE`,`200 dead · they keep coming`]].find(([e])=>e===this.killStreak);",
        "streak callouts",
    )

    # Snappier hit juice (readable, not gore)
    js = replace_once(
        js,
        "o!==`magic`&&o!==`aura`&&o!==`dot`&&(this.hitstop=Math.max(this.hitstop,a?.085:.04),this.shake=Math.max(this.shake,a?7:3),j.hit(a)",
        "o!==`magic`&&o!==`aura`&&o!==`dot`&&(this.hitstop=Math.max(this.hitstop,a?.1:.05),this.shake=Math.max(this.shake,a?9:4),j.hit(a)",
        "hit juice",
    )

    # Generator smash fuels the streak — smash nurseries, ride the blood
    js = replace_once(
        js,
        "e.hp<=0){e.dead=!0,this.stats.gens++;let t=100*Math.ceil(e.maxHp/4);this.score+=t,this.gainXp(40+e.maxHp*4);",
        "e.hp<=0){e.dead=!0,this.stats.gens++;"
        "this.killStreak=Math.max(this.killStreak,8),this.streakT=Math.max(this.streakT,3.8),"
        "this.hero&&(this.hero.inv=Math.max(this.hero.inv||0,.5),"
        "this.hero.hp=Math.min(this.hero.maxHp,this.hero.hp+this.hero.maxHp*.05));"
        "let t=100*Math.ceil(e.maxHp/4);this.score+=t,this.gainXp(40+e.maxHp*4);",
        "gen momentum reward",
    )
    js = replace_once(
        js,
        "this.callout(`GENERATOR DESTROYED`,`+${t}`,`#ffb04a`);",
        "this.callout(`NURSERY SILENCED`,`+${t} · blood surges`,`#ffb04a`);",
        "gen callout",
    )

    # Blood meter HUD + DOM heat class
    js = replace_once(
        js,
        "drawHud(e,t,n,r){if(e.save(),e.textAlign=`center`,t.banner&&",
        "drawHud(e,t,n,r){if(e.save(),e.textAlign=`center`," + BLOOD_METER_JS + "t.banner&&",
        "blood meter hud",
    )
    js = replace_once(
        js,
        "this.streakT>0&&(this.streakT-=e,this.streakT<=0&&(this.killStreak=0));",
        "this.streakT>0&&(this.streakT-=e,this.streakT<=0&&(this.killStreak=0));"
        "try{let _s=document.querySelector(`.app-shell`);_s&&_s.classList.toggle(`blood-hot`,(this.killStreak|0)>=8)}catch(_e){}",
        "blood-hot class",
    )

    # ========== r35 Flesh & Thunder ==========

    # Floating damage numbers — combat readability
    js = replace_once(
        js,
        "e.hp-=c,a&&o===`melee`&&c>=e.maxHp*.5&&e.hp>-e.maxHp&&this.hv(`crit`),",
        "e.hp-=c,"
        "o!==`dot`&&o!==`aura`&&c>=1&&this.text(e.x+q(-5,5),e.y-12-q(0,10),"
        "`${Math.max(1,Math.round(c))}`,a?`#ffe08a`:c>=20?`#ffb070`:`#f0e6d0`,a?15:c>=20?13:11,a?.95:.55),"
        "a&&o===`melee`&&c>=e.maxHp*.5&&e.hp>-e.maxHp&&this.hv(`crit`),",
        "damage numbers",
    )

    # Full-roll i-frames (was cutting early at .28 of .34)
    js = replace_once(
        js,
        "if(i.roll&&i.roll.t<.28){Math.random()<.45&&(this.text(i.x,i.y-16,`ROLL`,`#7cb4ff`,11,.55),this.sparks(i.x,i.y,8,`#7cb4ff`));return}",
        "if(i.roll&&i.roll.t<.36){Math.random()<.55&&(this.text(i.x,i.y-16,`ROLL`,`#7cb4ff`,12,.6),this.sparks(i.x,i.y,10,`#7cb4ff`));return}",
        "roll iframes",
    )

    # Snappier dodge roll
    js = replace_once(
        js,
        "n.roll.t+=e;let t=1-n.roll.t/.34,r=1+(i.whirlSpins>1?.2*(i.whirlSpins-1):0);_=n.roll.dx*320*r*Math.max(.3,t),v=n.roll.dy*320*r*Math.max(.3,t),n.roll.t>=.34&&(n.roll=null,n.rollCd=.12*i.rollCdMul)",
        "n.roll.t+=e;let t=1-n.roll.t/.32,r=1+(i.whirlSpins>1?.2*(i.whirlSpins-1):0);_=n.roll.dx*360*r*Math.max(.35,t),v=n.roll.dy*360*r*Math.max(.35,t),n.roll.t>=.32&&(n.roll=null,n.rollCd=.1*i.rollCdMul)",
        "roll speed",
    )

    # Wider aim assist
    js = replace_once(
        js,
        "assistTarget(e,t,n){let r=this.hero,i=null,a=1/0,o=null,s=1/0,c=t?.85:.96,",
        "assistTarget(e,t,n){let r=this.hero,i=null,a=1/0,o=null,s=1/0,c=t?1.05:1.2,",
        "assist cone",
    )
    js = replace_once(
        js,
        "assistTarget(o.x||o.y?Math.atan2(o.y,o.x):n.face,!!(o.x||o.y),d.some(Boolean)||f&&n.rskill!==`heavy`?260:sc.l1.reach+i.reachAdd+46)",
        "assistTarget(o.x||o.y?Math.atan2(o.y,o.x):n.face,!!(o.x||o.y),d.some(Boolean)||f&&n.rskill!==`heavy`?360:sc.l1.reach+i.reachAdd+72)",
        "assist range",
    )

    # Magnet pickup
    js = replace_once(
        js,
        "for(let e of this.items)e.taken||Math.hypot(e.x-n.x,e.y-n.y)<n.r+11&&this.pickup(e);for(let e of this.loot)if(!(e.taken||e.z>1)){if(Math.hypot(e.x-n.x,e.y-n.y)>n.r+10){",
        "for(let e of this.items)e.taken||Math.hypot(e.x-n.x,e.y-n.y)<n.r+18&&this.pickup(e);for(let e of this.loot)if(!(e.taken||e.z>1)){if(Math.hypot(e.x-n.x,e.y-n.y)>n.r+16){",
        "pickup magnet",
    )

    # Snappier class move speeds (~8%)
    for old, new, label in [
        ("speed:132,melee:1.2,reach:4,pots:1", "speed:144,melee:1.2,reach:4,pots:1", "barb speed"),
        ("speed:156,melee:.9,reach:0,pots:2", "speed:168,melee:.9,reach:0,pots:2", "ama speed"),
        ("speed:140,melee:.58,reach:-4,pots:4", "speed:152,melee:.58,reach:-4,pots:4", "sorc speed"),
        ("speed:128,melee:1.1,reach:2,pots:2", "speed:140,melee:1.1,reach:2,pots:2", "pal speed"),
        ("speed:136,melee:.8,reach:0,pots:3", "speed:148,melee:.8,reach:0,pots:3", "nec speed"),
    ]:
        js = replace_once(js, old, new, label)

    # Audio mix — SFX punch through, music sits under
    js = replace_once(
        js,
        "vol={master:.85,music:.48,sfx:.98}",
        "vol={master:.9,music:.32,sfx:1}",
        "default mix",
    )

    # Meatier hit / swing / splat
    js = replace_once(
        js,
        "hit(e=!1){if(!this.ok(`hit`,.028))return;let t=this.t,n=O(.88,1.12);this.thump(t,(e?150:210)*n,45,e?.22:.1,e?.5:.32),this.nz(t,e?.14:.07,`lowpass`,2600*n,260,1,e?.32:.22),this.click(t,O(900,1500),2,e?.16:.1,.018),e&&this.boneSnap()}",
        "hit(e=!1){if(!this.ok(`hit`,.022))return;let t=this.t,n=O(.88,1.12);this.thump(t,(e?125:185)*n,58,e?.3:.15,e?.68:.44),this.nz(t,e?.2:.11,`lowpass`,2100*n,200,1.35,e?.42:.3),this.click(t,O(750,1350),3,e?.22:.14,.022),e&&(this.boneSnap(),this.duck(.09)),!e&&this.duck(.045)}",
        "meaty hits",
    )
    js = replace_once(
        js,
        "swing(e=!1){if(!this.ok(`swing`,.05))return;let t=this.t,n=O(.9,1.1);this.nz(t,e?.3:.15,`bandpass`,(e?420:1300)*n,(e?2e3:3800)*n,1.6,e?.36:.24,void 0,e?.06:.03),e&&this.tone(t,.3,`sawtooth`,70,45,.06)}",
        "swing(e=!1){if(!this.ok(`swing`,.04))return;let t=this.t,n=O(.9,1.1);this.nz(t,e?.36:.2,`bandpass`,(e?380:1200)*n,(e?2200:4e3)*n,1.75,e?.42:.3,void 0,e?.07:.04),e&&this.tone(t,.34,`sawtooth`,65,42,.08)}",
        "meaty swings",
    )
    js = replace_once(
        js,
        "splat(e=1){if(!this.ok(`splat`,.03))return;let t=this.t,n=O(.88,1.15);this.thump(t,105*n-e*14,28,.24+e*.08,.55+e*.12),this.nz(t,.28+e*.14,`lowpass`,1800*n,110,4,.42+e*.08),this.nz(t+.012,.2+e*.1,`bandpass`,780*n,220,8,.34),this.nz(t+.04,.16,`bandpass`,420*n,700,10,.18)",
        "splat(e=1){if(!this.ok(`splat`,.025))return;this.duck(.07+e*.04);let t=this.t,n=O(.88,1.15);this.thump(t,95*n-e*12,36,.3+e*.1,.68+e*.14),this.nz(t,.34+e*.16,`lowpass`,1600*n,100,4.5,.5+e*.1),this.nz(t+.01,.24+e*.12,`bandpass`,720*n,200,8,.4),this.nz(t+.035,.18,`bandpass`,400*n,650,10,.22)",
        "meaty splat",
    )

    # Snappier hit juice on top of r34
    js = replace_once(
        js,
        "o!==`magic`&&o!==`aura`&&o!==`dot`&&(this.hitstop=Math.max(this.hitstop,a?.1:.05),this.shake=Math.max(this.shake,a?9:4),j.hit(a)",
        "o!==`magic`&&o!==`aura`&&o!==`dot`&&(this.hitstop=Math.max(this.hitstop,a?.12:.055),this.shake=Math.max(this.shake,a?11:5),j.hit(a)",
        "r35 hit juice",
    )

    # Low-HP DOM heat (with blood-hot) + crowded readability class
    js = replace_once(
        js,
        "try{let _s=document.querySelector(`.app-shell`);_s&&_s.classList.toggle(`blood-hot`,(this.killStreak|0)>=8)}catch(_e){}",
        "try{let _s=document.querySelector(`.app-shell`);if(_s){_s.classList.toggle(`blood-hot`,(this.killStreak|0)>=8);"
        "let _h=this.hero;_s.classList.toggle(`low-hp`,!!(_h&&_h.maxHp>0&&_h.hp/_h.maxHp<.32&&this.phase===`play`));"
        "let _en=0;try{for(let _e of this.enemies)_e&&!_e.dead&&_en++}catch(_x){}"
        "_s.classList.toggle(`crowded`,_en>=6&&this.phase===`play`)}}catch(_e){}",
        "low-hp class",
    )

    # Enemy heat feeds music intensity via streak
    js = replace_once(
        js,
        "setEnemyHeat(e){this.gs.heat=e,this.enemyHeat=e}",
        "setEnemyHeat(e){this.gs.heat=Math.max(e,(this.killStreak|0)>=8?Math.min(1,.35+(this.killStreak|0)*.02):e),this.enemyHeat=this.gs.heat}",
        "streak heat music",
    )

    # ========== r36 iframe integrity ==========
    # r35 extended hurtHero roll iframes to .36 but left hazard paths on .28
    # while the roll itself ends at .32 — dodge felt broken in bile / rot / peel.

    js = replace_once(
        js,
        "tileAt(Math.floor(n.x/32),Math.floor(n.y/32))===6&&!e.god&&!(n.roll&&n.roll.t<.28)&&(n.hp-=(16+r*2.5)*t,e.lastHurtBy=`a boiling bile soak`,n.hurtFlash=Math.max(n.hurtFlash,.08),Math.random()<.3&&e.sparks(n.x,n.y,2,`#ff7a2a`))",
        "tileAt(Math.floor(n.x/32),Math.floor(n.y/32))===6&&!e.god&&!(n.inv>0||n.roll&&n.roll.t<.36)&&(n.hp-=(16+r*2.5)*t,e.lastHurtBy=`a boiling bile soak`,n.hurtFlash=Math.max(n.hurtFlash,.08),Math.random()<.3&&e.sparks(n.x,n.y,2,`#ff7a2a`))",
        "bile roll+inv",
    )
    js = replace_once(
        js,
        "o.kind===`drown`&&r&&Math.hypot(t.x-o.x,t.y-o.y)<70&&(this.god,!this.god&&t.inv<=0&&!(t.roll&&t.roll.t<.28)&&(t.hp-=3.5*e,Math.random()<.04&&this.text(t.x,t.y-12,`Rot`,`#6a9a4a`,9,.4)))",
        "o.kind===`drown`&&r&&Math.hypot(t.x-o.x,t.y-o.y)<70&&(!this.god&&t.inv<=0&&!(t.roll&&t.roll.t<.36)&&(t.hp-=3.5*e,Math.random()<.04&&this.text(t.x,t.y-12,`Rot`,`#6a9a4a`,9,.4)))",
        "rot roll iframe",
    )
    js = replace_once(
        js,
        "o.kind===`reaper`&&c<T+2)!this.god&&!(t.roll&&t.roll.t<.28)&&(t.hp-=(26+n*2)*e,t.hurtFlash=.1,this.lastHurtBy=cc.reaper.name,Math.random()<.3&&this.blood(t.x,t.y,1,i,s,.4))",
        "o.kind===`reaper`&&c<T+2)!this.god&&!(t.inv>0||t.roll&&t.roll.t<.36)&&(t.hp-=(26+n*2)*e,t.hurtFlash=.1,this.lastHurtBy=cc.reaper.name,Math.random()<.3&&this.blood(t.x,t.y,1,i,s,.4))",
        "reaper roll+inv",
    )
    js = replace_once(
        js,
        "peelHero(e,t,n){let r=this.hero;if(this.phase===`play`&&!(!this.god&&(r.inv>0||r.roll&&r.roll.t<.28))){r.boneArmor=0,r.skinPeel=Math.max(r.skinPeel,1.6),this.god||this.hurtHero(e,cc.banshee.name,t,n);",
        "peelHero(e,t,n){let r=this.hero;if(this.phase===`play`&&!this.god&&!(r.inv>0||r.roll&&r.roll.t<.36)){r.boneArmor=0,r.skinPeel=Math.max(r.skinPeel,1.6),this.hurtHero(e,cc.banshee.name,t,n);",
        "peel roll+god gate",
    )
    js = replace_once(
        js,
        "o.kind===`drown`&&o.grappleT>0&&r)Math.hypot(t.x-o.x,t.y-o.y)<50&&(t.x+=(o.x-t.x)*Math.min(1,2.2*e),t.y+=(o.y-t.y)*Math.min(1,2.2*e),this.god||(t.hp-=6*e));",
        "o.kind===`drown`&&o.grappleT>0&&r)Math.hypot(t.x-o.x,t.y-o.y)<50&&!(t.inv>0||t.roll&&t.roll.t<.36)&&(t.x+=(o.x-t.x)*Math.min(1,2.2*e),t.y+=(o.y-t.y)*Math.min(1,2.2*e),this.god||(t.hp-=6*e));",
        "grapple roll+inv",
    )
    # Champ on-hit chunks still land after a real hit, but respect taken mul
    js = replace_once(
        js,
        "a===`Fire Enchanted`?(e.god||(r.hp-=3+i),e.sparks(r.x,r.y,4,`#ff7a2a`)):a===`Spectral Hit`&&(e.god||(r.hp-=n*.3),e.sparks(r.x,r.y,5,ao([`#ff7a2a`,`#9fd8ff`,`#e8f4ff`])))}",
        "a===`Fire Enchanted`?(e.god||(r.hp-=(3+i)*(e.mods().dmgTakenMul||1)),e.sparks(r.x,r.y,4,`#ff7a2a`)):a===`Spectral Hit`&&(e.god||(r.hp-=n*.3*(e.mods().dmgTakenMul||1)),e.sparks(r.x,r.y,5,ao([`#ff7a2a`,`#9fd8ff`,`#e8f4ff`])))}",
        "champ bonus taken mul",
    )

    # ========== r37 Coin-Up Crawl ==========
    # Crystal dump on the thumb pad (was keyboard-only E/Q — dead loot on phone)
    js = replace_once(
        js,
        "su={A:`attack`,B:`skill1`,X:`skill2`,Y:`quickHp`,L:`roll`,R:`rskill`,U:`ult`}",
        "su={A:`attack`,B:`skill1`,X:`skill2`,Y:`quickHp`,L:`roll`,R:`rskill`,U:`ult`,M:`magic`}",
        "pad magic map",
    )
    js = replace_once(
        js,
        "let ee=[[`A`,`⚔`,null],[`B`,`①`,_?i[0]??null:null],[`X`,`②`,_?i[1]??null:null],[`Y`,`♥`,null]]",
        "let ee=[[`A`,`⚔`,null],[`B`,`①`,_?i[0]??null:null],[`X`,`②`,_?i[1]??null:null],[`Y`,`♥`,null],[`M`,`✦`,null]]",
        "pad magic glyph",
    )
    js = replace_once(
        js,
        "L:{...d(u,180),d:o},Y:{...d(u,206),d:o},U:{...d(u,232),d:o},SELECT:",
        "L:{...d(u,180),d:o},Y:{...d(u,206),d:o},U:{...d(u,232),d:o},M:{x:s-Math.round(i*.95),y:c-Math.round(i*.22),d:o},SELECT:",
        "pad magic touch layout",
    )
    js = replace_once(
        js,
        "U:{x:c-f*1.15,y:l-f*1.15,d:Math.round(44*a)},SELECT:",
        "U:{x:c-f*1.15,y:l-f*1.15,d:Math.round(44*a)},M:{x:c+f*1.15,y:l-f*1.15,d:Math.round(44*a)},SELECT:",
        "pad magic desk layout",
    )

    # Panic quaff — belt pots land as a save, not a drip
    js = replace_once(
        js,
        "t.hpPool+=t.maxHp*n.power,t.hpRate=Math.max(t.hpRate,t.hpPool/2),this.text(t.x,t.y-24,`Glug.`,`#ff6a6a`,10,.7)",
        "t.hpPool+=t.maxHp*n.power,t.hpRate=Math.max(t.hpRate,t.hpPool/1.2),t.inv=Math.max(t.inv,.28),"
        "this.text(t.x,t.y-24,`+HEAL`,`#ff8a8a`,12,.85)",
        "panic hp quaff",
    )
    js = replace_once(
        js,
        "t.mpPool+=t.maxMana*n.power,t.mpRate=Math.max(t.mpRate,t.mpPool/2),this.text(t.x,t.y-24,`Glug.`,`#7d8cff`,10,.7)",
        "t.mpPool+=t.maxMana*n.power,t.mpRate=Math.max(t.mpRate,t.mpPool/1.2),"
        "this.text(t.x,t.y-24,`+MANA`,`#9ab0ff`,12,.85)",
        "panic mp quaff",
    )

    # Soft-start nurseries — first minutes teach smash-gen fantasy
    js = replace_once(
        js,
        "cd:q(.3,1.2),flash:0,dead:!1,t:Math.random()*10",
        "cd:q(2.6,4),flash:0,dead:!1,t:Math.random()*10",
        "gen soft start cd",
    )
    js = replace_once(
        js,
        "o.wave<=0&&(o.wave=2+o.tier+Math.floor(n/3),o.waves=(o.waves??0)+1)",
        "o.wave<=0&&(o.wave=(n<=1?1:2)+o.tier+Math.floor(n/3),o.waves=(o.waves??0)+1)",
        "gen early wave size",
    )
    js = replace_once(
        js,
        "o.cd=o.wave>0?q(.7,1.1):Math.max(3.5,6-n*.3-o.tier*.5)*q(.85,1.15)",
        "o.cd=o.wave>0?q(.7,1.1):Math.max(n<=1?4.8:3.8,6.5-n*.25-o.tier*.45)*q(.85,1.15)",
        "gen rest cd",
    )

    # Room-clear visual beat (was voice-only)
    js = replace_once(
        js,
        "this.vNear>=6&&s===0&&this.hv(`clear`),this.vNear=s===0?0:Math.max(this.vNear,s)",
        "this.vNear>=6&&s===0&&(this.hv(`clear`),this.callout(`CLEARED`,`loot · smash nurseries`,`#9be36b`),"
        "this.shake=Math.max(this.shake,4)),this.vNear=s===0?0:Math.max(this.vNear,s)",
        "clear callout",
    )

    # Faster death → rise (Gauntlet coin-up rhythm)
    js = replace_once(
        js,
        "this.phase===`dying`&&this.phaseT>2",
        "this.phase===`dying`&&this.phaseT>1.15",
        "dying duration",
    )
    js = replace_once(
        js,
        "e.inv=2.5,this.curseT=0",
        "e.inv=3.2,this.curseT=0",
        "respawn inv",
    )
    js = replace_once(
        js,
        "children:[`Rise at `,e.waypoints[e.lastWp]?.name??`the last waypoint`,` (Enter)`]",
        "children:[`RISE · reclaim `,e.waypoints[e.lastWp]?.name??`waypoint`,` (Enter)`]",
        "rise cta",
    )

    # Snappier crystal dump + drip heal so dump isn't a suicide commit
    js = replace_once(
        js,
        "magic:{dur:1.1,a0:.42,a1:.43,reach:0,arc:0,dmg:0,kb:0,lunge:0,move:0}",
        "magic:{dur:.7,a0:.16,a1:.2,reach:0,arc:0,dmg:0,kb:0,lunge:0,move:0}",
        "magic windup",
    )
    js = replace_once(
        js,
        "e.pots=0,this.magicFx.push({x:e.x,y:e.y,t:0,pots:r,style:e.classId}),this.say(`${n.magicName}! ${ao(fo)} ×${r}`),this.shake=18,this.flash=.45;let i=5+r*4",
        "e.pots=0,e.hp=Math.min(e.maxHp,e.hp+e.maxHp*(.03+.015*r)),e.inv=Math.max(e.inv,.35),"
        "this.magicFx.push({x:e.x,y:e.y,t:0,pots:r,style:e.classId}),this.say(`${n.magicName}! ${ao(fo)} ×${r}`),"
        "this.shake=18,this.flash=.45;let i=5+r*3.6",
        "magic dump heal",
    )

    # Floor-0 coach + slightly longer entry inv on D1
    js = replace_once(
        js,
        "this.banner={title:`${n.name} · Level ${this.level.index+1}`,line:`${this.level.name} — ${this.level.line}`,t:0},this.say(`${n.name} enters. ${n.flavor}`)",
        "this.banner={title:`${n.name} · Level ${this.level.index+1}`,"
        "line:this.level.index===0?`Hunger drains · eat meat · smash nurseries · Y drink · E/✦ dump crystals`:"
        "`${this.level.name} — ${this.level.line}`,t:0},this.say(`${n.name} enters. ${n.flavor}`)",
        "floor0 coach",
    )
    js = replace_once(
        js,
        "n.inv=1,n.keys=0;for(let e of t.gens)",
        "n.inv=this.level.index<=0?2.2:1.35,n.keys=0;for(let e of t.gens)",
        "entry inv",
    )

    # Empty belt tip points at crystals when you have them
    js = replace_once(
        js,
        "return this.text(this.hero.x,this.hero.y-22,e===`hp`?`I need healing potions.`:`I need mana. Or a nap.`,`#9a948a`,11,1),!1",
        "return this.text(this.hero.x,this.hero.y-22,e===`hp`?(this.hero.pots>0?`Dump crystals (E / ✦)!`:`I need healing potions.`):"
        "`I need mana. Or a nap.`,`#9a948a`,11,1),!1",
        "crystal tip",
    )

    if "build-tag" in js:
        js = (
            js.replace("r32g", BUILD_ID, 1)
            .replace("r33p", BUILD_ID, 1)
            .replace("r34a", BUILD_ID, 1)
            .replace("r35g", BUILD_ID, 1)
            .replace("r35f", BUILD_ID, 1)
            .replace("r36i", BUILD_ID, 1)
        )

    out_css = css + "\n\n/* === r34/r35/r37 flesh & thunder === */\n" + overlay
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
    <meta name="description" content="Dungeons &amp; Dismemberment: private adult Gauntlet crawl — flesh, thunder, blood momentum." />
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
const CACHE = 'dd-{BUILD_ID}-thunder';
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
        "description": "Private adult Gauntlet crawl — flesh, thunder, blood momentum.",
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

Playable GitHub Pages build of an adult Gauntlet-style dungeon crawler (**r37 coin-up crawl**).

- **Play:** open this branch / Pages site (`?desktop=1` on desktop)
- **Edit:** see [`src/README.md`](src/README.md) — patches + overlays are the source of truth
- **Build:** `python3 src/patches/build.py`

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
""",
        encoding="utf-8",
    )

    (SRC / "README.md").write_text(
        """# Editable source for Dungeons & Dismemberment

This repo ships a Vite-built game on `gh-pages`. The original app source is not in git; the playable core lives in `src/base-bundle.js` (snapshot of the last known-good r32 build).

**Edit here, not the minified file by hand:**

| Path | Purpose |
| --- | --- |
| `src/base-bundle.js` / `src/base-bundle.css` | Frozen game core (r32) |
| `src/patches/build.py` | Applies r33–r37 patches |
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
""",
        encoding="utf-8",
    )

    # Sanity: required r34/r35/r36/r37 markers must exist in output
    checks = [
        "BLOOD MOMENTUM",
        "NURSERY SILENCED",
        "blood-hot",
        "low-hp",
        "crowded",
        "killStreak>=2",
        "grunt:{hp:6,speed:66,dmg:15",
        "(1+o*.055)*1.5",
        "o!==`dot`&&o!==`aura`&&c>=1&&this.text",
        "vol={master:.9,music:.32,sfx:1}",
        "speed:144,melee:1.2,reach:4,pots:1",
        "i.roll.t<.36",
        "sc.l1.reach+i.reachAdd+72)",
        "onPointerDown:z,onClick:z",
        "le=ae===`on`||ae===`auto`&&ie",
        "_crowd=_en>=12",
        "Click here or press Enter",
        "Tab map · I inv · C char",
        # r36 integrity
        "!(n.inv>0||n.roll&&n.roll.t<.36)",
        "!(t.inv>0||t.roll&&t.roll.t<.36)&&(t.hp-=(26+n*2)*e",
        "t.roll.t<.36)&&(t.hp-=3.5*e",
        "phase===`play`&&!this.god&&!(r.inv>0||r.roll&&r.roll.t<.36)",
        ")<50&&!(t.inv>0||t.roll&&t.roll.t<.36)&&",
        "(e.mods().dmgTakenMul||1)",
        # r37 coin-up
        "M:`magic`",
        "[`M`,`✦`,null]",
        "M:{x:s-Math.round(i*.95),y:c-Math.round(i*.22),d:o}",
        "hpPool/1.2",
        "cd:q(2.6,4)",
        "callout(`CLEARED`",
        "phaseT>1.15",
        "e.inv=3.2",
        "magic:{dur:.7,a0:.16,a1:.2",
        "Dump crystals (E / ✦)!",
        "smash nurseries · Y drink",
    ]
    for c in checks:
        if c not in out_js:
            raise SystemExit(f"post-build check failed: missing {c!r}")
    if "28eachAdd" in out_js or "r+28each" in out_js:
        raise SystemExit("post-build check failed: mangled assist range")
    if "roll.t<.28" in out_js:
        raise SystemExit("post-build check failed: leftover roll.t<.28")

    print(f"built assets/{js_name}")
    print(f"built assets/{css_name}")
    print("updated index.html sw.js manifest.webmanifest README.md")
    print(f"build-id {BUILD_ID} ok ({len(checks)} checks)")


if __name__ == "__main__":
    main()
