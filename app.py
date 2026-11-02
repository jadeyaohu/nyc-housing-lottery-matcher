"""NYC Housing Lottery Matcher - Streamlit app.

Run:  streamlit run app.py
Public data only. Not an eligibility decision and not an application service.
"""

from datetime import date

import streamlit as st

import match as m

st.set_page_config(page_title="NYC Housing Lottery Matcher", page_icon="🏠", layout="wide")


@st.cache_data
def lotteries():
    return m.load_lotteries()


st.title("🏠 NYC Housing Lottery Matcher · 纽约保障房抽签匹配")
st.caption("Free, public data only (NYC Open Data + HPD AMI). Not an eligibility decision. "
           "We never apply for you and never predict log numbers. · 仅用公开数据，不代申请，不预测排号。")

with st.sidebar:
    st.header("Your household · 家庭信息")
    size = st.number_input("Household size · 家庭人数", 1, 12, 2)
    income = st.number_input("Total yearly income ($) · 家庭年收入", 0, 1_000_000, 70_000, step=1_000)
    units = st.multiselect("Unit size · 户型 (blank = rough guide)", list(m.UNIT_COLS))
    boroughs = st.multiselect("Borough · 区", list(m.BOROUGHS), format_func=lambda b: m.BOROUGHS[b])
    zip_code = st.text_input("Current home ZIP · 现住址邮编 (for community board preference)")
    flags = st.multiselect("Applies to your household · 适用情况",
                           [k for k in m.PREFS if k not in ("community_board", "senior")],
                           format_func=lambda k: m.PREF_LABELS[k])
    has_senior = st.checkbox("Someone is 62+ · 有 62 岁以上成员")
    history = st.checkbox("Show past lotteries too · 显示历史抽签", value=True)

cb = None
if zip_code.strip().isdigit() and len(zip_code.strip()) == 5:
    cb = m.zip_to_community_board(zip_code.strip())

hh = m.Household(int(size), float(income), units, boroughs, cb,
                 flags + (["senior"] if has_senior else []), has_senior)
r = m.match(lotteries(), hh, today=date.today(), include_history=history)
t = r["matches"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("% of AMI", f"{r['ami_percent']}%")
c2.metric("Income band · 收入档", r["band"].replace(" Income", ""))
c3.metric("Open now · 可报名", int(t["open_now"].sum()) if len(t) else 0)
c4.metric("Matches shown · 匹配数", len(t))

if r["near_band"]:
    st.info(f"You are close to a band edge, so some **{r['near_band']}** units may also fit. "
            "Check each lottery's exact income range. · 你接近收入档边界，请看每个广告的具体收入范围。")
if r["units_guessed"]:
    st.caption(f"Unit sizes not chosen; using a rough guide: {', '.join(r['units_considered'])}. "
               "Each ad sets its own household-size limits.")
if cb:
    st.caption(f"ZIP {zip_code} → most likely community board {cb} (best guess from building data).")
if r["band"] == m.ABOVE:
    st.warning("Income is above 165% AMI; very few lottery units are in this band.")

if not len(t):
    st.write("No matching lotteries with these filters. Try more unit sizes or boroughs, or show past lotteries.")
    st.stop()

show = t.rename(columns={"start": "Start", "end": "Deadline", "open_now": "Open now",
                         "units_in_band": "Units in your band", "units_your_size": "Units of your size (all bands)",
                         "your_preferences": "Preferences that may apply", "competition_note": "Note"})
show["Borough"] = show["Borough"].map(m.BOROUGHS).fillna(show["Borough"])
st.dataframe(show.drop(columns=["Lottery ID"]), width="stretch", hide_index=True)

st.subheader("Documents to get ready · 提前准备的材料")
st.markdown(
    "- Photo ID and Social Security / ITIN for each household member\n"
    "- Last 6–8 weeks of pay stubs, or employer letter; self-employed: tax returns + profit & loss\n"
    "- Most recent federal tax return(s)\n"
    "- Bank statements (usually several recent months)\n"
    "- Proof of current address (for community board preference)\n\n"
    "Exact list varies by building; follow the marketing agent's request. "
    "Applying on Housing Connect is always free."
)
st.caption("Data: NYC Open Data, Advertised Lotteries on Housing Connect (By Lottery / By Building). "
           f"Mini lotteries and Mitchell-Lama lotteries are not included. AMI: HPD {m.AMI_YEAR} table.")
