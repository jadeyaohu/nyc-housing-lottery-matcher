"""NYC Housing Lottery Matcher - Streamlit app (English / 中文).

Run:  streamlit run app.py
Language: follows the browser's language (Chinese -> 中文, anything else -> English),
can be switched with the EN / 中文 toggle, or forced with ?lang=zh / ?lang=en in the URL.
Public data only. Not an eligibility decision and not an application service.
"""

from datetime import date

import streamlit as st

import match as m

T = {
    "en": {
        "page": "NYC Housing Lottery Matcher",
        "title": "🏠 NYC Housing Lottery Matcher",
        "intro": "Free, public data only (NYC Open Data + HPD AMI). Not an eligibility decision. "
                 "We never apply for you and never predict log numbers.",
        "household": "Your household",
        "size": "Household size",
        "income": "Total yearly income ($)",
        "units": "Unit size (leave blank for a rough guide)",
        "boroughs": "Borough",
        "zip": "Current home ZIP (for community board preference)",
        "flags": "Applies to your household",
        "senior": "Someone in the household is 62+",
        "history": "Show past lotteries too",
        "m_ami": "% of AMI", "m_band": "Income band", "m_open": "Open now", "m_count": "Matches shown",
        "near": "You are close to a band edge, so some **{b}** units may also fit. Check each lottery's exact income range.",
        "guess": "Unit sizes not chosen; using a rough guide: {u}. Each ad sets its own household-size limits.",
        "cb": "ZIP {z} → most likely community board {cb} (best guess from building data).",
        "above": "Income is above 165% AMI; very few lottery units are in this band.",
        "none": "No matching lotteries with these filters. Try more unit sizes or boroughs, or show past lotteries.",
        "cols": {"Lottery Name": "Lottery", "Borough": "Borough", "Community Board": "Community board",
                 "Development Type": "Type", "start": "Start", "end": "Deadline", "open_now": "Open now",
                 "Unit Count": "Total units", "units_in_band": "Units in your band",
                 "units_your_size": "Units of your size (all bands)",
                 "your_preferences": "Preferences that may apply", "competition_note": "Note"},
        "docs_h": "Documents to get ready",
        "docs": "- Photo ID and Social Security / ITIN for each household member\n"
                "- Last 6–8 weeks of pay stubs, or an employer letter; self-employed: tax returns + profit & loss\n"
                "- Most recent federal tax return(s)\n"
                "- Bank statements (usually several recent months)\n"
                "- Proof of current address (for community board preference)\n\n"
                "The exact list varies by building; follow the marketing agent's request. "
                "**Applying on Housing Connect is always free.**",
        "source": "Data: NYC Open Data, Advertised Lotteries on Housing Connect (By Lottery / By Building). "
                  "Mini lotteries and Mitchell-Lama lotteries are not included. AMI: HPD {y} table.",
        "note_few": "Very few units in your band ({n})", "note_small": "Small number of units in your band ({n})",
        "note_many": "{n} units in your band", "note_tail": "; lotteries often draw far more applicants than units.",
        "not_listed": "share not listed; check the ad",
    },
    "zh": {
        "page": "纽约保障房抽签匹配",
        "title": "🏠 纽约保障房抽签匹配",
        "intro": "免费，只使用公开数据（NYC Open Data + HPD AMI 收入标准）。结果不代表最终资格。"
                 "我们不代你申请，也不预测排号。",
        "household": "家庭信息",
        "size": "家庭人数",
        "income": "家庭年收入总额（美元）",
        "units": "户型（不选则按家庭人数大致推荐）",
        "boroughs": "区",
        "zip": "现住址邮编（用于判断本区居民优先）",
        "flags": "适用于你家的情况",
        "senior": "家里有 62 岁以上的成员",
        "history": "同时显示已结束的抽签",
        "m_ami": "占 AMI 百分比", "m_band": "收入档", "m_open": "现在可报名", "m_count": "匹配数量",
        "near": "你接近收入档的分界线，**{b}** 的单元也可能适合你。请查看每个抽签广告的具体收入范围。",
        "guess": "未选择户型，按家庭人数大致推荐：{u}。每个广告对家庭人数有各自的要求。",
        "cb": "邮编 {z} → 大概率属于社区委员会 {cb}（根据楼盘数据推测）。",
        "above": "收入高于 AMI 的 165%，这个收入档的抽签单元非常少。",
        "none": "没有符合条件的抽签。可以多选几个户型或区，或勾选显示已结束的抽签。",
        "cols": {"Lottery Name": "抽签项目", "Borough": "区", "Community Board": "社区委员会",
                 "Development Type": "类型", "start": "开始", "end": "截止", "open_now": "可报名",
                 "Unit Count": "总单元", "units_in_band": "你这一档的单元",
                 "units_your_size": "你这个户型的单元（所有档）",
                 "your_preferences": "可能适用的优先", "competition_note": "说明"},
        "docs_h": "提前准备的材料",
        "docs": "- 每位家庭成员的带照片证件，以及社安号（SSN）或 ITIN\n"
                "- 最近 6–8 周的工资单，或雇主证明信；自雇者：报税表 + 损益表\n"
                "- 最近一年的联邦报税表\n"
                "- 银行流水（通常需要最近几个月）\n"
                "- 现住址证明（申请本区居民优先时需要）\n\n"
                "具体材料以每个楼盘的要求为准，请按管理方的通知准备。"
                "**在 Housing Connect 上申请永远是免费的。**",
        "source": "数据来源：NYC Open Data「Advertised Lotteries on Housing Connect」（按抽签 / 按楼盘）。"
                  "不包含 mini lottery 和 Mitchell-Lama 抽签。AMI：HPD {y} 年标准。",
        "note_few": "你这一档的单元很少（{n} 套）", "note_small": "你这一档的单元不多（{n} 套）",
        "note_many": "你这一档有 {n} 套", "note_tail": "；抽签的申请人数通常远多于单元数。",
        "not_listed": "比例未列出，请看广告",
    },
}
BAND_ZH = {"Extremely Low Income": "极低收入 (Extremely Low)", "Very Low Income": "很低收入 (Very Low)",
           "Low Income": "低收入 (Low)", "Moderate Income": "中等收入 (Moderate)",
           "Middle Income": "中高收入 (Middle)", "Above Middle Income": "高于中高收入 (Above Middle)"}
BOROUGH_ZH = {"MN": "曼哈顿", "BX": "布朗克斯", "BK": "布鲁克林", "QN": "皇后区", "SI": "史坦顿岛"}
UNIT_ZH = {"Studio": "开间 Studio", "1BR": "一室 1BR", "2BR": "两室 2BR", "3BR": "三室 3BR", "4BR+": "四室及以上 4BR+"}
PREF_ZH = {"community_board": "本区居民", "mobility": "行动障碍", "vision_hearing": "视力/听力障碍",
           "municipal_or_veteran": "市政府雇员 / 退伍军人", "nycha": "NYCHA 住户", "senior": "62 岁以上老人"}
DEV_ZH = {"Rental": "出租", "Owner": "产权购买"}


# ---------- language: URL ?lang= > saved choice > browser language ----------
def browser_lang() -> str:
    loc = ""
    try:
        loc = getattr(st.context, "locale", None) or ""
        if not loc:
            loc = st.context.headers.get("Accept-Language", "")
    except Exception:
        pass
    return "zh" if loc.lower().startswith("zh") else "en"


st.set_page_config(page_title="NYC Housing Lottery Matcher · 纽约保障房抽签匹配", page_icon="🏠", layout="wide")

if "lang" not in st.session_state:
    q = st.query_params.get("lang", "")
    st.session_state.lang = q if q in ("en", "zh") else browser_lang()

head, switch = st.columns([5, 1])
with switch:
    pick = st.segmented_control("Language", ["EN", "中文"], default="中文" if st.session_state.lang == "zh" else "EN",
                                label_visibility="collapsed", key="lang_pick")
    if pick:
        new = "zh" if pick == "中文" else "en"
        if new != st.session_state.lang:
            st.session_state.lang = new
            st.query_params["lang"] = new
            st.rerun()
L = st.session_state.lang
t = T[L]
zh = L == "zh"


def band_name(b): return BAND_ZH.get(b, b) if zh else b
def borough_name(b): return BOROUGH_ZH.get(b, m.BOROUGHS.get(b, b)) if zh else m.BOROUGHS.get(b, b)
def unit_name(u): return UNIT_ZH.get(u, u) if zh else u
def pref_name(k): return PREF_ZH.get(k, m.PREF_LABELS[k]) if zh else m.PREF_LABELS[k]


@st.cache_data
def lotteries():
    return m.load_lotteries()


with head:
    st.title(t["title"])
    st.caption(t["intro"])

with st.sidebar:
    st.header(t["household"])
    size = st.number_input(t["size"], 1, 12, 2, key="size")
    income = st.number_input(t["income"], 0, 1_000_000, 70_000, step=1_000, key="income")
    units = st.multiselect(t["units"], list(m.UNIT_COLS), format_func=unit_name, key="units")
    boroughs = st.multiselect(t["boroughs"], list(m.BOROUGHS), format_func=borough_name, key="boroughs")
    zip_code = st.text_input(t["zip"], key="zip")
    flags = st.multiselect(t["flags"], [k for k in m.PREFS if k not in ("community_board", "senior")],
                           format_func=pref_name, key="flags")
    has_senior = st.checkbox(t["senior"], key="senior")
    history = st.checkbox(t["history"], value=True, key="history")

cb = None
if zip_code.strip().isdigit() and len(zip_code.strip()) == 5:
    cb = m.zip_to_community_board(zip_code.strip())

hh = m.Household(int(size), float(income), units, boroughs, cb,
                 flags + (["senior"] if has_senior else []), has_senior)
r = m.match(lotteries(), hh, today=date.today(), include_history=history)
tbl = r["matches"]

c1, c2, c3, c4 = st.columns(4)
c1.metric(t["m_ami"], f"{r['ami_percent']}%")
c2.metric(t["m_band"], band_name(r["band"]) if zh else r["band"].replace(" Income", ""))
c3.metric(t["m_open"], int(tbl["open_now"].sum()) if len(tbl) else 0)
c4.metric(t["m_count"], len(tbl))

if r["near_band"]:
    st.info(t["near"].format(b=band_name(r["near_band"])))
if r["units_guessed"]:
    st.caption(t["guess"].format(u=", ".join(unit_name(u) for u in r["units_considered"])))
if cb:
    st.caption(t["cb"].format(z=zip_code, cb=cb))
if r["band"] == m.ABOVE:
    st.warning(t["above"])

if not len(tbl):
    st.write(t["none"])
else:
    show = tbl.copy()

    def note(n):
        n = int(n)
        key = "note_few" if n <= 3 else "note_small" if n <= 15 else "note_many"
        return t[key].format(n=n) + t["note_tail"]

    def prefs_local(s):
        if not s:
            return ""
        out = []
        for part in s.split("; "):
            for k, en in m.PREF_LABELS.items():
                if part.startswith(en):
                    rest = part[len(en):].replace("share not listed; check ad", t["not_listed"])
                    out.append(pref_name(k) + rest)
                    break
            else:
                out.append(part)
        return "；".join(out) if zh else "; ".join(out)

    show["competition_note"] = show["units_in_band"].apply(note)
    show["your_preferences"] = show["your_preferences"].apply(prefs_local)
    show["Borough"] = show["Borough"].apply(borough_name)
    if zh:
        show["Development Type"] = show["Development Type"].map(DEV_ZH).fillna(show["Development Type"])
    show = show.drop(columns=["Lottery ID"]).rename(columns=t["cols"])
    st.dataframe(show, width="stretch", hide_index=True)

st.subheader(t["docs_h"])
st.markdown(t["docs"])
st.caption(t["source"].format(y=m.AMI_YEAR))
