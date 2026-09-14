"""Headless GH-7: shared guns, separate dam."""
from __future__ import annotations
import math

KINDS = {
    "r": {"hp": 22, "spd": 102, "wood": 6, "leak": 12, "r": 13, "armor": 0},
    "c": {"hp": 92, "spd": 36, "wood": 12, "leak": 22, "r": 20, "armor": 0.35},
    "o": {"hp": 28, "spd": 120, "wood": 7, "leak": 14, "r": 12, "armor": 0},
}
GUNS = [
    {"range": 210, "cd": 0.48, "dmg": 14, "splash": 0, "pspd": 920, "cost": 0},
    {"range": 220, "cd": 0.40, "dmg": 22, "splash": 0, "pspd": 1000, "cost": 80},
    {"range": 230, "cd": 0.68, "dmg": 34, "splash": 56, "pspd": 760, "cost": 150},
    {"range": 190, "cd": 0.16, "dmg": 8, "splash": 0, "pspd": 0, "cost": 220, "cone": 0.7},
]
PATH_N = [[0.50, 0.10], [0.46, 0.22], [0.54, 0.36], [0.47, 0.50], [0.52, 0.64], [0.50, 0.76]]
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
]


def build_path():
    pts = [(8 + p[0] * (W - 16), 50 + p[1] * (H * 0.62)) for p in PATH_N]
    cum, plen = [0.0], 0.0
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


def simulate(level, upgrade=True):
    pts, cum, plen = build_path()
    pads = [(W * 0.28, H * 0.78), (W * 0.72, H * 0.78)]
    wood = level["wood"]
    dam = level["dam"]
    dam_max = dam
    tlv = 0
    dt = 1 / 30
    leaks = 0
    towers = [{"cd": 0.0}, {"cd": 0.0}]

    def gun():
        return GUNS[max(0, min(len(GUNS) - 1, tlv))]

    def try_up():
        nonlocal wood, tlv
        if not upgrade or tlv >= len(GUNS) - 1:
            return
        cost = GUNS[tlv + 1]["cost"]
        if wood >= cost:
            wood -= cost
            tlv += 1

    try_up()
    for wi, wave in enumerate(level["waves"], 1):
        q = list(wave["seq"])
        spawn_t = 0.25
        enemies, shots = [], []
        while q or enemies or shots:
            spawn_t -= dt
            if spawn_t <= 0 and q:
                k = KINDS.get(q.pop(0), KINDS["r"])
                enemies.append({"hp": k["hp"] * wave["hpMul"], "spd": k["spd"] * wave["spdMul"],
                                "wood": k["wood"], "leak": k["leak"], "r": k["r"], "armor": k["armor"],
                                "dist": 0.0})
                spawn_t = wave["interval"]
            for e in enemies:
                e["dist"] += e["spd"] * dt
            still = []
            for e in enemies:
                if e["dist"] >= plen:
                    dam -= e["leak"]
                    leaks += 1
                    if dam <= 0:
                        return {"win": False, "wave": wi, "dam": 0, "dam_max": dam_max, "leaks": leaks, "tlv": tlv}
                else:
                    still.append(e)
            enemies = still
            g = gun()
            for i, tw in enumerate(towers):
                tw["cd"] -= dt
                px, py = pads[i]
                tgt, best = None, -1
                for e in enemies:
                    x, y = point_at(pts, cum, plen, e["dist"])
                    if math.hypot(x - px, y - py) <= g["range"] + e["r"] and e["dist"] > best:
                        tgt, best = e, e["dist"]
                if tgt is not None and tw["cd"] <= 0:
                    tw["cd"] = g["cd"]
                    tx, ty = point_at(pts, cum, plen, tgt["dist"])
                    shots.append({"x": px, "y": py, "tx": tx, "ty": ty, "target": tgt, "spd": max(1, g["pspd"]), "dmg": g["dmg"], "splash": g["splash"]})
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
    return {"win": True, "wave": len(level["waves"]), "dam": dam, "dam_max": dam_max, "leaks": leaks, "tlv": tlv}


def main():
    a = simulate(LEVELS[0], True)
    assert a["win"], a
    print("L1 twin same-fire", a)
    print("OK")


if __name__ == "__main__":
    main()
