"""NYC Housing Lottery matcher (public data only).

Given a household's size, yearly income and wishes, this script:
  1. works out the household's % of AMI (HPD 2026 table)
  2. puts it in an HPD income band (Extremely Low ... Middle)
  3. lists lotteries that have units in that band and the wanted unit size
  4. shows which preferences may apply and a simple, public-data competition note

It never predicts a log number, never applies for anyone, and is not an
eligibility decision: the lottery's own ad and the marketing agent decide that.

Data: NYC Open Data "Advertised Lotteries on Housing Connect" (By Lottery and
By Building). Mini lotteries and Mitchell-Lama lotteries are not in that data.

Usage:
  python match.py --size 3 --income 85000 --units 1BR 2BR --borough BK BX
  python match.py --size 1 --income 60000 --zip 11226 --history
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# HPD 2026 New York City area AMI, 100% column, by household size.
# Source: nyc.gov/site/hpd/services-and-information/area-median-income.page (read 2026-11-01).
AMI_100 = {1: 118800, 2: 135700, 3: 152700, 4: 169600, 5: 183200, 6: 196800,
           7: 210400, 8: 223900, 9: 237500, 10: 251100, 11: 264600, 12: 278200}
AMI_YEAR = 2026

# HPD income bands (% of AMI). Upper bound inclusive.
BANDS = [
    ("Extremely Low Income", 30),
    ("Very Low Income", 50),
    ("Low Income", 80),
    ("Moderate Income", 120),
    ("Middle Income", 165),
]
ABOVE = "Above Middle Income"

UNIT_COLS = {
    "Studio": "Unit Distribution - Studio",
    "1BR": "Unit Distribution - 1 Bedroom",
    "2BR": "Unit Distribution - 2 Bedrooms",
    "3BR": "Unit Distribution - 3 Bedrooms",
    "4BR+": "Unit Distribution - 4 Bedroom+",
}

# Rough guide only, NOT an official rule: each lottery ad sets its own
# household-size range per unit. Used only when the user doesn't pick sizes.
TYPICAL_UNITS_FOR_SIZE = {
    1: ["Studio", "1BR"], 2: ["Studio", "1BR", "2BR"], 3: ["1BR", "2BR"],
    4: ["2BR", "3BR"], 5: ["2BR", "3BR"], 6: ["3BR", "4BR+"],
}

PREFS = {
    "community_board": "Lottery Community Board Percentage",
    "mobility": "Lottery Mobility Percentage",
    "vision_hearing": "Lottery Vision/Hearing Percentage",
    "municipal_or_veteran": "Lottery Municipal Employee/Military Veteran Percentage",
    "nycha": "Lottery NYCHA Percentage",
    "senior": "Lottery Senior Percentage",
}
PREF_LABELS = {
    "community_board": "Community board resident",
    "mobility": "Mobility disability",
    "vision_hearing": "Vision/hearing disability",
    "municipal_or_veteran": "City employee / veteran",
    "nycha": "NYCHA resident",
    "senior": "Senior (62+)",
}

BOROUGHS = {"MN": "Manhattan", "BX": "Bronx", "BK": "Brooklyn", "QN": "Queens", "SI": "Staten Island"}


# ---------- step 1-2: income -> AMI% -> band ----------

def ami_percent(size: int, income: float, digits: int | None = 1) -> float:
    if size < 1:
        raise ValueError("Household size must be at least 1")
    base = AMI_100.get(size) or AMI_100[12] + (size - 12) * (AMI_100[12] - AMI_100[11])
    pct = income / base * 100
    return round(pct, digits) if digits is not None else pct


def income_band(pct: float) -> str:
    for name, upper in BANDS:
        if pct <= upper:
            return name
    return ABOVE


def nearby_band(pct: float, margin: float = 5.0) -> str | None:
    """If the household is within `margin` points of a band edge, name the other band."""
    names = [n for n, _ in BANDS] + [ABOVE]
    for i, (name, upper) in enumerate(BANDS):
        if upper < pct <= upper + margin:      # just above an edge -> band below
            return name
        if upper - margin <= pct <= upper:     # just below an edge -> band above
            return names[i + 1]
    return None


# ---------- data ----------

def load_lotteries(path: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(path or os.path.join(HERE, "data", "lotteries.csv"), low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df["Lottery Status"] = df["Lottery Status"].str.strip()
    df["start"] = pd.to_datetime(df["Lottery Start Date"], errors="coerce").dt.date
    df["end"] = pd.to_datetime(df["Lottery End Date"], errors="coerce").dt.date
    num = [c for c in df.columns if c.startswith(("Unit Distribution", "Applied Income", "Lottery ")) and
           c not in ("Lottery ID", "Lottery Name", "Lottery Status", "Lottery Start Date", "Lottery End Date")]
    df[num] = df[num].apply(pd.to_numeric, errors="coerce").fillna(0)
    df["Community Board"] = pd.to_numeric(df["Community Board"], errors="coerce")
    return df


def zip_to_community_board(zip_code: str, buildings_path: str | None = None) -> int | None:
    """Best guess of a ZIP's community board from the By Building file (most common match)."""
    b = pd.read_csv(buildings_path or os.path.join(HERE, "data", "buildings.csv"), low_memory=False)
    b.columns = [c.strip() for c in b.columns]
    b["Postcode"] = pd.to_numeric(b["Postcode"], errors="coerce")
    hits = b.loc[b["Postcode"] == int(zip_code), "Community Board"].dropna()
    return int(hits.mode().iloc[0]) if not hits.empty else None


# ---------- step 3-4: match ----------

@dataclass
class Household:
    size: int
    income: float
    units: list[str] = field(default_factory=list)       # e.g. ["1BR", "2BR"]
    boroughs: list[str] = field(default_factory=list)    # e.g. ["BK", "BX"]
    community_board: int | None = None                   # e.g. 317 (Brooklyn CB 17)
    flags: list[str] = field(default_factory=list)       # keys of PREFS that apply
    has_senior: bool = False


def match(df: pd.DataFrame, hh: Household, today: date | None = None, include_history: bool = False) -> dict:
    today = today or date.today()
    pct = ami_percent(hh.size, hh.income)
    band = income_band(ami_percent(hh.size, hh.income, digits=None))  # band on unrounded %
    units = hh.units or TYPICAL_UNITS_FOR_SIZE.get(hh.size, ["3BR", "4BR+"])
    band_col = f"Applied Income AMI Category - {band}"

    m = df[df[band_col] > 0].copy()
    m["units_your_size"] = sum(m[UNIT_COLS[u]] for u in units)
    m = m[m["units_your_size"] > 0]
    if hh.boroughs:
        m = m[m["Borough"].isin(hh.boroughs)]
    # Senior buildings (most units set aside for 62+) only fit households with a senior.
    if not hh.has_senior:
        m = m[m[PREFS["senior"]] < 50]

    m["open_now"] = m["end"].apply(lambda d: d is not None and not pd.isna(d) and d >= today)
    if not include_history:
        m = m[m["open_now"]]

    m["units_in_band"] = m[band_col]
    m["band_share"] = (m[band_col] / m["Unit Count"].where(m["Unit Count"] > 0)).round(2)

    def prefs_for(row):
        out = []
        for key in hh.flags + (["community_board"] if hh.community_board else []):
            share = row[PREFS[key]]
            if key == "community_board":
                if row["Community Board"] != hh.community_board:
                    continue
                out.append(f"{PREF_LABELS[key]} ({share:g}%)" if share > 0
                           else f"{PREF_LABELS[key]} (share not listed; check ad)")
                continue
            if share > 0:
                out.append(f"{PREF_LABELS[key]} ({share:g}%)")
        return "; ".join(dict.fromkeys(out))

    m["your_preferences"] = m.apply(prefs_for, axis=1) if len(m) else []
    m["competition_note"] = m.apply(_competition_note, axis=1) if len(m) else []
    m = m.sort_values(["open_now", "end"], ascending=[False, False])

    cols = ["Lottery ID", "Lottery Name", "Borough", "Community Board", "Development Type",
            "start", "end", "open_now", "Unit Count", "units_in_band", "units_your_size",
            "your_preferences", "competition_note"]
    return {
        "ami_percent": pct,
        "band": band,
        "near_band": nearby_band(pct),
        "units_considered": units,
        "units_guessed": not hh.units,
        "matches": m[cols].reset_index(drop=True),
    }


def _competition_note(row) -> str:
    """Plain-language note from public numbers only. Not a prediction."""
    n = int(row["units_in_band"])
    if n <= 3:
        size = f"Very few units in your band ({n})"
    elif n <= 15:
        size = f"Small number of units in your band ({n})"
    else:
        size = f"{n} units in your band"
    return size + "; lotteries often draw far more applicants than units."


# ---------- CLI ----------

def main():
    p = argparse.ArgumentParser(description="Match a household to NYC housing lotteries (public data).")
    p.add_argument("--size", type=int, required=True, help="household size")
    p.add_argument("--income", type=float, required=True, help="total yearly household income, $")
    p.add_argument("--units", nargs="*", default=[], choices=list(UNIT_COLS))
    p.add_argument("--borough", nargs="*", default=[], choices=list(BOROUGHS))
    p.add_argument("--zip", help="current home ZIP, to guess community board")
    p.add_argument("--flags", nargs="*", default=[], choices=[k for k in PREFS if k != "community_board"])
    p.add_argument("--senior", action="store_true", help="household includes someone 62+")
    p.add_argument("--history", action="store_true", help="include closed lotteries for reference")
    a = p.parse_args()

    cb = zip_to_community_board(a.zip) if a.zip else None
    hh = Household(a.size, a.income, a.units, a.borough, cb, a.flags + (["senior"] if a.senior else []), a.senior)
    r = match(load_lotteries(), hh, include_history=a.history)

    print(f"Household of {a.size}, ${a.income:,.0f}/yr  ->  {r['ami_percent']}% of AMI ({AMI_YEAR})  ->  {r['band']}")
    if r["near_band"]:
        print(f"  Close to a band edge: some '{r['near_band']}' units may also fit. Check each ad's income range.")
    if r["units_guessed"]:
        print(f"  Unit sizes not given; using a rough guide: {', '.join(r['units_considered'])}")
    if cb:
        print(f"  ZIP {a.zip} is most likely community board {cb}")
    t = r["matches"]
    print(f"\n{len(t)} {'lotteries (incl. history)' if a.history else 'lotteries open now'}:\n")
    if len(t):
        with pd.option_context("display.max_colwidth", 45, "display.width", 200):
            print(t.head(30).to_string(index=False))
    print("\nNot an eligibility decision: each lottery's ad sets exact income and household-size limits.")


if __name__ == "__main__":
    main()
