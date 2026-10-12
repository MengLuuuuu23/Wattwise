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
        self.times = data["buildings"]["office_tower"]["dumb"]["times"]
        self.order = ["mall", "office_tower", "innovation_park",
                      "data_centre", "warehouse"]
        self.mode = "dumb"
        self.step = 0
        self.tab = "overview"
        self.selected = "mall"
        self.tariff = data.get("tariff", {})
        self.cap_share = self.tariff.get("capacity_share", 0.311)

    # ---- helpers ------------------------------------------------------
    def b(self, key):
        return self.T["buildings"][key]

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
        for k in self.order:
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
            rows.append("%-24s %9s kW %9s kW %7s %11s   %s"
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
        return "\n".join(out)

    def tab_buildings(self):
        k = self.selected
        b = self.b(k)
        tr = self.trace(k)
        w = b["wattwise"]
        saving = round(b["bill_dumb_rm"] - b["bill_wattwise_rm"])
        zone = tr["zone_c"][self.step]
        banked = tr["stored_kwh"][self.step]
        cap = b.get("cap_kwh", 900)
        action = tr["action"][self.step].replace("-", " ")
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
        return "\n".join(lines)

    # ---- render -------------------------------------------------------
    def render(self):
        fn = {"overview": self.tab_overview,
              "buildings": self.tab_buildings,
              "forecast": self.tab_forecast,
              "scheduler": self.tab_scheduler,
              "reports": self.tab_reports}[self.tab]
        body = fn()
        return self.header() + "\n" + body + "\n"

# ---------------------------------------------------------------- commands

HELP = """commands:
  select <building>    pick a building (prefix ok: mall, office, dc, ware)
  next | prev          next / previous building
  set time HH:MM       jump the clock (snaps to the 30-min grid)
  mode dumb|wattwise   switch scenario (scheduler needs wattwise)
  play                 run the day (Ctrl+C stops playback)
  pause                stop playback
  reset                back to 00:00
  tab <name>           overview | buildings | forecast | scheduler | reports
  help                 this list
  quit                 exit"""

def resolve_building(app, name):
    # match on key prefix or label substring, like the dashboard
    name = name.lower()
    for k in app.order:
        if k.startswith(name) or name == k:
            return k
    for k in app.order:
        if app.b(k)["label"].lower().find(name) >= 0:
            return k
    return None

def run_command(app, raw):
    # returns "quit", "play", or None
    cmd = raw.strip().lower()
    if not cmd:
        return None
    parts = cmd.split(None, 1)
    head = parts[0]
    arg = parts[1] if len(parts) > 1 else ""
    if head == "help":
        print(HELP)
    elif head == "quit" or head == "exit":
        return "quit"
    elif head == "select":
        k = resolve_building(app, arg)
        if k:
            app.selected = k
            app.tab = "buildings"
        else:
            print(red("no building matches '%s'" % arg))
    elif head == "next" or head == "prev":
        i = app.order.index(app.selected)
        app.selected = app.order[(i + (1 if head == "next" else -1)) % len(app.order)]
    elif head == "set" and arg.startswith("time"):
        t = arg[4:].strip()
        try:
            hh, mm = t.split(":")
            idx = min(47, max(0, round((int(hh) * 60 + int(mm)) / 30)))
            app.step = idx
            snapped = app.times[idx] != "%02d:%02d" % (int(hh), int(mm))
            print(dim("time set to %s%s" % (app.times[idx],
                  " (snapped to 30-min grid)" if snapped else "")))
        except ValueError:
            print(red("usage: set time HH:MM"))
    elif head == "mode":
        if arg in ("dumb", "baseline"):
            app.mode = "dumb"
        elif arg == "wattwise" or arg == "wise":
            app.mode = "wattwise"
        else:
            print(red("mode: dumb | wattwise"))
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
            print(red("tab: overview | buildings | forecast | scheduler | reports"))
    else:
        print(red("unknown command. type help"))
    return None

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
        result = run_command(app, raw)
        if result == "quit":
            break
        if result == "play":
            play_loop(app, args.speed)
        os.system("cls" if os.name == "nt" else "clear")
        print(app.render())

if __name__ == "__main__":
    main()
