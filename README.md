# Bober Dam Defense

Fan game by a holder. Not affiliated with any token, studio, or official Bober project.

**Play online:** https://ccosma1.github.io/bober-dam-defense/

Splash, level select, and endcard show a cream line: Also play · [Yeet](https://ccosma1.github.io/bober-yeet/) · [Frost Lodge](https://ccosma1.github.io/bober-frost-lodge/). Hidden during a fight so it does not cover the tower shop. Dam Defense is standalone; other games are not required.

A mobile-first tower defense in **one HTML page**. 20-level campaign. Hold the wooden dam.

No install. No wallet. No login. No leaderboard.

## Local

Run `START.bat` or open `index.html` in a browser.

## How to play

1. Tap **HOLD THE DAM**, then pick a level. Level 1 is unlocked; beat a level to open the next.
2. **START WAVE** / **NEXT WAVE** begins the next wave. **Pause**, **Mute**, and **Restart** always work.
3. Tap a **bank pad** to place the selected tower (cost is on the pad). Tap an existing Stick or Sap to upgrade it (rank 1, then rank 2). Upgrade twice, then tap to evolve.
4. **Stick Thrower** (50 wood) — cheap single-target DPS. Upgrade twice, then **evolve to Cybertruck** (140 wood, unlocks after clearing level 4, max 1).
5. **Sap Sprayer** (70 wood) — splash sap that slows a pack. Upgrade twice, then **evolve to Flame Beaver** (120 wood, unlocks after clearing level 8, max 1).
6. Leaks **flash the dam** and drop HP. Low HP shows cracks.
7. Optional: **Repair Dam** (30 wood) for HP back.
8. Hold the dam. Stars (1–3) come from HP left. Win returns to the map. Lose does not unlock.

Pause, mute, and restart sit in the top-right. Footer is Stick, Sap, Repair, Start Wave.

### Enemies

| Unit | Role |
|---|---|
| Twig Rat | Fast, fragile |
| Log Crab | Slow, armored |
| Otter Scout | Fast scout |

Wood drops from kills. Spend it on pads along the river.

Evolved towers replace the Stick or Sap on that pad. Cybertruck pierces armor (max 1). Flame Beaver is a short cone (max 1). Neither upgrades further. Short skippable cartoon cameos; mute still kills their SFX.

## GitHub Pages

Live at **https://ccosma1.github.io/bober-dam-defense/**

Repo: https://github.com/ccosma1/bober-dam-defense

`.nojekyll` is included so GitHub does not run Jekyll on the assets.

## Files

- `index.html` — the whole game (HTML, CSS, canvas JS)
- `assets/splash.jpg` — title art
- `assets/cameo-*.jpg` — skippable cartoon meme overlays (exact level clears: 2 sink, 4 truck, 7 mars, 8 flame, 10 tunnel, 12 starlink, 15 bot, 18 doge, 20 endgame)
- `assets/history/` — 30s skippable “Bober: A Short History” intro frames
- `assets/sprites/bober-*.png` — Yeet Bober idle/fly/splat for the dam NPC and towers
- `assets/icons/` — original dam-defense mark (not the Yeet slingshot)
- `scripts/make_icon.py` — regenerates the mark

## Note

This is a fan game by a holder. It does not connect to a chain, a wallet, or a score server.
