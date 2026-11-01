"""Roborock pose: the robot's position AND heading from its live map.

The built-in roborock.get_vacuum_current_position only returns x/y. The 3D card's drive mode
also needs the heading the robot reports (map vacuum_position.a, degrees, robot map frame),
so it can turn the 3D robot exactly like the real one. Reuses the Roborock integration's own
connection: refreshes its map_content trait (same call the built-in service makes).
"""
from __future__ import annotations

import asyncio
import collections
import json
import math
import logging
import os
import time

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
DOMAIN = "roborock_pose"
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("path", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=200)),
    }
)


def _entity(hass: HomeAssistant, entity_id: str):
    comp = hass.data.get("vacuum")
    ent = comp.get_entity(entity_id) if comp is not None and hasattr(comp, "get_entity") else None
    if ent is None:
        raise HomeAssistantError(f"{entity_id} not found")
    return ent


async def async_setup(hass: HomeAssistant, config) -> bool:
    async def get(call: ServiceCall):
        ent = _entity(hass, call.data["entity_id"])
        try:
            mc = ent.coordinator.properties_api.map_content
        except AttributeError as err:
            raise HomeAssistantError("not a Roborock v1 vacuum") from err
        t0 = time.time()
        try:
            await mc.refresh()
        except Exception as err:  # noqa: BLE001
            raise HomeAssistantError(f"map refresh failed: {err}") from err
        md = mc.map_data
        p = md.vacuum_position if md is not None else None
        if p is None:
            raise HomeAssistantError("position not found")
        out = {"x": p.x, "y": p.y, "a": p.a, "t0": t0, "t1": time.time()}
        n = call.data.get("path", 0)
        if n and md.path is not None:
            pts = md.path.path or []
            if pts and isinstance(pts[0], list):
                pts = [q for seg in pts for q in seg]
            out["path"] = [[q.x, q.y] for q in pts[-n:]]
        return out

    hass.services.async_register(DOMAIN, "get", get, schema=SCHEMA, supports_response=SupportsResponse.ONLY)
    _setup_calib(hass)
    return True


# ---------------------------------------------------------------------------------------------
# Synced BLE calibration recorder (phone taped to the robot).
# One clock on the Pi: every tick (1 s) it refreshes the robot's pose AND snapshots every BLE
# distance sensor in the same tick, each reading with its own last_updated stamp. The 3D card
# then pairs every BLE reading with the robot's position at that exact moment (not a 5 s helper).
# Rows go to /config/roborock_calib/<start_ms>.jsonl (line 1 = header).
# ---------------------------------------------------------------------------------------------
ACTIVE = {"cleaning", "returning", "paused"}
DEF_PREFIX = "sensor.my_phone_ble_unfiltered_distance_to_"
START_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("prefix", default=DEF_PREFIX): cv.string,
        vol.Optional("tick", default=1.0): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=5)),
        vol.Optional("max_minutes", default=180): vol.All(vol.Coerce(int), vol.Range(min=1, max=600)),
        # phone-fell-off watchdog: scanner spots {key: [x_ft, y_ft, z_m]} + robot->tracker transform {M, t}
        vol.Optional("scanners"): dict,
        vol.Optional("xform"): dict,
        vol.Optional("watchdog", default=True): cv.boolean,
        vol.Optional("notify"): cv.string,
        vol.Optional("wd_min"): vol.Coerce(float),
        vol.Optional("wd_strikes"): vol.Coerce(int),
        vol.Optional("wd_window"): vol.Coerce(float),
    }
)

# Watchdog: if the phone falls off, its BLE distances stop tracking where the robot is. Every WD_EVERY s it
# correlates log(reported distance) with log(robot->scanner distance) over the last WD_WINDOW s, per scanner
# with its own mean removed, pooled. Phone on the floor ~0.
# v1.2 (120 s window, 2 checks < 0.08) false-alarmed: with the phone ON the robot, one strip along a wall
# read 0.01-0.09 for ~3 min. Replaying that run:
# 240 s window never went below 0.03. So: 240 s window, pause only after 3 checks in a row <= 0.0, robot spread >= 6 ft.
# Slower to catch a real fall (~5-8 min) but shouldn't stop on its own. Tunable per run via calib_start (wd_*).
WD_WINDOW, WD_EVERY, WD_MIN, WD_STRIKES, WD_SPREAD, WD_SILENT = 240.0, 30.0, 0.0, 3, 6.0, 90.0
PZ_ROBOT_FT = 0.12 / 0.3048
GET_SCHEMA = vol.Schema({vol.Required("id"): cv.string})


class _Recorder:
    def __init__(self, hass: HomeAssistant, entity_id: str, prefix: str, tick: float, max_minutes: int,
                 scanners=None, xform=None, watchdog=True, notify=None, wd=None):
        self.hass, self.entity_id, self.prefix, self.tick, self.max_s = hass, entity_id, prefix, tick, max_minutes * 60
        self.scanners = {k: [float(v[0]), float(v[1]), float(v[2]) / 0.3048] for k, v in (scanners or {}).items()}
        self.xform = xform if xform and "M" in xform and "t" in xform else None
        self.watchdog = bool(watchdog and self.scanners and self.xform)
        self.notify = notify
        wd = wd or {}
        self.wd_min = wd.get("wd_min", WD_MIN); self.wd_strikes_n = wd.get("wd_strikes", WD_STRIKES); self.wd_window = wd.get("wd_window", WD_WINDOW)
        self.wd = collections.deque()  # (t, key, log r, log v, x, y)
        self.wd_seen, self.wd_last, self.wd_strikes, self.wd_heard = {}, 0.0, 0, 0.0
        self.lost = []  # [{t, from}]
        self.last_wd = None
        self.armed_at = time.time()
        self.id = None  # set when the first active tick lands
        self.n = 0
        self.stop = False
        self.task = None

    def _append(self, path: str, lines: list[str]) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write("".join(lines))

    async def run(self) -> None:
        hass = self.hass
        d = hass.config.path("roborock_calib")
        await hass.async_add_executor_job(lambda: os.makedirs(d, exist_ok=True))
        path, idle_since, buf = None, None, []
        try:
            mc = _entity(hass, self.entity_id).coordinator.properties_api.map_content
            while not self.stop and time.time() - self.armed_at < self.max_s:
                tick0 = time.time()
                st = hass.states.get(self.entity_id)
                state = st.state if st else None
                if state in ACTIVE:
                    idle_since = None
                    if path is None:
                        self.id = str(int(tick0 * 1000))
                        path = os.path.join(d, self.id + ".jsonl")
                        buf.append(json.dumps({"v": 1, "entity": self.entity_id, "prefix": self.prefix, "tick": self.tick, "start": round(tick0, 3)}) + "\n")
                    t0 = time.time()
                    pose = None
                    try:
                        await asyncio.wait_for(mc.refresh(), timeout=max(2.0, self.tick * 2))
                        md = mc.map_data
                        p = md.vacuum_position if md is not None else None
                        if p is not None:
                            pose = [p.x, p.y, p.a]
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug("calib tick: map refresh failed: %s", err)
                    t1 = time.time()
                    ble = {}
                    for s in hass.states.async_all("sensor"):  # same tick as the pose
                        if s.entity_id.startswith(self.prefix):
                            try:
                                ble[s.entity_id[len(self.prefix):]] = [round(float(s.state), 3), round(s.last_updated.timestamp(), 3)]
                            except (TypeError, ValueError):
                                pass
                    buf.append(json.dumps({"t0": round(t0, 3), "t1": round(t1, 3), "p": pose, "b": ble, "s": state}, separators=(",", ":")) + "\n")
                    self.n += 1
                    if self.watchdog:
                        ev = await self._watch(t1, pose, ble, state)
                        if ev:
                            buf.append(json.dumps(ev, separators=(",", ":")) + "\n")
                elif path is not None:
                    idle_since = idle_since or tick0
                    if tick0 - idle_since > 20:  # docked / idle for 20 s: run is over
                        break
                if buf and path and (len(buf) >= 5 or state not in ACTIVE):
                    lines, buf = buf, []
                    await hass.async_add_executor_job(self._append, path, lines)
                await asyncio.sleep(max(0.05, self.tick - (time.time() - tick0)))
        except Exception:  # noqa: BLE001
            _LOGGER.exception("roborock_pose calibration recorder stopped")
        finally:
            if buf and path:
                await hass.async_add_executor_job(self._append, path, buf)
            if hass.data.get(DOMAIN, {}).get("rec") is self:
                hass.data[DOMAIN]["rec"] = None
            _LOGGER.info("roborock_pose: calibration recording %s done, %s ticks", self.id, self.n)


    def _ft(self, p):
        M, t = self.xform["M"], self.xform["t"]
        return M[0][0] * p[0] + M[0][1] * p[1] + t[0], M[1][0] * p[0] + M[1][1] * p[1] + t[1]

    async def _watch(self, now, pose, ble, state):
        if state != "cleaning":  # paused / returning: start over when it cleans again
            self.wd.clear(); self.wd_strikes = 0; self.wd_last = now; self.wd_heard = now
            return None
        # Silence is about the phone, not the robot: count any fresh reading, even
        # when a map refresh failed and there is no pose to pair it with.
        if any(now - tb <= 1.5 for _, tb in ble.values()):
            self.wd_heard = now
        if pose:
            x, y = self._ft(pose)
            for k, (v, tb) in ble.items():
                S = self.scanners.get(k)
                if S is None or v <= 0 or self.wd_seen.get(k) == tb or now - tb > 1.5:
                    continue
                self.wd_seen[k] = tb; self.wd_heard = now
                r = math.sqrt((x - S[0]) ** 2 + (y - S[1]) ** 2 + (S[2] - PZ_ROBOT_FT) ** 2)
                self.wd.append((tb, k, math.log10(max(r, 1.0)), math.log10(v), x, y))
        while self.wd and now - self.wd[0][0] > self.wd_window:
            self.wd.popleft()
        if not self.wd_heard:
            self.wd_heard = now
        if now - self.wd_heard > WD_SILENT:  # phone not heard by any scanner at all
            return await self._lost(now, "no scanner has heard the phone for %d s" % (now - self.wd_heard), None)
        if now - self.wd_last < WD_EVERY:
            return None
        self.wd_last = now
        c, info = _wd_corr(self.wd)
        self.last_wd = {"t": round(now, 3), "c": None if c is None else round(c, 3), **info}
        if c is None:  # robot hasn't moved enough / too few readings: can't tell, don't count
            return {"wd": self.last_wd}
        self.wd_strikes = self.wd_strikes + 1 if c <= self.wd_min else 0
        self.last_wd["strikes"] = self.wd_strikes
        if self.wd_strikes >= self.wd_strikes_n:
            return await self._lost(now, "the phone's Bluetooth stopped following the robot (match %.2f)" % c, c)
        return {"wd": self.last_wd}

    async def _lost(self, now, why, c):
        frm = now - self.wd_window - WD_EVERY * (self.wd_strikes_n - 1)
        self.lost.append({"t": now, "from": frm})
        self.wd.clear(); self.wd_strikes = 0; self.wd_last = now; self.wd_heard = now
        _LOGGER.warning("roborock_pose: phone looks like it fell off (%s): pausing the robot", why)
        hass = self.hass
        try:
            await hass.services.async_call("vacuum", "pause", {"entity_id": self.entity_id}, blocking=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("could not pause: %s", err)
        msg = f"Paused the robot: your phone looks like it fell off ({why}). Put it back on and resume, or dock it."
        try:
            await hass.services.async_call("persistent_notification", "create", {"title": "Robot calibration", "message": msg, "notification_id": "roborock_calib_lost"}, blocking=False)
            if self.notify and hass.services.has_service("notify", self.notify):
                await hass.services.async_call("notify", self.notify, {"title": "Robot calibration paused", "message": msg}, blocking=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("could not notify: %s", err)
        return {"ev": "lost", "t": round(now, 3), "from": round(frm, 3), "why": why, "c": c}


def _wd_corr(rows):
    by = {}
    for _, k, lr, lv, x, y in rows:
        by.setdefault(k, []).append((lr, lv))
    xs = [q[4] for q in rows]; ys = [q[5] for q in rows]
    spread = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) if rows else 0.0
    A, B = [], []
    for L in by.values():
        if len(L) < 8:
            continue
        ma = sum(a for a, _ in L) / len(L); mb = sum(b for _, b in L) / len(L)
        A += [a - ma for a, _ in L]; B += [b - mb for _, b in L]
    info = {"n": len(A), "sc": sum(1 for L in by.values() if len(L) >= 8), "spread": round(spread, 1)}
    if len(A) < 60 or info["sc"] < 3 or spread < WD_SPREAD:
        return None, info
    saa = sum(a * a for a in A); sbb = sum(b * b for b in B)
    if saa <= 0 or sbb <= 0:
        return None, info
    return sum(a * b for a, b in zip(A, B)) / math.sqrt(saa * sbb), info


def _list_runs(d: str, live_id):
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d), reverse=True)[:30]:
        if not fn.endswith(".jsonl"):
            continue
        rid, n, end, first = fn[:-6], 0, None, None
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                n += 1
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if "t0" not in r:
                    n -= 1
                    continue
                first = first or r.get("t0")
                end = r.get("t1", end)
        out.append({"id": rid, "start": int(rid), "end": int((end or int(rid) / 1000) * 1000), "n": n, "recording": rid == live_id})
    return out


def _read_run(path: str):
    rows, head = [], None
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if i == 0:
                head = r
            else:
                rows.append(r)
    return head, rows


def _setup_calib(hass: HomeAssistant) -> None:
    hass.data.setdefault(DOMAIN, {"rec": None})
    d = hass.config.path("roborock_calib")

    async def start(call: ServiceCall):
        _entity(hass, call.data["entity_id"])
        cur = hass.data[DOMAIN]["rec"]
        if cur and not cur.stop:
            return {"armed": True, "already": True, "id": cur.id}
        rec = _Recorder(hass, call.data["entity_id"], call.data["prefix"], call.data["tick"], call.data["max_minutes"],
                        call.data.get("scanners"), call.data.get("xform"), call.data.get("watchdog", True), call.data.get("notify"),
                        {k: call.data[k] for k in ("wd_min", "wd_strikes", "wd_window") if k in call.data})
        hass.data[DOMAIN]["rec"] = rec
        rec.task = hass.async_create_background_task(rec.run(), "roborock_pose_calib")
        return {"armed": True, "already": False, "watchdog": rec.watchdog}

    async def stop(call: ServiceCall):
        cur = hass.data[DOMAIN]["rec"]
        if cur:
            cur.stop = True
        return {"stopped": bool(cur), "id": cur.id if cur else None}

    async def runs(call: ServiceCall):
        cur = hass.data[DOMAIN]["rec"]
        out = await hass.async_add_executor_job(_list_runs, d, cur.id if cur else None)
        return {"armed": bool(cur and not cur.stop), "recording": cur.id if cur else None, "ticks": cur.n if cur else 0,
                "watchdog": (cur.last_wd if cur else None), "watch_on": bool(cur and cur.watchdog), "lost": (cur.lost if cur else []), "runs": out}

    async def get_run(call: ServiceCall):
        rid = call.data["id"]
        if not rid.isdigit():
            raise HomeAssistantError("bad id")
        path = os.path.join(d, rid + ".jsonl")
        if not os.path.isfile(path):
            raise HomeAssistantError(f"no recording {rid}")
        head, rows = await hass.async_add_executor_job(_read_run, path)
        return {"id": rid, "head": head, "rows": rows}

    hass.services.async_register(DOMAIN, "calib_start", start, schema=START_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "calib_stop", stop, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, "calib_runs", runs, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "calib_get", get_run, schema=GET_SCHEMA, supports_response=SupportsResponse.ONLY)
