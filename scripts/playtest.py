"""Headless balance check for Bober Dam Defense (mirrors index.html combat)."""
from __future__ import annotations

import math

KINDS = {
    "r": {"hp": 26, "spd": 96, "wood": 8, "leak": 8, "r": 13, "armor": 0},
    "c": {"hp": 90, "spd": 40, "wood": 18, "leak": 16, "r": 18, "armor": 0.4},
    "o": {"hp": 44, "spd": 112, "wood": 14, "leak": 12, "r": 15, "armor": 0},
}
TOWERS = {
    "stick": {"cost": 50, "range": 138, "cd": 0.58, "dmg": 16, "splash": 0, "slow": 0, "pspd": 440},
    "sap": {"cost": 100, "range": 108, "cd": 1.12, "dmg": 8, "splash": 74, "slow": 2.2, "pspd": 340},
}
WAVES = [
    {"interval": 0.88, "hpMul": 1.00, "spdMul": 1.00, "seq": "rrrrrrrr"},
    {"interval": 0.76, "hpMul": 1.08, "spdMul": 1.04, "seq": "rrcrrcrrc"},
    {"interval": 0.66, "hpMul": 1.18, "spdMul": 1.08, "seq": "rocrorcrocror"},
    {"interval": 0.54, "hpMul": 1.32, "spdMul": 1.12, "seq": "rrocrrcocrrocrocr"},
    {"interval": 0.38, "hpMul": 1.62, "spdMul": 1.16, "seq": "rrococrrococrrooccoorrccro"},
]
PATH_N = [
    [-0.08, 0.13], [0.16, 0.14], [0.38, 0.17], [0.56, 0.25],
    [0.66, 0.36], [0.58, 0.47], [0.40, 0.53], [0.24, 0.60],
    [0.18, 0.70], [0.30, 0.80], [0.50, 0.84], [0.68, 0.78],
    [0.72, 0.68], [0.76, 0.56],
]
PAD_N = [
    [0.433, 0.099], [0.580, 0.220], [0.139, 0.552],
    [0.489, 0.762], [0.560, 0.640],
]
W, H = 390.0, 640.0


def build_path():
    pts = [(x * W, y * H) for x, y in PATH_N]
    cum = [0.0]
    total = 0.0
    for i in range(1, len(pts)):
        total += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        cum.append(total)
    return pts, cum, total


def point_at(pts, cum, plen, dist):
    d = max(0.0, min(plen, dist))
    for i in range(1, len(cum)):
        if d <= cum[i]:
            span = cum[i] - cum[i - 1] or 1.0
            t = (d - cum[i - 1]) / span
            return (
                pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t,
                pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t,
            )
    return pts[-1]


def simulate(plan):
    """plan: list of (pad_index, type) bought as soon as wood allows, in order."""
    pts, cum, plen = build_path()
    pads = [(x * W, y * H) for x, y in PAD_N]
    wood = 100
    dam = 100
    towers = []
    buy_i = 0
    dt = 1 / 30
    leaks = 0
    kills = 0

    def try_buy():
        nonlocal wood, buy_i
        while buy_i < len(plan):
            pad, typ = plan[buy_i]
            cost = TOWERS[typ]["cost"]
            if any(t["pad"] == pad for t in towers):
                buy_i += 1
                continue
            if wood < cost:
                return
            wood -= cost
            towers.append({"pad": pad, "type": typ, "cd": 0.0})
            buy_i += 1

    try_buy()
    for wi, wave in enumerate(WAVES, 1):
        q = list(wave["seq"])
        spawn_t = 0.25
        enemies = []
        shots = []
        while q or enemies or shots:
            spawn_t -= dt
            if spawn_t <= 0 and q:
                ch = q.pop(0)
                k = KINDS[ch]
                enemies.append({
                    "hp": k["hp"] * wave["hpMul"],
                    "max": k["hp"] * wave["hpMul"],
                    "spd": k["spd"] * wave["spdMul"],
                    "wood": k["wood"],
                    "leak": k["leak"],
                    "r": k["r"],
                    "armor": k["armor"],
                    "dist": 0.0,
                    "slow": 0.0,
                })
                spawn_t = wave["interval"]
            for e in enemies:
                if e["slow"] > 0:
                    e["slow"] -= dt
                e["dist"] += e["spd"] * (0.45 if e["slow"] > 0 else 1.0) * dt
            still = []
            for e in enemies:
                if e["dist"] >= plen:
                    dam -= e["leak"]
                    leaks += 1
                    if dam <= 0:
                        return {"win": False, "wave": wi, "dam": 0, "wood": wood, "leaks": leaks, "kills": kills, "towers": len(towers)}
                else:
                    still.append(e)
            enemies = still
            for tw in towers:
                spec = TOWERS[tw["type"]]
                tw["cd"] -= dt
                px, py = pads[tw["pad"]]
                tgt = None
                best = -1
                for e in enemies:
                    x, y = point_at(pts, cum, plen, e["dist"])
                    if math.hypot(x - px, y - py) <= spec["range"] + e["r"] and e["dist"] > best:
                        tgt, best = e, e["dist"]
                if tgt is not None and tw["cd"] <= 0:
                    tw["cd"] = spec["cd"]
                    tx, ty = point_at(pts, cum, plen, tgt["dist"])
                    shots.append({
                        "type": tw["type"], "x": px, "y": py, "tx": tx, "ty": ty,
                        "target": tgt, **{k: spec[k] for k in ("pspd", "dmg", "splash", "slow")},
                    })
            live_shots = []
            for s in shots:
                if s["target"] in enemies:
                    s["tx"], s["ty"] = point_at(pts, cum, plen, s["target"]["dist"])
                dx, dy = s["tx"] - s["x"], s["ty"] - s["y"]
                dist = math.hypot(dx, dy) or 1.0
                step = s["pspd"] * dt
                if step >= dist:
                    if s["splash"] > 0:
                        for e in list(enemies):
                            x, y = point_at(pts, cum, plen, e["dist"])
                            if math.hypot(x - s["tx"], y - s["ty"]) <= s["splash"] + e["r"]:
                                e["slow"] = max(e["slow"], s["slow"])
                                e["hp"] -= s["dmg"] * (1 - e["armor"])
                    elif s["target"] in enemies:
                        s["target"]["hp"] -= s["dmg"] * (1 - s["target"]["armor"])
                    nxt = []
                    for e in enemies:
                        if e["hp"] <= 0:
                            wood += e["wood"]
                            kills += 1
                        else:
                            nxt.append(e)
                    enemies = nxt
                    try_buy()
                else:
                    s["x"] += dx / dist * step
                    s["y"] += dy / dist * step
                    live_shots.append(s)
            shots = live_shots
    return {"win": True, "wave": 5, "dam": dam, "wood": wood, "leaks": leaks, "kills": kills, "towers": len(towers)}


def main():
    none = simulate([])
    assert none["win"] is False, none
    assert none["wave"] <= 2, none

    greedy = simulate([
        (0, "stick"), (1, "stick"), (4, "sap"), (2, "stick"), (3, "sap"),
    ])
    print("no-towers", none)
    print("greedy   ", greedy)
    assert greedy["win"], greedy
    assert greedy["towers"] >= 3, greedy
    print("OK")


if __name__ == "__main__":
    main()
