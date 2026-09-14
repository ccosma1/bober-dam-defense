# Bober Dam Defense

Fan game by a holder. Not affiliated with any token, studio, or official Bober project.

**Play online:** https://ccosma1.github.io/bober-dam-defense/

Splash shows a hub link: [More games · Green Home Games](https://ccosma1.github.io/green-home-games/). Hidden during a fight so it does not cover the tower shop. Dam Defense is standalone; other games are not required.

A mobile-first tower defense in **one HTML page**. 20-level campaign.

Mission: Twin posts on the dam face. Hold the flood.

Portrait waterfall → irregular river → bottom dam. Two posts share one gun ladder: Arrows → Bullets → Rockets → Flame. Dam Wood → Rock → Steel is a separate $BOBER buy. Repair Bober is the mascot, not a third gun. Currency is $BOBER.

No install. No wallet. No login. No leaderboard.

## Local

Run `START.bat` or open `index.html` in a browser.

## How to play

1. Tap **HOLD THE DAM**, then pick a level. Level 1 is unlocked; beat a level to open the next.
2. **START WAVE** / **NEXT WAVE** begins the next wave. **Pause**, **1x / 2x**, **Mute**, and **Restart** always work.
3. Two posts on the dam. Both auto-fire the **same** munition: Arrows → Bullets → Rockets → Flame. Upgrade guns once; both advance.
4. **Dam Wood → Rock → Steel** is a separate $BOBER buy (HP + leak resist). Both posts at Bullets also grants Rock; both at Rockets also grants Steel.
5. **Repair Dam** (28 $BOBER) heals +22 HP. Dam only. Not a gun.
6. Optional mascot help: **Scout Yell** (clear L5, 60 $BOBER, once/wave +15% fire rate 4s) and **Bober Laser** (clear L8 or both posts Bullets, 100 $BOBER, hold to carve, CD 2.0). Hot Laser from L15. Laser assists; it is not a third post and does not replace gun upgrades.
7. A level clears only when the dam still stands **and every foe is dead**. Remaining count is on the HUD. Stars: 3 if dam ≥70% after that clear, 2 if ≥40%, 1 for a clear. No star if foes remain.

Pause, **1x / 2x**, mute, and restart sit in the top-right. 2× speeds the fight and is saved. Footer is Guns, Dam, Repair, then Yell / Laser.

**Museum** (splash, map, or pause) is play cards: Towers, Foes, Dam. Tap a card for detail. Unlock by playing.

**History** is a chapter list. Play never waits on it.

### Enemies

| Unit | Role |
|---|---|
| Drift Snout | Fast, fragile. L1 |
| Pebble Skip | Faster skip. L3 |
| Log Rider | Slow armor. L4 |
| Oasis Biter | Melee. L5 |
| Current Dart | Fast current. L7 |
| Reed Stalker | Stealthed until mid. L8 |
| Barrel Crab | Heavy armor. L10 |
| Spit Minnow | Spits from mid. L11 |
| Foam Choir | Three voices. L12 |
| Eddy Twin | Dies into two Snouts. L14 |
| Splash Monk | Aura allies. L16 |
| Cataract Maw | L20 boss. Telegraph. Never farms Bober |

$BOBER drops from kills. Spend it on the shared gun ladder, the dam, repair, or mascot help.

## GitHub Pages

Live at **https://ccosma1.github.io/bober-dam-defense/**

Repo: https://github.com/ccosma1/bober-dam-defense

`.nojekyll` is included so GitHub does not run Jekyll on the assets.

## Files

- `index.html` — the whole game (HTML, CSS, canvas JS)
- `assets/splash.jpg` — title art
- `assets/cameo-*.jpg` — skippable cartoon meme overlays
- `assets/history/` — History chapter frames
- `assets/museum/` — foe portraits for Museum cards
- `assets/sprites/bober-*.png` — Yeet Bober idle/fly/splat for the dam NPC and posts
- `assets/icons/` — original dam-defense mark (not the Yeet slingshot)
- `scripts/playtest.py` — headless GH-9 sim (win-all-dead, ease dial, four strategies, Flame ≥ Rockets)
- `scripts/make_icon.py` — regenerates the mark

## Note

This is a fan game by a holder. It does not connect to a chain, a wallet, or a score server.
