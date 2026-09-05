# Bober Dam Defense

Fan game by a holder. Not affiliated with any token, studio, or official Bober project.

**Play online:** https://ccosma1.github.io/bober-dam-defense/

A mobile-first tower defense in **one HTML page**. Hold a wooden dam against five waves.

No install. No wallet. No login. No leaderboard.

## Local

Run `START.bat` or open `index.html` in a browser.

## How to play

1. Tap **HOLD THE DAM**.
2. During the short **build** window (and during a wave), tap a **bank pad** to place a tower.
3. **Stick Thrower** (50 wood) — single-target sticks.
4. **Sap Sprayer** (100 wood) — splash sap that slows a pack.
5. Enemies that reach the dam **leak** and chew dam HP.
6. Optional: **Repair Dam** (35 wood) for a little HP back.
7. Survive **5 waves**. Dam HP 0 is a loss.

Mute and restart sit in the top-right.

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
