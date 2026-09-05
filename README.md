# Bober Dam Defense

Fan game by a holder. Not affiliated with any token, studio, or official Bober project.

**Play online:** https://ccosma1.github.io/bober-dam-defense/

A mobile-first tower defense in **one HTML page**. Hold a wooden dam against five waves.

No install. No wallet. No login. No leaderboard.

## Local

Run `START.bat` or open `index.html` in a browser.

## How to play

1. Tap **HOLD THE DAM**.
2. **START WAVE** / **NEXT WAVE** begins the next wave. **Pause** and **Restart** always work.
3. Tap a **bank pad** to place the selected tower (cost is on the pad). Tap an existing tower to upgrade it.
4. **Stick Thrower** (50 wood) — cheap single-target DPS.
5. **Sap Sprayer** (100 wood) — splash sap that slows a pack.
6. Leaks **flash the dam** and drop HP. Low HP shows cracks.
7. Optional: **Repair Dam** (30 wood) for HP back.
8. Survive **5 waves**. Dam HP 0 is a loss.

Pause, mute, and restart sit in the top-right.

### Enemies

| Unit | Role |
|---|---|
| Twig Rat | Fast, fragile |
| Log Crab | Slow, armored |
| Otter Scout | Fast scout |

Wood drops from kills. Spend it on pads along the river.

## GitHub Pages

Live at **https://ccosma1.github.io/bober-dam-defense/**

Repo: https://github.com/ccosma1/bober-dam-defense

`.nojekyll` is included so GitHub does not run Jekyll on the assets.

## Files

- `index.html` — the whole game (HTML, CSS, canvas JS)
- `assets/splash.jpg` — title art
- `assets/icons/` — original dam-defense mark (not the Yeet slingshot)
- `scripts/make_icon.py` — regenerates the mark

## Note

This is a fan game by a holder. It does not connect to a chain, a wallet, or a score server.
