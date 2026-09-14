"""Headless campaign for Bober Dam Defense GH-6 (mirrors twin-turret layout)."""
from __future__ import annotations

import math

KINDS = {
    "r": {"hp": 22, "spd": 102, "wood": 6, "leak": 12, "r": 13, "armor": 0},
    "c": {"hp": 92, "spd": 36, "wood": 12, "leak": 22, "r": 20, "armor": 0.35},
    "o": {"hp": 28, "spd": 120, "wood": 7, "leak": 14, "r": 12, "armor": 0},
    "b": {"hp": 48, "spd": 72, "wood": 8, "leak": 18, "r": 16, "armor": 0.08},
    "f": {"hp": 40, "spd": 54, "wood": 9, "leak": 10, "r": 16, "armor": 0},
    "m": {"hp": 380, "spd": 26, "wood": 40, "leak": 36, "r": 28, "armor": 0.22},
}
LEFT = [
    {"range": 168, "cd": 0.50, "dmg": 14, "splash": 0, "slow": 0, "pspd": 920, "cost": 0},
    {"range": 178, "cd": 0.42, "dmg": 22, "splash": 0, "slow": 0, "pspd": 980, "cost": 80},
    {"range": 185, "cd": 0.68, "dmg": 34, "splash": 52, "slow": 0, "pspd": 740, "cost": 140},
    {"range": 148, "cd": 0.18, "dmg": 8, "splash": 0, "slow": 0, "pspd": 0, "cost": 200, "cone": 0.78},
]
RIGHT = [
    {"range": 150, "cd": 0.85, "dmg": 9, "splash": 90, "slow": 1.9, "pspd": 640, "cost": 0},
    {"range": 160, "cd": 0.70, "dmg": 16, "splash": 42, "slow": 1.1, "pspd": 820, "cost": 90},
    {"range": 155, "cd": 0.88, "dmg": 22, "splash": 108, "slow": 2.2, "pspd": 580, "cost": 150},
    {"range": 158, "cd": 0.72, "dmg": 12, "splash": 80, "slow": 1.6, "pspd": 700, "cost": 210},
]
PATH_N = [[0.50, 0.10], [0.50, 0.24], [0.50, 0.40], [0.50, 0.56], [0.50, 0.72]]
W, H = 390.0, 640.0


def wv(interval, hp, spd, seq):
    return {"interval": interval, "hpMul": hp, "spdMul": spd, "seq": seq}


LEVELS = [
    {"name": "Oasis Drip", "wood": 160, "dam": 100, "waves": [
        wv(1.10, 1.00, 1.00, "rrrrrr"), wv(1.00, 1.00, 1.00, "rrrrrrr"), wv(0.92, 1.00, 1.00, "rrrrrrrr")
    ]},
    {"name": "Driftwood", "wood": 150, "dam": 100, "waves": [
        wv(0.95, 1.00, 1.00, "rrrrrrr"), wv(0.88, 1.02, 1.00, "rrcrrrr"), wv(0.80, 1.06, 1.02, "rrcrrcrr")
    ]},
    {"name": "Scout Line", "wood": 140, "dam": 100, "waves": [
        wv(0.88, 1.15, 1.00, "rrrrrrrrr"), wv(0.78, 1.20, 1.02, "rrcrrcrrr"),
        wv(0.70, 1.24, 1.04, "rrocrrocr"), wv(0.64, 1.29, 1.06, "rrocrrocrrr")
    ]},
]


def build_path():
    pts = [(8 + p[0] * (W - 16), 50 + p[1] * (H * 0.62)) for p in PATH_N]
    cum = [0.0]
    plen = 0.0
    for i in range(1, len(pts)):
        plen += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        cum.append(plen)
    return pts, cum, max(1.0, plen)


def point_at(pts, cum, plen, dist):
    d = max(0.0, min(plen, dist))
    for i in range(1, len(cum)):
        if d <= cum[i]:
            span = cum[i] - cum[i - 1] or 1.0
            t = (d - cum[i - 1]) / span
            return pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t
    return pts[-1]


def simulate(level, left=0, right=0, upgrade=True):
    pts, cum, plen = build_path()
    pads = [(W * 0.22, H * 0.72), (W * 0.78, H * 0.72)]
    wood = level["wood"]
    dam_max = level["dam"]
    dam = dam_max
    ll, rr = left, right
    dt = 1 / 30
    leaks = 0
    towers = [{"pad": 0, "cd": 0.0}, {"pad": 1, "cd": 0.0}]

    def spec(side):
        line = LEFT if side == 0 else RIGHT
        lv = ll if side == 0 else rr
        return line[max(0, min(len(line) - 1, lv))]

    def try_up():
        nonlocal wood, ll, rr
        if not upgrade:
            return
        for side in (0, 1):
            line = LEFT if side == 0 else RIGHT
            lv = ll if side == 0 else rr
            if lv >= len(line) - 1:
                continue
            cost = line[lv + 1]["cost"]
            if wood >= cost:
                wood -= cost
                if side == 0:
                    ll += 1
                else:
                    rr += 1

    try_up()
    for wi, wave in enumerate(level["waves"], 1):
        q = list(wave["seq"])
        spawn_t = 0.25
        enemies = []
        shots = []
        while q or enemies or shots:
            spawn_t -= dt
            if spawn_t <= 0 and q:
                ch = q.pop(0)
                k = KINDS.get(ch, KINDS["r"])
                enemies.append({
                    "hp": k["hp"] * wave["hpMul"], "spd": k["spd"] * wave["spdMul"],
                    "wood": k["wood"], "leak": k["leak"], "r": k["r"], "armor": k["armor"],
                    "dist": 0.0, "slow": 0.0,
                })
                spawn_t = wave["interval"]
            for e in enemies:
                if e["slow"] > 0:
                    e["slow"] -= dt
                e["dist"] += e["spd"] * (0.42 if e["slow"] > 0 else 1.0) * dt
            still = []
            for e in enemies:
                if e["dist"] >= plen:
                    dam -= e["leak"]
                    leaks += 1
                    if dam <= 0:
                        return {"win": False, "wave": wi, "dam": 0, "dam_max": dam_max, "leaks": leaks, "ll": ll, "rr": rr}
                else:
                    still.append(e)
            enemies = still
            for i, tw in enumerate(towers):
                s = spec(i)
                tw["cd"] -= dt
                px, py = pads[i]
                tgt = None
                best = -1
                for e in enemies:
                    x, y = point_at(pts, cum, plen, e["dist"])
                    if math.hypot(x - px, y - py) <= s["range"] + e["r"] and e["dist"] > best:
                        tgt, best = e, e["dist"]
                if tgt is not None and tw["cd"] <= 0:
                    tw["cd"] = s["cd"]
                    tx, ty = point_at(pts, cum, plen, tgt["dist"])
                    shots.append({"x": px, "y": py, "tx": tx, "ty": ty, "target": tgt, "spd": max(1, s["pspd"]), "dmg": s["dmg"], "splash": s["splash"], "slow": s["slow"]})
            live = []
            for sh in shots:
                if sh["target"] in enemies:
                    sh["tx"], sh["ty"] = point_at(pts, cum, plen, sh["target"]["dist"])
                dx, dy = sh["tx"] - sh["x"], sh["ty"] - sh["y"]
                dist = math.hypot(dx, dy) or 1.0
                step = sh["spd"] * dt
                if step >= dist:
                    if sh["splash"] > 0:
                        for e in list(enemies):
                            x, y = point_at(pts, cum, plen, e["dist"])
                            if math.hypot(x - sh["tx"], y - sh["ty"]) <= sh["splash"] + e["r"]:
                                e["slow"] = max(e["slow"], sh["slow"])
                                e["hp"] -= sh["dmg"] * (1 - e["armor"])
                    elif sh["target"] in enemies:
                        sh["target"]["hp"] -= sh["dmg"] * (1 - sh["target"]["armor"])
                    nxt = []
                    for e in enemies:
                        if e["hp"] <= 0:
                            wood += e["wood"]
                            try_up()
                        else:
                            nxt.append(e)
                    enemies = nxt
                else:
                    sh["x"] += dx / dist * step
                    sh["y"] += dy / dist * step
                    live.append(sh)
            shots = live
    return {"win": True, "wave": len(level["waves"]), "dam": dam, "dam_max": dam_max, "leaks": leaks, "ll": ll, "rr": rr}


def main():
    print("Lv  name          twin+up                 sap-lead")
    for i, lv in enumerate(LEVELS):
        a = simulate(lv, 0, 0, True)
        b = simulate(lv, 0, 3, False)

        def fmt(x):
            if not x["win"]:
                return "LOSE@w%s" % x["wave"]
            return "win %s/%s leak%s L%s/R%s" % (int(x["dam"]), x["dam_max"], x["leaks"], x["ll"], x["rr"])
        print("%2d %-12s  %-22s  %s" % (i + 1, lv["name"], fmt(a), fmt(b)))
    assert simulate(LEVELS[0], 0, 0, True)["win"]
    print("OK")


if __name__ == "__main__":
    main()
