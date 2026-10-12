"""
wattwise.py - CLI monitor for the WattWise township demo.

Reads the same data/township.json the dashboard uses, so the two always
agree. For people who want numbers in a terminal instead of a browser.

Quick one-shot (monitoring, scripts, cron):
    python wattwise.py --once                       # overview at 00:00
    python wattwise.py --tab scheduler --time 09:30 --mode wattwise --once
    python wattwise.py --tab reports --once

Interactive (like the dashboard's command bar):
    python wattwise.py
    > help
    > select mall
    > set time 09:30
    > mode wattwise
    > play            (Ctrl+C stops playback, drops back to prompt)
    > tab scheduler
    > quit

Stdlib only. No numpy/pandas needed.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data" / "township.json"
N = 48

# ---------------------------------------------------------------- colors
# ansi colours, disabled when not a tty or NO_COLOR is set
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

def c(text, code):
    # wrap text in an ansi colour when colours are on
    if not USE_COLOR:
        return str(text)
    return "\033[" + code + "m" + str(text) + "\033[0m"

def green(t):  return c(t, "32")
def red(t):    return c(t, "31")
def amber(t):  return c(t, "33")
def blue(t):   return c(t, "34")
def bold(t):   return c(t, "1")
def dim(t):    return c(t, "90")

def bar(frac, width=20, fill="#"):
    # simple ascii gauge, frac clamped to 0..1
    frac = max(0.0, min(1.0, frac))
    n = int(round(frac * width))
    return "[" + fill * n + "-" * (width - n) + "]"

# ---------------------------------------------------------------- state

class App:
    def __init__(self, data):
        self.T = data
        self.times = data["buildings"]["elmina_tower"]["dumb"]["times"]
        self.towns = list(data["towns"].keys())
        self.town = None          # None = portfolio root (town list)
        self.order = list(data["buildings"].keys())
        self.mode = "dumb"
        self.step = 0
        self.tab = "overview"
        self.selected = None      # building key; None = town/building list
        self.tariff = data.get("tariff", {})
        self.cap_share = self.tariff.get("capacity_share", 0.311)

    # ---- helpers ------------------------------------------------------
    def b(self, key):
        return self.T["buildings"][key]

    def plant_max(self, key):
        # chiller plant capacity: the day's own max draw (precool runs at
        # full plant, so the trace tops out at capacity)
        b = self.b(key)
        return max(max(b["dumb"]["chiller_kw"]),
                   max(b["wattwise"]["chiller_kw"]))

    def trace(self, key=None):
        # the active mode's trace for a building
        k = key or self.selected
        return self.b(k)[self.mode]

    def town_sums(self):
        # per-step township coincident draw for the active mode
        out = []
        for i in range(N):
            out.append(sum(self.b(k)[self.mode]["net_kw"][i] for k in self.order))
        return out

    def clock(self):
        return self.times[self.step]

    # ---- header -------------------------------------------------------
    def header(self):
        T = self.T
        draw = sum(self.trace(k)["net_kw"][self.step] for k in self.order)
        solar = sum(self.trace(k)["solar_kw"][self.step] for k in self.order)
        sums = self.town_sums()
        pk = max(sums)
        pk_t = self.times[sums.index(pk)]
        bill = sum(self.b(k)[("bill_dumb_rm" if self.mode == "dumb"
                              else "bill_wattwise_rm")] for k in self.order)
        save = sum(self.b(k)["bill_dumb_rm"] - self.b(k)["bill_wattwise_rm"]
                   for k in self.order)
        lines = [
            bold("WattWise") + dim(" | " + T.get("day_label", "")),
            "clock " + bold(self.clock()) +
            "  mode " + bold("BASELINE" if self.mode == "dumb" else "WATTWISE") +
            dim("  |  MD rate RM %.2f/kW/mo (capacity %d%% + network %d%%)"
                % (self.tariff.get("md_rate_rm", 97.06),
                   round(self.cap_share * 100),
                   round((1 - self.cap_share) * 100))),
            "draw now %s kW   solar %s kW   coincident peak %s kW @ %s"
            % (bold(f"{draw:,.0f}"), green(f"{solar:,.0f}"),
               bold(f"{pk:,.0f}"), pk_t),
            "MD bill RM %s/mo   wattwise saves RM %s/mo"
            % (f"{bill:,.0f}", green(f"{save:,.0f}")),
            dim("-" * 74),
        ]
        return "\n".join(lines)

    # ---- tabs ---------------------------------------------------------
    def tab_overview(self):
        rows = []
        for tk in self.towns:
            t = self.T["towns"][tk]
            rows.append(bold(t["label"]))
            for k in t["buildings"]:
                b = self.b(k)
                tr = self.trace(k)
                now = tr["net_kw"][self.step]
                max_b = max(max(b["dumb"]["net_kw"]), max(b["wattwise"]["net_kw"]))
                stress = now / max_b if max_b else 0
                badge = (red("NEAR PEAK") if stress > 0.8
                         else amber("MODERATE") if stress > 0.5
                         else green("OK"))
                peak = b["peak_dumb_kw"] if self.mode == "dumb" else b["peak_wattwise_kw"]
                bill = b["bill_dumb_rm"] if self.mode == "dumb" else b["bill_wattwise_rm"]
                shave = ("-%s%%" % b["shave_pct"]) if b["shave_pct"] > 0 else "-"
                rows.append("  %-24s %9s kW %9s kW %7s %11s   %s"
                            % (b["label"], f"{now:,.0f}", f"{peak:,.0f}",
                               shave, "RM %s" % f"{bill:,.0f}", badge))
        head = "%-24s %10s %10s %7s %12s   %s" % (
            "building", "now kW", "peak kW", "shave", "MD/mo", "status")
        out = [bold(head), dim("-" * len(head))] + rows

        # alarm feed, same rules as the dashboard
        alarms = []
        for k in self.order:
            b = self.b(k)
            tr = self.trace(k)
            now = tr["net_kw"][self.step]
            pk = b["peak_dumb_kw"] if self.mode == "dumb" else b["peak_wattwise_kw"]
            if now > 0.95 * pk:
                alarms.append(red("%s  %s at %s kW (within 5%% of peak %s kW)"
                                  % (self.clock(), b["label"],
                                     f"{now:,.0f}", f"{pk:,.0f}")))
            if tr["zone_c"][self.step] > 26.01:
                alarms.append(red("%s  %s zone %.1fC exceeds comfort band"
                                  % (self.clock(), b["label"],
                                     tr["zone_c"][self.step])))
        out.append("")
        out.append(bold("alarm feed"))
        out.extend(alarms if alarms
                   else [dim("%s  no active alarms. all buildings nominal."
                             % self.clock())])

        # plant watchlist: chiller loading right now (strain before breakdown)
        out.append("")
        out.append(bold("plant watchlist (chiller loading now)"))
        for k in self.order:
            tr = self.trace(k)
            cap = self.plant_max(k)
            now = tr["chiller_kw"][self.step]
            pct = 100 * now / cap if cap else 0
            act = tr["action"][self.step]
            col = red if pct > 70 else (amber if pct > 40 else green)
            # full plant is BY DESIGN during precool/soak; the DC's
            # essential cooling runs at max around the clock by design.
            # Flag those as expected instead of crying wolf at the desk.
            if pct > 70 and (act in ("precool", "soak")
                             or act == "essential-cooling"):
                flag = dim("  (expected: %s)" % act)
            elif pct > 70:
                flag = red("  <-- HIGH LOAD")
            else:
                flag = ""
            out.append("%-24s %s %4d%%  (%s / %s kW)%s"
                       % (self.b(k)["label"], col(bar(pct / 100, 20)),
                          pct, f"{now:,.0f}", f"{cap:,.0f}", flag))
        return "\n".join(out)

    def tab_buildings(self):
        if self.town is None:
            return self.town_list()
        if self.selected is None:
            return self.building_list()
        return self.building_detail()

    # ---- town list (portfolio root) ------------------------------------
    def town_list(self):
        lines = [bold("towns"), dim("navigate: town <name|number>, then"
                                    " select a building; back goes up")]
        load_total = 0
        for k in self.order:
            load_total += self.trace(k)["total_kw"][self.step]
        for n, tk in enumerate(self.towns, 1):
            t = self.T["towns"][tk]
            keys = t["buildings"]
            load = sum(self.trace(k)["total_kw"][self.step] for k in keys)
            solar = t["solar_actual_kw"][self.step]
            fc_kwh = sum(v * 0.5 for v in t["solar_fc_kw"])
            cov = 100 * solar / load if load else 0
            save = t["bill_dumb_rm"] - t["bill_wattwise_rm"]
            lines.append("%d  %-22s %d bldgs   load %7s kW   solar now %6s kW"
                         "  fcst %6s kWh   covers %4.1f%%   saves RM %s/mo"
                         % (n, bold(t["label"]), len(keys), f"{load:,.0f}",
                            green(f"{solar:,.0f}"), f"{fc_kwh:,.0f}",
                            cov, f"{save:,.0f}"))
        lines.append("")
        lines.append(dim("portfolio: %d buildings, load %s kW"
                         % (len(self.order), f"{load_total:,.0f}")))
        return "\n".join(lines)

    # ---- buildings of the selected town --------------------------------
    def building_list(self):
        t = self.T["towns"][self.town]
        lines = [bold(t["label"]) + dim("  (town %s)" % self.town),
                 dim("select <name|number> to inspect; back returns to towns")]
        fc_kwh = sum(v * 0.5 for v in t["solar_fc_kw"])
        lines.append("town solar forecast %s kWh today   solar now %s kW"
                     % (f"{fc_kwh:,.0f}",
                        green(f"{t['solar_actual_kw'][self.step]:,.0f}")))
        lines.append("")
        for n, k in enumerate(t["buildings"], 1):
            b = self.b(k)
            tr = self.trace(k)
            load = tr["total_kw"][self.step]
            solar = tr["solar_kw"][self.step]
            used = min(solar, load)
            cov = 100 * used / load if load else 0
            shave = ("-%s%%" % b["shave_pct"]) if b["shave_pct"] > 0 else "-"
            lines.append("%d  %-26s load %6s kW  solar %5s kW (use %5s kW,"
                         " %4.1f%%)  peak %6s kW  shave %6s"
                         % (n, b["label"], f"{load:,.0f}",
                            f"{solar:,.0f}", f"{used:,.0f}", cov,
                            f"{b['peak_dumb_kw']:,.0f}", shave))
        return "\n".join(lines)

    # ---- one building ---------------------------------------------------
    def building_detail(self):
        k = self.selected
        b = self.b(k)
        tr = self.trace(k)
        w = b["wattwise"]
        saving = round(b["bill_dumb_rm"] - b["bill_wattwise_rm"])
        zone = tr["zone_c"][self.step]
        banked = tr["stored_kwh"][self.step]
        cap = b.get("cap_kwh", 900)
        action = tr["action"][self.step].replace("-", " ")
        # maintenance stats over the elapsed day
        zmax = max(tr["zone_c"][:self.step + 1])
        zover = sum(1 for z in tr["zone_c"][:self.step + 1] if z > 26.01)
        pmax = self.plant_max(k)
        pnow = tr["chiller_kw"][self.step]
        full_h = sum(1 for v in tr["chiller_kw"][:self.step + 1]
                     if v >= 0.9 * pmax) * 0.5
        lines = [
            bold(b["label"]) + dim("  (%s)" % k),
            "grid draw now     %s kW   (solar %s kW)"
            % (bold(f"{tr['net_kw'][self.step]:,.0f}"),
               f"{tr['solar_kw'][self.step]:,.0f}"),
            "billed peak       %s kW -> %s kW under wattwise  (shave %s%%)"
            % (f"{b['peak_dumb_kw']:,.0f}", f"{b['peak_wattwise_kw']:,.0f}",
               b["shave_pct"]),
            "MD charge         RM %s/mo -> RM %s/mo   saves RM %s/mo"
            % (f"{b['bill_dumb_rm']:,.0f}", f"{b['bill_wattwise_rm']:,.0f}",
               green(f"{saving:,.0f}")),
            "zone / cold bank  %.1fC   %s kWh / %s kWh"
            % (zone, f"{banked:,.0f}", f"{cap:,.0f}"),
            "current action    " + bold(action),
            "solar now         %s kW forecast, %s kW generating;"
            " on-site use %s kW of %s kW load (%.1f%%)"
            % (f"{tr['solar_fc_kw'][self.step]:,.0f}",
               green(f"{tr['solar_kw'][self.step]:,.0f}"),
               f"{min(tr['solar_kw'][self.step], tr['total_kw'][self.step]):,.0f}",
               f"{tr['total_kw'][self.step]:,.0f}",
               100 * min(tr["solar_kw"][self.step], tr["total_kw"][self.step])
               / tr["total_kw"][self.step] if tr["total_kw"][self.step] else 0),
            "",
            bold("plant detail (maintenance)"),
            "chiller loading   %s %4d%%  (%s / %s kW)"
            % (bar(pnow / pmax if pmax else 0, 20), 100 * pnow / pmax if pmax else 0,
               f"{pnow:,.0f}", f"{pmax:,.0f}"),
            "zone today        max %.1fC   steps above 26C: %d%s"
            % (zmax, zover, red("  <-- CHECK" if zover else "")),
            "full-load runtime %s h at >90%% plant so far today%s"
            % (f"{full_h:.1f}", amber("  <-- wear watch") if full_h >= 4 else ""),
            "",
        ]

        # ascii sparkline of the day's net draw, mode line + other-mode ghost
        dumb = b["dumb"]["net_kw"]
        wise = b["wattwise"]["net_kw"]
        mx = max(max(dumb), max(wise)) * 1.05 or 1.0
        lines.append(bold("net grid draw, full day (o = baseline, * = wattwise, | = now)"))
        for i in range(N):
            other = wise if self.mode == "dumb" else dumb
            cur = dumb if self.mode == "dumb" else wise
            w_other = int(round(other[i] / mx * 46))
            w_cur = int(round(cur[i] / mx * 46))
            row = [" "] * 47
            row[min(w_other, 46)] = "o"
            row[min(w_cur, 46)] = "*" if w_cur != w_other else "@"
            mark = " " + dim("<- now") if i == self.step else ""
            # mark the billed window 08:30-10:30 in the time label
            tlabel = self.times[i]
            if 8.5 <= (i / 2) < 10.5:
                tlabel = amber(tlabel)
            lines.append("%s |%s%s" % (tlabel, "".join(row), mark))
        lines.append(dim("kW scale 0 -> %s" % f"{mx:,.0f}"))
        return "\n".join(lines)

    def tab_forecast(self):
        F = self.T["forecast"]
        errs, ape = [], []
        # only elapsed steps: the forecast is 30-min-ahead, never see ahead
        for i in range(self.step + 1):
            f = F["solar_fc_kw"][i]
            a = F["solar_actual_kw"][i]
            if f is not None and a > 20:
                errs.append(abs(f - a))
                ape.append(abs(f - a) / a)
        mae = (sum(errs) / len(errs)) if errs else None
        mape = (100 * sum(ape) / len(ape)) if ape else None
        pk = max((F["solar_actual_kw"][i] for i in range(self.step + 1)),
                 default=0)
        lines = [
            bold("WATTWISE-1 live forecasts (base site, 30-min ahead)"),
            "solar MAE   %s   mean abs error %s   peak so far %s kW"
            % (("-" if mae is None else f"{mae:.1f} kW"),
               ("-" if mape is None else f"{mape:.1f}%"),
               f"{pk:,.0f}"),
            "demand MAE  10.2 kW (walk-forward, held-out 60 days)",
            "",
            bold("solar output, daylight steps (amber = forecast, green = actual)"),
        ]
        peak_fc = max((v for v in F["solar_fc_kw"] if v is not None), default=1) or 1
        for i in range(12, 40):
            f = F["solar_fc_kw"][i]
            a = F["solar_actual_kw"][i]
            fb = bar((f or 0) / peak_fc, 30, amber("#") if USE_COLOR else "#")
            ab = bar(a / peak_fc, 30, green("=") if USE_COLOR else "=")
            mark = dim(" <- now") if i == self.step else ""
            lines.append("%s  %s %7s   %s %7s%s"
                         % (F["times"][i], fb, f"{f:.1f}" if f is not None else "-",
                            ab, f"{a:.1f}", mark))
        lines.append(dim("model metrics (held-out): solar nRMSE 7.35% R2 0.996,"
                         " demand MAE 10.2 kW. benchmark LSTM nRMSE 6.75%."))

        # PV health: sustained under-delivery vs forecast = inspect panels
        lag = 0
        worst = 0
        for i in range(self.step + 1):
            f = F["solar_fc_kw"][i]
            a = F["solar_actual_kw"][i]
            if f is not None and f > 50:
                if a < 0.8 * f:
                    lag += 1
                    worst = max(worst, 1 - a / f)
                else:
                    lag = 0
            else:
                lag = 0
        lines.append("")
        lines.append(bold("PV health (elapsed daylight)"))
        if lag >= 3:
            lines.append(red("UNDER-DELIVERY: actuals <80%% of forecast for %d"
                             " consecutive steps (worst gap %.0f%%)"
                             % (lag, 100 * worst)))
            lines.append(red("action: inspect panels / inverter / soiling"))
        else:
            lines.append(green("ok: no sustained under-delivery vs forecast"
                               " (flag raises at 3+ steps below 80%)"))
        return "\n".join(lines)

    def tab_scheduler(self):
        if self.mode != "wattwise":
            return ("scheduler offline. switch mode first: "
                    + bold("mode wattwise"))
        lines = [bold("WATTWISE-2 control room - rule state per building")]
        for k in self.order:
            b = self.b(k)
            w = b["wattwise"]
            a = w["action"][self.step].replace("-", " ")
            lines.append("%-24s %-18s chiller %6s kW   solar %6s kW"
                         % (b["label"], bold(a),
                            f"{w['chiller_kw'][self.step]:,.0f}",
                            f"{w['solar_kw'][self.step]:,.0f}"))
        lines.append("")
        lines.append(bold("cold bank"))
        for k in self.order:
            b = self.b(k)
            v = b["wattwise"]["stored_kwh"][self.step]
            cap = b.get("cap_kwh", 900) or 900
            pct = 100 * v / cap
            col = green if pct > 60 else (amber if pct > 25 else red)
            lines.append("%-24s %s %5s / %s kWh"
                         % (b["label"], col(bar(pct)), f"{v:,.0f}",
                            f"{cap:,.0f}"))
        # intervention log: rule changes up to now
        lines.append("")
        lines.append(bold("intervention log (rule changes so far)"))
        log = []
        for k in self.order:
            b = self.b(k)
            acts = b["wattwise"]["action"]
            prev = acts[0]
            for i in range(1, self.step + 1):
                if acts[i] != prev:
                    log.append("%s  %-22s %s -> %s"
                               % (self.times[i], b["label"].replace("Elmina ", ""),
                                  prev.replace("-", " "),
                                  acts[i].replace("-", " ")))
                    prev = acts[i]
        lines.extend(log[-12:] if log
                     else [dim("no rule changes yet at " + self.clock())])

        # next up: when each building's rule changes next (plan rounds around)
        lines.append("")
        lines.append(bold("next up (upcoming rule changes today)"))
        for k in self.order:
            acts = self.b(k)["wattwise"]["action"]
            nxt = None
            for i in range(self.step + 1, N):
                if acts[i] != acts[self.step]:
                    nxt = i
                    break
            if nxt is not None:
                lines.append("%-24s %s -> %s at %s"
                             % (self.b(k)["label"].replace("Elmina ", ""),
                                bold(acts[self.step].replace("-", " ")),
                                acts[nxt].replace("-", " "),
                                self.times[nxt]))
            else:
                lines.append("%-24s %s for the rest of the day"
                             % (self.b(k)["label"].replace("Elmina ", ""),
                                acts[self.step].replace("-", " ")))
        return "\n".join(lines)

    def tab_reports(self):
        lines = [bold("EECA 2024 threshold check (illustrative annualisation,"
                      " one simulated day x365)")]
        for k in self.order:
            b = self.b(k)
            kwh = sum(v * 0.5 for v in b["wattwise"]["net_kw"])
            gj = kwh * 3.6 / 1000 * 365
            over = gj > 21600
            mark = red("OVER - statutory duties apply") if over else green("under")
            lines.append("%-24s %s %9s GJ/yr  %s"
                         % (b["label"], bar(gj / 27000, 26), f"{gj:,.0f}", mark))
        lines.append(dim("threshold 21,600 GJ in any 12 consecutive months"
                         " (P.U.(A) 466/2024 reg. 3, verified)"))
        lines.append("")
        lines.append(bold("maximum demand charge, monthly breakdown"))
        cap_pct = round(self.cap_share * 100)
        head = ("%-24s %9s %13s %13s %13s %13s"
                % ("building", "peak kW", "capacity (%d%%)" % cap_pct,
                   "network (%d%%)" % (100 - cap_pct), "total MD/mo",
                   "saves"))
        lines.append(head)
        for k in self.order:
            b = self.b(k)
            total = b["bill_dumb_rm"] if self.mode == "dumb" else b["bill_wattwise_rm"]
            peak = b["peak_dumb_kw"] if self.mode == "dumb" else b["peak_wattwise_kw"]
            cap = round(total * self.cap_share)
            net = round(total - cap)
            save = round(b["bill_dumb_rm"] - b["bill_wattwise_rm"])
            lines.append("%-24s %9s %13s %13s %13s %13s"
                         % (b["label"], f"{peak:,.0f}", "RM %s" % f"{cap:,.0f}",
                            "RM %s" % f"{net:,.0f}", "RM %s" % f"{total:,.0f}",
                            green("RM %s" % f"{save:,.0f}")))

        # rule runtime summary: hours each plant spends in each state
        lines.append("")
        lines.append(bold("rule runtime, full day (hours per rule, wattwise)"))
        rules = ["precool", "coast", "soak", "recovery", "comfort",
                 "hold", "night", "essential", "safety"]
        hdr = "%-24s" % "building" + "".join("%8s" % r[:7] for r in rules)
        lines.append(hdr)
        for k in self.order:
            acts = self.b(k)["wattwise"]["action"]
            hours = {r: 0.0 for r in rules}
            for a in acts:
                for r in rules:
                    if a.startswith(r):
                        hours[r] += 0.5
                        break
            lines.append("%-24s" % self.b(k)["label"].replace("Elmina ", "")
                         + "".join("%8.1f" % hours[r] if hours[r] else "%8s" % "-"
                                   for r in rules))
        lines.append(dim("export csv at the prompt writes the full township"
                         " dataset (same as the dashboard export)"))
        return "\n".join(lines)

    # ---- render -------------------------------------------------------
    def render(self):
        fn = {"overview": self.tab_overview,
              "buildings": self.tab_buildings,
              "forecast": self.tab_forecast,
              "scheduler": self.tab_scheduler,
              "reports": self.tab_reports}[self.tab]
        body = fn()
        return self.header() + "\n" + body + "\n" + dim(MENU) + "\n"

# ---------------------------------------------------------------- commands

# always-shown tab menu; numbers work at the prompt as shortcuts
MENU = ("tabs: 1 home | 2 buildings | 3 forecast | 4 scheduler | 5 reports"
        "   (export csv, help, quit)")

HELP = """commands:
  1..5                jump straight to a tab
  town <name|1-3>     open a township
  select <name|#>     pick a building from the open town
  back                up one level (building -> town -> portfolio)
  next | prev         next / previous building (or town at the top level)
  set time HH:MM       jump the clock (snaps to the 30-min grid)
  mode dumb|wattwise   switch scenario (scheduler needs wattwise)
  play                 run the day (Ctrl+C stops playback)
  pause                stop playback
  reset                back to 00:00
  tab <name>           overview | buildings | forecast | scheduler | reports
  export               write the township CSV (same as the dashboard export)
  help                 this list
  quit                 exit"""

def resolve_building(app, name):
    # numbers pick from the visible list; names match key prefix or label
    name = name.lower()
    pool = (app.T["towns"][app.town]["buildings"]
            if app.town else app.order)
    if name.isdigit():
        i = int(name) - 1
        if 0 <= i < len(pool):
            return pool[i]
        return None
    for k in pool:
        if k.startswith(name) or name == k:
            return k
    for k in pool:
        if app.b(k)["label"].lower().find(name) >= 0:
            return k
    return None

def resolve_town(app, name):
    name = name.lower()
    if name.isdigit():
        i = int(name) - 1
        if 0 <= i < len(app.towns):
            return app.towns[i]
        return None
    for k in app.towns:
        if k.startswith(name) or name == k:
            return k
    for k in app.towns:
        if app.T["towns"][k]["label"].lower().find(name) >= 0:
            return k
    return None

def run_command(app, raw, msgs):
    # returns "quit", "play", or None; informational output goes into msgs
    # so the caller can print it AFTER the screen refresh (otherwise the
    # clear would wipe it before anyone can read it)
    cmd = raw.strip().lower()
    if not cmd:
        return None
    parts = cmd.split(None, 1)
    head = parts[0]
    arg = parts[1] if len(parts) > 1 else ""
    if head == "help":
        msgs.append(HELP)
    elif head in ("1", "2", "3", "4", "5"):
        app.tab = {"1": "overview", "2": "buildings", "3": "forecast",
                   "4": "scheduler", "5": "reports"}[head]
    elif head == "quit" or head == "exit":
        return "quit"
    elif head == "export":
        msgs.append(export_csv(app))
    elif head == "select":
        if app.town is None:
            # no town yet: treat select as a town jump for convenience
            tk = resolve_town(app, arg)
            if tk:
                app.town = tk
                app.selected = None
                app.tab = "buildings"
            elif arg:
                msgs.append(red("pick a town first: town <name|1-3>"))
            else:
                msgs.append(red("town <name|1-3> first, then select a building"))
        else:
            k = resolve_building(app, arg)
            if k:
                app.selected = k
                app.tab = "buildings"
            else:
                msgs.append(red("no building matches '%s'" % arg))
    elif head == "town":
        tk = resolve_town(app, arg)
        if tk:
            app.town = tk
            app.selected = None
            app.tab = "buildings"
        else:
            msgs.append(red("no town matches '%s'" % arg))
    elif head == "back":
        if app.selected is not None:
            app.selected = None
        elif app.town is not None:
            app.town = None
        else:
            msgs.append(dim("already at the top"))
    elif head == "next" or head == "prev":
        if app.town is None:
            msgs.append(dim("open a town first: town <name|1-3>"))
        else:
            pool = app.T["towns"][app.town]["buildings"]
            cur = pool.index(app.selected) if app.selected in pool else 0
            app.selected = pool[(cur + (1 if head == "next" else -1)) % len(pool)]
    elif head == "set" and arg.startswith("time"):
        t = arg[4:].strip()
        try:
            hh, mm = t.split(":")
            idx = min(47, max(0, round((int(hh) * 60 + int(mm)) / 30)))
            app.step = idx
            snapped = app.times[idx] != "%02d:%02d" % (int(hh), int(mm))
            msgs.append(dim("time set to %s%s" % (app.times[idx],
                  " (snapped to 30-min grid)" if snapped else "")))
        except ValueError:
            msgs.append(red("usage: set time HH:MM"))
    elif head == "mode":
        if arg in ("dumb", "baseline"):
            app.mode = "dumb"
        elif arg == "wattwise" or arg == "wise":
            app.mode = "wattwise"
        else:
            msgs.append(red("mode: dumb | wattwise"))
    elif head == "play":
        return "play"
    elif head == "pause":
        pass
    elif head == "reset":
        app.step = 0
    elif head == "tab":
        if arg in ("overview", "home"):
            app.tab = "overview"
        elif arg in ("buildings", "building"):
            app.tab = "buildings"
        elif arg == "forecast":
            app.tab = "forecast"
        elif arg == "scheduler":
            app.tab = "scheduler"
        elif arg == "reports":
            app.tab = "reports"
        else:
            msgs.append(red("tab: overview | buildings | forecast | scheduler | reports"))
    else:
        msgs.append(red("unknown command. type help"))
    return None

def export_csv(app):
    # same rows the dashboard export writes, from the same data
    dest = HERE / "wattwise_township_demo.csv"
    lines = ["building,time,mode,net_grid_kw,chiller_kw,zone_c,stored_kwh,"
             "solar_kw,action"]
    for k in app.order:
        b = app.b(k)
        for m in ("dumb", "wattwise"):
            tr = b[m]
            for i in range(N):
                lines.append(",".join(str(x) for x in
                    (b["label"], tr["times"][i], m, tr["net_kw"][i],
                     tr["chiller_kw"][i], tr["zone_c"][i], tr["stored_kwh"][i],
                     tr["solar_kw"][i], tr["action"][i])))
    dest.write_text("\n".join(lines) + "\n")
    return green("wrote %s (%d rows)" % (dest, len(lines) - 1))

def play_loop(app, speed):
    # run the day like the dashboard play button; Ctrl+C returns to prompt
    try:
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            print(app.render())
            print(dim("playing... Ctrl+C to stop"))
            time.sleep(speed)
            app.step = (app.step + 1) % N
    except KeyboardInterrupt:
        pass

# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description="WattWise CLI monitor")
    p.add_argument("--tab", default="overview",
                   choices=["overview", "buildings", "forecast",
                            "scheduler", "reports"])
    p.add_argument("--mode", default="dumb", choices=["dumb", "wattwise"])
    p.add_argument("--time", default=None, help="HH:MM on the 30-min grid")
    p.add_argument("--building", "-b", default=None, help="select building")
    p.add_argument("--speed", type=float, default=0.6,
                   help="seconds per step in play mode")
    p.add_argument("--live", action="store_true",
                   help="start playing immediately (Ctrl+C stops)")
    p.add_argument("--once", action="store_true",
                   help="print once and exit (for scripts/monitoring)")
    args = p.parse_args()

    if not DATA.exists():
        print(red("data/township.json not found."))
        print("generate it first:  python generate_ui_data.py")
        sys.exit(1)

    app = App(json.loads(DATA.read_text()))
    app.tab = args.tab
    app.mode = args.mode
    if args.time:
        try:
            hh, mm = args.time.split(":")
            app.step = min(47, max(0, round((int(hh) * 60 + int(mm)) / 30)))
        except ValueError:
            print(red("--time expects HH:MM"))
            sys.exit(2)
    if args.building:
        k = resolve_building(app, args.building)
        if not k:
            print(red("no building matches '%s'" % args.building))
            sys.exit(2)
        app.selected = k
        app.town = app.b(k)["town"]
        if args.tab == "overview":
            app.tab = "buildings"

    if args.once:
        print(app.render())
        return

    if args.live:
        play_loop(app, args.speed)

    # interactive loop, same commands as the dashboard command bar
    print(app.render())
    while True:
        try:
            raw = input(c("ww>", "32") + " ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        msgs = []
        snap = (app.tab, app.mode, app.step, app.selected)
        result = run_command(app, raw, msgs)
        if result == "quit":
            break
        if result == "play":
            play_loop(app, args.speed)
        # re-render only when the state actually changed; for help/errors
        # the message alone is the point, don't scroll it away
        if (app.tab, app.mode, app.step, app.selected) != snap:
            os.system("cls" if os.name == "nt" else "clear")
            print(app.render())
        for m in msgs:
            print(m)

if __name__ == "__main__":
    main()
