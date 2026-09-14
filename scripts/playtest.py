"""Headless GH-9: win-all-dead, ease dial, four strategies, Flame >= Rockets."""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")

KIND_CH = {
    "s": "snout", "r": "snout", "p": "pebble", "l": "rider", "c": "rider", "b": "biter",
    "d": "dart", "k": "stalker", "a": "barrel", "y": "minnow", "f": "foam",
    "e": "eddy", "n": "monk", "w": "maw", "m": "maw",
}


def _num_list(name: str) -> list[int]:
    m = re.search(rf"const {name} = \[([^\]]+)\]", HTML)
    assert m, name
    return [int(x.strip()) for x in m.group(1).split(",") if x.strip()]


def _js_objs(name: str) -> list[dict]:
    m = re.search(rf"const {name} = \[([\s\S]*?)\];", HTML)
    assert m, name
    body = m.group(1)
    out = []
    for block in re.finditer(r"\{([^}]+)\}", body):
        d = {}
        chunk = block.group(1)
        for km in re.finditer(r"(\w+):\s*(\"[^\"]+\"|-?\d+(?:\.\d+)?)", chunk):
            k, v = km.group(1), km.group(2)
            d[k] = v.strip('"') if v.startswith('"') else float(v) if "." in v else int(v)
        if d:
            out.append(d)
    return out


def _kinds() -> dict:
    m = re.search(r"const KINDS = \{([\s\S]*?)\};", HTML)
    assert m
    kinds = {}
    for block in re.finditer(r"(\w+):\s*\{([^}]+)\}", m.group(1)):
        d = {"name": block.group(1)}
        for km in re.finditer(r"(\w+):\s*(\"[^\"]+\"|-?\d+(?:\.\d+)?|true|false)", block.group(2)):
            k, v = km.group(1), km.group(2)
            if v in ("true", "false"):
                d[k] = v == "true"
            elif v.startswith('"'):
                d[k] = v.strip('"')
            else:
                d[k] = float(v) if "." in v else int(v)
        kinds[block.group(1)] = d
    return kinds


def _levels() -> list[dict]:
    m = re.search(r"const LEVELS = \[([\s\S]*?)\];", HTML)
    assert m
    levels = []
    for lm in re.finditer(
        r'\{ name: "([^"]+)", wood: (\d+), dam: (\d+), waves: \[([\s\S]*?)\]\}',
        m.group(1),
    ):
        waves = []
        for wm in re.finditer(
            r'wv\(([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*"([^"]+)"\)',
            lm.group(4),
        ):
            waves.append({
                "interval": float(wm.group(1)),
                "hpMul": float(wm.group(2)),
                "spdMul": float(wm.group(3)),
                "seq": wm.group(4),
            })
        levels.append({
            "name": lm.group(1),
            "wood": int(lm.group(2)),
            "dam": int(lm.group(3)),
            "waves": waves,
        })
    return levels


def _path_n() -> list[list[float]]:
    m = re.search(r"const PATH_N = \[([\s\S]*?)\];", HTML)
    assert m
    pts = [[float(a), float(b)] for a, b in re.findall(r"\[([\d.]+),\s*([\d.]+)\]", m.group(1))]
    assert len(pts) >= 5
    return pts


START_WOOD = _num_list("START_WOOD")
GUNS = _js_objs("GUNS")
DAM_TIERS = _js_objs("DAM_TIERS")
KINDS = _kinds()
LEVELS = _levels()
PATH_N = _path_n()
W, H = 390.0, 640.0
COST_REPAIR, REPAIR_HP = 28, 22
COST_LASER, COST_HOT, COST_YELL = 100, 150, 60


def build_path():
    dam_h = max(70, round(H * 0.16))
    dam_w = min(W * 0.88, W - 16)
    dam_x = (W - dam_w) / 2
    dam_y = H - dam_h - 6
    frame_t = round(H * 0.08)
    mouth = dam_y + 4
    pts = [(8 + p[0] * (W - 16), frame_t + p[1] * (mouth - frame_t)) for p in PATH_N]
    pts[-1] = (pts[-1][0], mouth)
    cum, plen = [0.0], 0.0
    for i in range(1, len(pts)):
        plen += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        cum.append(plen)
    pads = [(dam_x + dam_w * 0.28, dam_y + 8), (dam_x + dam_w * 0.72, dam_y + 8)]
    laser_o = (W * 0.5, dam_y)
    return pts, cum, max(1.0, plen), pads, laser_o, dam_y


def point_at(pts, cum, plen, dist):
    d = max(0.0, min(plen, dist))
    for i in range(1, len(cum)):
        if d <= cum[i]:
            span = cum[i] - cum[i - 1] or 1.0
            t = (d - cum[i - 1]) / span
            return pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t
    return pts[-1]


def first_in_range(enemies, pts, cum, plen, x, y, rng):
    best, best_dist, best_pct = None, 1e9, 2.0
    for e in enemies:
        if e["hp"] <= 0 or e.get("ally"):
            continue
        if e.get("stealth") and e["dist"] < plen * 0.45:
            continue
        px, py = point_at(pts, cum, plen, e["dist"])
        if math.hypot(px - x, py - y) > rng + e["r"]:
            continue
        pct = e["hp"] / e["max"] if e["max"] else 1
        if e["dist"] < best_dist - 1 or (abs(e["dist"] - best_dist) <= 1 and pct < best_pct):
            best, best_dist, best_pct = e, e["dist"], pct
    return best


def spawn_one(ch, wave, hp_mul, spd_mul, extra_dist=0.0):
    kind = KIND_CH.get(ch, "snout")
    k = KINDS[kind]
    n = 3 if kind == "foam" else 1
    out = []
    for i in range(n):
        out.append({
            "kind": kind,
            "hp": k["hp"] * hp_mul, "max": k["hp"] * hp_mul,
            "spd": k["spd"] * spd_mul, "wood": k["wood"], "leak": k["leak"],
            "r": k["r"], "armor": k.get("armor") or 0,
            "dist": extra_dist - i * 12, "stealth": bool(k.get("stealth")),
            "split": bool(k.get("split")), "aura": bool(k.get("aura")),
            "boss": bool(k.get("boss")), "spit": bool(k.get("spit")),
            "spitT": 1.2, "windT": 1.15 if k.get("boss") else 0.0,
            "windMid": False, "ally": False,
        })
    return out


class Run:
    def __init__(self, level_i, strat):
        self.li = level_i
        self.strat = strat
        self.level = LEVELS[level_i]
        self.pts, self.cum, self.plen, self.pads, self.laser_o, self.dam_y = build_path()
        self.wood = START_WOOD[level_i] if level_i < len(START_WOOD) else self.level["wood"]
        self.tlv = 0
        self.dam_lv = 0
        self.dam_max = DAM_TIERS[0]["hp"]
        self.dam_hp = self.dam_max
        self.laser = False
        self.hot = level_i >= 14
        self.laser_cd = 0.0
        self.laser_fire = 0.0
        self.yell_t = 0.0
        self.leaks = 0
        self.flame_bought_before_l6 = False
        self.towers = [{"cd": 0.0}, {"cd": 0.0}]

    def gun(self):
        return GUNS[max(0, min(len(GUNS) - 1, self.tlv))]

    def leak_mul(self):
        return DAM_TIERS[self.dam_lv].get("leakMul", 1)

    def apply_dam(self, tier):
        if tier <= self.dam_lv:
            return
        old = self.dam_max
        self.dam_lv = tier
        self.dam_max = DAM_TIERS[self.dam_lv]["hp"]
        self.dam_hp = min(self.dam_max, self.dam_hp + (self.dam_max - old))

    def buy_gun(self):
        if self.tlv >= len(GUNS) - 1:
            return False
        cost = GUNS[self.tlv + 1]["cost"]
        if self.wood < cost:
            return False
        self.wood -= cost
        self.tlv += 1
        if self.tlv >= 1:
            self.apply_dam(1)
        if self.tlv >= 2:
            self.apply_dam(2)
        if self.tlv >= 3 and self.li < 5:
            self.flame_bought_before_l6 = True
        return True

    def buy_dam(self):
        if self.dam_lv >= len(DAM_TIERS) - 1:
            return False
        cost = DAM_TIERS[self.dam_lv + 1]["cost"]
        if self.wood < cost:
            return False
        self.wood -= cost
        self.apply_dam(self.dam_lv + 1)
        return True

    def repair(self):
        if self.dam_hp >= self.dam_max or self.wood < COST_REPAIR:
            return False
        self.wood -= COST_REPAIR
        self.dam_hp = min(self.dam_max, self.dam_hp + REPAIR_HP)
        return True

    def next_gun_cost(self):
        if self.tlv >= len(GUNS) - 1:
            return 0
        return GUNS[self.tlv + 1]["cost"]

    def try_yell(self, wave_i):
        if self.li < 5 or self.yell_t > 0 or wave_i < 2 or self.wood < COST_YELL:
            return
        nxt = self.next_gun_cost()
        if nxt and self.wood < nxt + COST_YELL:
            return
        self.wood -= COST_YELL
        self.yell_t = 4.0

    def try_buys(self, wave_i):
        s = self.strat
        if s == "dam_first":
            if self.tlv == 0 and self.dam_lv < 1 and self.wood >= 120:
                self.buy_dam()
            if self.tlv == 0 and self.wood >= 90:
                self.buy_gun()
            elif self.tlv == 1 and self.wood >= 140:
                self.buy_gun()
            elif self.tlv == 2 and self.li >= 15 and self.wood >= 200:
                self.buy_gun()
            elif self.dam_lv < 2 and self.wood >= 180:
                self.buy_dam()
            if self.dam_hp < self.dam_max * (0.35 if self.tlv == 0 else 0.72):
                self.repair()
        elif s == "guns_first":
            while self.tlv < 3:
                if self.tlv >= 2 and self.li < 8:
                    break
                if self.wood < self.next_gun_cost():
                    break
                self.buy_gun()
            if self.dam_hp < self.dam_max * 0.45:
                self.repair()
            self.try_yell(wave_i)
        elif s == "balanced":
            if self.tlv == 0 and self.wood >= 90:
                self.buy_gun()
            elif self.dam_lv < 1 and self.wood >= 120:
                self.buy_dam()
            elif self.tlv == 1 and self.wood >= 140:
                self.buy_gun()
            elif self.dam_lv < 2 and self.wood >= 180:
                self.buy_dam()
            elif self.tlv == 2 and self.li >= 15 and self.wood >= 200:
                self.buy_gun()
            if self.dam_hp < self.dam_max * 0.55:
                self.repair()
            self.try_yell(wave_i)
        elif s == "bober_assist":
            if self.tlv == 0 and self.wood >= 90:
                self.buy_gun()
            cost_l = COST_HOT if self.hot else COST_LASER
            if not self.laser and (self.tlv >= 1 or self.li >= 8) and self.wood >= cost_l:
                self.wood -= cost_l
                self.laser = True
            elif self.tlv == 1 and self.wood >= 140:
                self.buy_gun()
            elif self.tlv == 2 and self.li >= 14 and self.wood >= 200:
                self.buy_gun()
            if self.dam_hp < self.dam_max * 0.5:
                self.repair()
            self.try_yell(wave_i)

    def simulate(self):
        dt = 1 / 30
        for wi, wave in enumerate(self.level["waves"], 1):
            self.hp_mul = wave["hpMul"]
            self.spd_mul = wave["spdMul"]
            self.try_buys(wi)
            q = list(wave["seq"])
            spawn_t = 0.25
            enemies, shots = [], []
            laser_hold = True
            t = 0.0
            while q or enemies or shots:
                t += dt
                if t > 240:
                    return {"win": False, "wave": wi, "dam": max(0, self.dam_hp), "leaks": self.leaks, "tlv": self.tlv, "timeout": True}
                if self.yell_t > 0:
                    self.yell_t = max(0.0, self.yell_t - dt)
                if self.laser_cd > 0:
                    self.laser_cd = max(0.0, self.laser_cd - dt)
                spawn_t -= dt
                if spawn_t <= 0 and q:
                    enemies.extend(spawn_one(q.pop(0), wave, wave["hpMul"], wave["spdMul"]))
                    spawn_t = wave["interval"]
                    self.try_buys(wi)
                choir = 1.08 if any(e["kind"] == "foam" for e in enemies) else 1.0
                still = []
                for e in enemies:
                    if e["boss"] and not e["windMid"]:
                        ex, ey = point_at(self.pts, self.cum, self.plen, e["dist"])
                        for pad in self.pads:
                            if math.hypot(ex - pad[0], ey - pad[1]) <= 175 + e["r"]:
                                e["windMid"] = True
                                e["windT"] = max(e["windT"], 2.6)
                                break
                    if e["windT"] > 0:
                        e["windT"] -= dt
                    else:
                        aura = choir
                        if not e.get("aura"):
                            ex, ey = point_at(self.pts, self.cum, self.plen, e["dist"])
                            for m in enemies:
                                if not m.get("aura"):
                                    continue
                                mx, my = point_at(self.pts, self.cum, self.plen, m["dist"])
                                if math.hypot(ex - mx, ey - my) < 90:
                                    aura = max(aura, 1.12)
                        e["dist"] += e["spd"] * aura * dt
                    if e.get("spit") and self.plen * 0.45 < e["dist"] < self.plen * 0.92:
                        e["spitT"] -= dt
                        if e["spitT"] <= 0:
                            e["spitT"] = 1.8
                            self.dam_hp -= 6 * self.leak_mul()
                            if self.dam_hp <= 0:
                                return {"win": False, "wave": wi, "dam": 0, "leaks": self.leaks, "tlv": self.tlv}
                    if e["dist"] >= self.plen:
                        self.dam_hp -= e["leak"] * self.leak_mul()
                        self.leaks += 1
                        if self.dam_hp <= 0:
                            return {"win": False, "wave": wi, "dam": 0, "leaks": self.leaks, "tlv": self.tlv}
                    else:
                        still.append(e)
                enemies = still
                g = self.gun()
                rate = 1.15 if self.yell_t > 0 else 1.0
                for i, tw in enumerate(self.towers):
                    tw["cd"] -= dt
                    px, py = self.pads[i]
                    tgt = first_in_range(enemies, self.pts, self.cum, self.plen, px, py, g["range"])
                    if tgt is not None and tw["cd"] <= 0:
                        tw["cd"] = g["cd"] / rate
                        if g.get("cone"):
                            lane = point_at(self.pts, self.cum, self.plen, self.plen * 0.52)
                            ang = math.atan2(lane[1] - py, lane[0] - px)
                            for e in list(enemies):
                                ex, ey = point_at(self.pts, self.cum, self.plen, e["dist"])
                                dist = math.hypot(ex - px, ey - py)
                                dang = math.atan2(ey - py, ex - px) - ang
                                while dang > math.pi:
                                    dang -= 2 * math.pi
                                while dang < -math.pi:
                                    dang += 2 * math.pi
                                stealthed = e.get("stealth") and e["dist"] < self.plen * 0.45
                                if not stealthed and dist <= g["range"] + e["r"] and abs(dang) <= g["cone"]:
                                    self.hurt(e, g["dmg"], enemies)
                        else:
                            tx, ty = point_at(self.pts, self.cum, self.plen, tgt["dist"])
                            shots.append({
                                "x": px, "y": py, "tx": tx, "ty": ty, "target": tgt,
                                "spd": max(1, g.get("pspd") or 800), "dmg": g["dmg"],
                                "splash": g.get("splash") or 0,
                            })
                live = []
                for sh in shots:
                    if sh["target"] in enemies:
                        sh["tx"], sh["ty"] = point_at(self.pts, self.cum, self.plen, sh["target"]["dist"])
                    dx, dy = sh["tx"] - sh["x"], sh["ty"] - sh["y"]
                    dist = math.hypot(dx, dy) or 1.0
                    step = sh["spd"] * dt
                    if step >= dist:
                        if sh["splash"] > 0:
                            for e in list(enemies):
                                x, y = point_at(self.pts, self.cum, self.plen, e["dist"])
                                if math.hypot(x - sh["tx"], y - sh["ty"]) <= sh["splash"] + e["r"]:
                                    self.hurt(e, sh["dmg"], enemies)
                        elif sh["target"] in enemies:
                            self.hurt(sh["target"], sh["dmg"], enemies)
                    else:
                        sh["x"] += dx / dist * step
                        sh["y"] += dy / dist * step
                        live.append(sh)
                shots = live
                if self.laser and laser_hold and self.laser_cd <= 0:
                    lt = first_in_range(enemies, self.pts, self.cum, self.plen, self.laser_o[0], self.laser_o[1], 120)
                    if lt:
                        prev = self.laser_fire
                        self.laser_fire += dt
                        if math.floor(self.laser_fire / 0.18) > math.floor(prev / 0.18):
                            self.hurt(lt, 12 if self.hot else 8, enemies)
                        if self.laser_fire >= 1.0:
                            self.laser_cd = 1.6 if self.hot else 2.0
                            self.laser_fire = 0.0
                    else:
                        self.laser_fire = 0.0
                enemies = [e for e in enemies if e["hp"] > 0]
                self.try_buys(wi)
        pct = self.dam_hp / self.dam_max if self.dam_max else 0
        stars = 3 if pct >= 0.7 else 2 if pct >= 0.4 else 1
        return {
            "win": True, "wave": len(self.level["waves"]), "dam": self.dam_hp,
            "dam_max": self.dam_max, "leaks": self.leaks, "tlv": self.tlv,
            "dam_lv": self.dam_lv, "stars": stars, "laser": self.laser,
            "flame_early": self.flame_bought_before_l6,
        }

    def hurt(self, e, raw, enemies):
        if e not in enemies or e["hp"] <= 0:
            return
        e["hp"] -= raw * (1 - e["armor"])
        if e["hp"] <= 0:
            self.wood += e["wood"]
            if e.get("split"):
                enemies.extend(spawn_one("s", None, self.hp_mul, self.spd_mul, e["dist"] - 8))
            enemies.remove(e)


def kill_gold(level) -> int:
    total = 0
    for w in level["waves"]:
        for ch in w["seq"]:
            kind = KIND_CH.get(ch, "snout")
            n = 3 if kind == "foam" else 1
            total += KINDS[kind]["wood"] * n
    return total


def next_rung(start_wood: int) -> int:
    if start_wood < 90:
        return 90
    if start_wood < 90 + 140:
        return 140
    return 200


def main():
    assert len(LEVELS) == 20, len(LEVELS)
    assert START_WOOD == [200, 190, 180, 170, 160, 150, 145, 140, 135, 130, 140, 135, 130, 125, 120, 130, 125, 120, 115, 120]
    assert [g["name"] for g in GUNS] == ["Arrows", "Bullets", "Rockets", "Flame"]
    assert GUNS[1]["cost"] == 90 and GUNS[1]["range"] == 145 and GUNS[1]["cd"] == 0.42 and GUNS[1]["dmg"] == 14
    assert GUNS[2]["cost"] == 140 and GUNS[2]["range"] == 155 and GUNS[2]["cd"] == 0.70 and GUNS[2]["dmg"] == 28
    assert GUNS[2].get("splash") == 36
    assert GUNS[3]["cost"] == 200 and GUNS[3]["range"] == 170 and GUNS[3]["cd"] == 0.18 and GUNS[3]["dmg"] == 9
    flame_dps = GUNS[3]["dmg"] / GUNS[3]["cd"]
    rocket_dps = GUNS[2]["dmg"] / GUNS[2]["cd"]
    assert flame_dps > rocket_dps, (flame_dps, rocket_dps)
    assert GUNS[3]["range"] >= GUNS[2]["range"]
    assert DAM_TIERS[0]["hp"] == 100 and DAM_TIERS[1]["hp"] == 140 and DAM_TIERS[2]["hp"] == 200
    assert DAM_TIERS[1]["cost"] == 120 and DAM_TIERS[2]["cost"] == 180
    assert abs(DAM_TIERS[1]["leakMul"] - 0.85) < 1e-6
    assert abs(DAM_TIERS[2]["leakMul"] - 0.70) < 1e-6
    assert KINDS["snout"]["hp"] == 20 and KINDS["maw"]["hp"] == 340
    assert KINDS["barrel"]["armor"] == 0.45
    assert KINDS["snout"]["leak"] == 11
    assert "COST_REPAIR = 28" in HTML and "REPAIR_HP = 22" in HTML
    assert "28 $BOBER" in HTML
    assert "Twin posts on the dam face. Hold the flood." in HTML
    assert "Defend the dam." in HTML
    assert "bober-dam-campaign-v5" in HTML
    assert "canWinLevel" in HTML and "remainingEnemies" in HTML
    assert "Not a third tower" in HTML
    assert "Bolts" not in HTML
    mus_imgs = re.findall(r'img: "(assets/museum/[^"]+)"', HTML)
    assert mus_imgs, "museum thumbs missing"
    assert len(mus_imgs) == len(set(mus_imgs)), mus_imgs
    for p in mus_imgs:
        assert (ROOT / p).is_file(), p
    assert "Never farms Bober" in HTML or "never farms Bober" in HTML.lower()

    pts, cum, plen, pads, laser_o, _ = build_path()
    up = {"hp": 10, "max": 10, "dist": max(0, plen - 90), "r": 10, "stealth": False, "ally": False}
    down = {"hp": 4, "max": 10, "dist": max(0, plen - 25), "r": 10, "stealth": False, "ally": False}
    bober = {"hp": 1, "max": 99, "dist": max(0, plen - 40), "r": 10, "stealth": False, "ally": True}
    pick = first_in_range([down, up, bober], pts, cum, plen, pads[0][0], pads[0][1], 2000)
    assert pick is up, f"must prefer farthest upstream, skip ally Bober; got dist={pick and pick.get('dist')}"
    out_of_range_up = {"hp": 10, "max": 10, "dist": 10, "r": 10, "stealth": False, "ally": False}
    pick2 = first_in_range([out_of_range_up, down], pts, cum, plen, pads[0][0], pads[0][1], 140)
    assert pick2 is down, "must ignore upstream foes outside range"

    strats = ["dam_first", "guns_first", "balanced", "bober_assist"]
    results = {s: [] for s in strats}
    for s in strats:
        for i, L in enumerate(LEVELS):
            r = Run(i, s).simulate()
            results[s].append(r)
            tag = "WIN" if r["win"] else "FAIL"
            print(f"{s:13} L{i+1:02} {L['name']:16} {tag} dam={r['dam']:.0f} tlv={r['tlv']} leaks={r['leaks']}")

    for i, L in enumerate(LEVELS):
        gold = kill_gold(L)
        nxt = 90 if i < 3 else 140 if i < 10 else 200
        ratio = gold / nxt
        print(f"gold L{i+1:02} {gold:4} / rung {nxt} = {ratio:.2f}x")

    l10_wins = [s for s in strats if results[s][9]["win"]]
    assert len(l10_wins) >= 2, f"L10 need >=2 strats, got {l10_wins}"
    for s in strats:
        early = results[s][:8]
        assert any(r["win"] for r in early), f"{s} never cleared early"
        assert not any(r.get("flame_early") for r in results[s]), f"{s} forced Flame by L5"

    end_ok = []
    for s in ("guns_first", "bober_assist"):
        if results[s][19]["win"]:
            end_ok.append(s)
    assert end_ok, "endgame L20 must be winnable by Flame+Steel or Laser+Rockets"

    print("L10 wins:", l10_wins)
    print("L20 wins:", [s for s in strats if results[s][19]["win"]])
    print("Flame DPS", round(flame_dps, 1), ">= Rockets", round(rocket_dps, 1))
    print("OK")


if __name__ == "__main__":
    main()
