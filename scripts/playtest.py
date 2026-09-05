"""Headless campaign balance for Bober Dam Defense (mirrors index.html)."""
from __future__ import annotations

import math

KINDS = {
    "r": {"hp": 24, "spd": 92, "wood": 6, "leak": 14, "r": 14, "armor": 0},
    "c": {"hp": 96, "spd": 38, "wood": 12, "leak": 24, "r": 20, "armor": 0.4},
    "o": {"hp": 44, "spd": 110, "wood": 9, "leak": 18, "r": 16, "armor": 0},
}
TOWERS = {
    "stick": {"cost": 50, "range": 150, "cd": 0.38, "dmg": 18, "splash": 0, "slow": 0, "pspd": 820},
    "sap": {"cost": 100, "range": 120, "cd": 0.82, "dmg": 7, "splash": 96, "slow": 2.8, "pspd": 640},
}
PATH_N = [
    [-0.08, 0.13], [0.16, 0.14], [0.38, 0.17], [0.56, 0.25],
    [0.66, 0.36], [0.58, 0.47], [0.40, 0.53], [0.24, 0.60],
    [0.18, 0.70], [0.30, 0.80], [0.50, 0.84], [0.68, 0.78],
    [0.72, 0.68], [0.76, 0.56],
]
PAD_N = [
    [0.28, 0.14], [0.62, 0.12], [0.88, 0.22],
    [0.22, 0.78], [0.55, 0.86],
]
W, H = 390.0, 640.0
GREEDY = [(0, "stick"), (1, "stick"), (4, "sap"), (2, "stick"), (3, "sap")]
TWO = [(0, "stick"), (1, "stick")]


def wv(interval, hp, spd, seq):
    return {"interval": interval, "hpMul": hp, "spdMul": spd, "seq": seq}


LEVELS = [
    {"name": "Trickle", "wood": 120, "dam": 100, "waves": [
        wv(1.10, 1.00, 1.00, "rrrrrr"),
        wv(1.00, 1.00, 1.00, "rrrrrrr"),
        wv(0.92, 1.00, 1.00, "rrrrrrrr"),
    ]},
    {"name": "Driftwood", "wood": 110, "dam": 100, "waves": [
        wv(0.95, 1.00, 1.00, "rrrrrrr"),
        wv(0.88, 1.02, 1.00, "rrcrrrr"),
        wv(0.80, 1.06, 1.02, "rrcrrcrr"),
    ]},
    {"name": "Scout Line", "wood": 100, "dam": 100, "waves": [
        wv(0.92, 1.00, 1.00, "rrrrrrrr"),
        wv(0.82, 1.04, 1.02, "rrcrrcrr"),
        wv(0.74, 1.08, 1.04, "rrocrroc"),
        wv(0.68, 1.12, 1.06, "rrocrrocrr"),
    ]},
    {"name": "Pack Night", "wood": 100, "dam": 100, "waves": [
        wv(0.85, 1.10, 1.06, "rrcrrcrr"),
        wv(0.68, 1.22, 1.10, "rrocrrcocr"),
        wv(0.50, 1.38, 1.16, "rrocrrcocrrocr"),
        wv(0.32, 1.58, 1.24, "rrococrrococrroocoo"),
        wv(0.16, 1.92, 1.40, "rrococrrococrrooccoorrccrrooooo"),
    ]},
    {"name": "Low Timber", "wood": 70, "dam": 100, "waves": [
        wv(0.78, 1.16, 1.10, "rrcrrcrr"),
        wv(0.54, 1.32, 1.16, "rrocrrocrrc"),
        wv(0.36, 1.52, 1.24, "rrocrrcocrrocrro"),
        wv(0.12, 2.05, 1.48, "rrococrrococrrooccoorrccrroooooooo"),
    ]},
    {"name": "Thin Dam", "wood": 100, "dam": 75, "waves": [
        wv(0.78, 1.18, 1.10, "rrcrrcrr"),
        wv(0.54, 1.34, 1.16, "rrocrrocrr"),
        wv(0.36, 1.54, 1.24, "rrocrrcocrrocr"),
        wv(0.22, 1.76, 1.32, "rrococrrococrroocoo"),
        wv(0.13, 2.05, 1.46, "rrooocrrococrrooccoorrccroooooooo"),
    ]},
    {"name": "Crab Walk", "wood": 100, "dam": 100, "waves": [
        wv(0.78, 1.22, 1.02, "rccrrccr"),
        wv(0.58, 1.40, 1.08, "rccrccrccr"),
        wv(0.40, 1.58, 1.12, "crroccrccroc"),
        wv(0.26, 1.78, 1.16, "rccocrccrococr"),
        wv(0.16, 2.05, 1.26, "ccrococrccrroccrocooooo"),
    ]},
    {"name": "Fast Water", "wood": 95, "dam": 100, "waves": [
        wv(0.58, 1.14, 1.26, "rrrrrrrrr"),
        wv(0.44, 1.30, 1.34, "rroorrorro"),
        wv(0.32, 1.48, 1.42, "rrocrroorrro"),
        wv(0.22, 1.68, 1.50, "rroocrroorrroo"),
        wv(0.14, 2.00, 1.62, "rrooocrroorrroorrooooo"),
    ]},
    {"name": "Pocket Wood", "wood": 60, "dam": 100, "waves": [
        wv(0.72, 1.20, 1.12, "rrcrrcrr"),
        wv(0.52, 1.38, 1.18, "rrocrrocrr"),
        wv(0.36, 1.58, 1.24, "rrocrrcocrrocr"),
        wv(0.24, 1.80, 1.32, "rrococrrococrro"),
        wv(0.16, 2.05, 1.40, "rrococrrococrrooccoor"),
    ]},
    {"name": "Night Rush", "wood": 100, "dam": 100, "waves": [
        wv(0.60, 1.28, 1.20, "rrcrrcocr"),
        wv(0.44, 1.46, 1.28, "rrocrrcocrro"),
        wv(0.30, 1.66, 1.36, "rrococrrococrro"),
        wv(0.22, 1.88, 1.44, "rrococrrooccoorr"),
        wv(0.16, 2.12, 1.52, "rrococrrococrrooccoorr"),
        wv(0.12, 2.36, 1.60, "rrococrrococrrooccoorrccrrooc"),
    ]},
    {"name": "Hairline", "wood": 100, "dam": 70, "waves": [
        wv(0.58, 1.32, 1.22, "rrcrrcocr"),
        wv(0.42, 1.50, 1.30, "rrocrrcocrro"),
        wv(0.28, 1.72, 1.38, "rrococrrococrro"),
        wv(0.20, 1.96, 1.46, "rrococrrooccoorr"),
        wv(0.14, 2.22, 1.54, "rrococrrococrrooccoorr"),
        wv(0.11, 2.48, 1.64, "rrococrrococrrooccoorrccrroocco"),
    ]},
    {"name": "Last Stand", "wood": 100, "dam": 80, "waves": [
        wv(0.54, 1.36, 1.24, "rrcrrcocr"),
        wv(0.40, 1.54, 1.32, "rrocrrcocrro"),
        wv(0.28, 1.74, 1.40, "rrococrrococrro"),
        wv(0.20, 1.96, 1.48, "rrococrrooccoorr"),
        wv(0.15, 2.20, 1.56, "rrococrrococrrooccoorr"),
        wv(0.12, 2.44, 1.64, "rrococrrococrrooccoorrccrro"),
        wv(0.10, 2.70, 1.72, "rrococrrococrrooccoorrccrrooccoor"),
    ]},
]


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


def nearest_path(px, py, pts):
    best, nx, ny = 1e9, 0.0, -1.0
    for j in range(len(pts) - 1):
        ax, ay = pts[j]
        bx, by = pts[j + 1]
        vx, vy = bx - ax, by - ay
        l2 = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
        sx, sy = ax + t * vx, ay + t * vy
        d = math.hypot(px - sx, py - sy)
        if d < best:
            best = d
            rx, ry = -vy, vx
            nl = math.hypot(rx, ry) or 1.0
            rx, ry = rx / nl, ry / nl
            if (px - sx) * rx + (py - sy) * ry < 0:
                rx, ry = -rx, -ry
            nx, ny = rx, ry
    return best, nx, ny


def bank_pads(pts):
    river_w = max(40.0, min(W, H) * 0.11)
    min_d = river_w / 2 + 16 + 8
    out = []
    for nx, ny in PAD_N:
        x, y = nx * W, ny * H
        d, bx, by = nearest_path(x, y, pts)
        if d < min_d:
            push = min_d - d + 1
            x += bx * push
            y += by * push
            x = max(28.0, min(W - 28.0, x))
            y = max(28.0, min(H - 28.0, y))
        out.append((x, y))
    return out


def simulate(level, plan, repair_below=None, repair_cost=30, repair_hp=24):
    pts, cum, plen = build_path()
    pads = bank_pads(pts)
    wood = level["wood"]
    dam_max = level["dam"]
    dam = dam_max
    towers = []
    buy_i = 0
    dt = 1 / 30
    leaks = 0
    kills = 0
    repairs = 0

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
    for wi, wave in enumerate(level["waves"], 1):
        q = list(wave["seq"])
        spawn_t = 0.25
        enemies = []
        shots = []
        puddles = []
        while q or enemies or shots:
            spawn_t -= dt
            if spawn_t <= 0 and q:
                ch = q.pop(0)
                k = KINDS[ch]
                enemies.append({
                    "hp": k["hp"] * wave["hpMul"],
                    "spd": k["spd"] * wave["spdMul"],
                    "wood": k["wood"],
                    "leak": k["leak"],
                    "r": k["r"],
                    "armor": k["armor"],
                    "dist": 0.0,
                    "slow": 0.0,
                })
                spawn_t = wave["interval"]
            for u in list(puddles):
                u["t"] -= dt
            puddles = [u for u in puddles if u["t"] > 0]
            for e in enemies:
                if e["slow"] > 0:
                    e["slow"] -= dt
                x, y = point_at(pts, cum, plen, e["dist"])
                for u in puddles:
                    if math.hypot(x - u["x"], y - u["y"]) <= u["r"] + e["r"]:
                        e["slow"] = max(e["slow"], 0.35)
                e["dist"] += e["spd"] * (0.42 if e["slow"] > 0 else 1.0) * dt
            still = []
            for e in enemies:
                if e["dist"] >= plen:
                    dam -= e["leak"]
                    leaks += 1
                    if repair_below is not None and dam < repair_below and wood >= repair_cost and dam > 0:
                        wood -= repair_cost
                        dam = min(dam_max, dam + repair_hp)
                        repairs += 1
                    if dam <= 0:
                        return {"win": False, "wave": wi, "dam": 0, "dam_max": dam_max, "wood": wood, "leaks": leaks, "kills": kills, "towers": len(towers), "repairs": repairs}
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
                    tx, ty = point_at(pts, cum, plen, tgt["dist"] + tgt["spd"] * 0.07)
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
                        puddles.append({"x": s["tx"], "y": s["ty"], "r": s["splash"] * 0.72, "t": 1.35})
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
    return {"win": True, "wave": len(level["waves"]), "dam": dam, "dam_max": dam_max, "wood": wood, "leaks": leaks, "kills": kills, "towers": len(towers), "repairs": repairs}


def pct(r):
    return 0 if r["dam_max"] <= 0 else r["dam"] / r["dam_max"]


def main():
    print("Lv  name          twoSticks              greedy                 greedy+repair")
    rows = []
    for i, lv in enumerate(LEVELS):
        two = simulate(lv, TWO)
        g = simulate(lv, GREEDY)
        r = simulate(lv, GREEDY, repair_below=35)
        rows.append((i, lv, two, g, r))
        def fmt(x):
            if not x["win"]:
                return "LOSE@w%s" % x["wave"]
            return "win %s/%s leak%s" % (int(x["dam"]), x["dam_max"], x["leaks"])
        print("%2d %-12s  %-21s  %-21s  %s" % (i + 1, lv["name"], fmt(two), fmt(g), fmt(r)))

    # 1-3 easy for two sticks
    for i in range(3):
        two = rows[i][2]
        assert two["win"] and pct(two) >= 0.7, (LEVELS[i]["name"], two)

    # 4-6: dam should get hit for a full Stick+Sap line
    for i in range(3, 6):
        g = rows[i][3]
        assert (not g["win"]) or g["leaks"] > 0 or pct(g) < 1.0, (LEVELS[i]["name"], "should chip", g)

    # 10-12 greedy must not finish at full HP; at least one can burst
    late = [rows[i][3] for i in range(9, 12)]
    for g in late:
        assert pct(g) < 0.85, ("late full HP", g)
    assert any(not g["win"] for g in late), "10-12 should be able to burst greedy"
    print("OK")


if __name__ == "__main__":
    main()
