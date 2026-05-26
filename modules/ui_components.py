from typing import List, Optional
import streamlit as st

# ─────────────────────────────────────────────
#  Design Tokens
# ─────────────────────────────────────────────
# bg:       #f9f5f0   warm off-white page
# surface:  #ffffff   cards
# border:   #edddd0
# orange:   #f97316
# dark:     #1a1613   topbar / headings
# text:     #3a2e26
# muted:    #9b8679
# green:    #16a34a
# red:      #dc2626

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Global ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #3a2e26 !important;
}
.stApp, .main, section.main > div {
    background: linear-gradient(155deg, #fdf9f4 0%, #faf4ec 50%, #f8f0e6 100%) !important;
}
#MainMenu, footer, header, .stDeployButton,
div[data-testid="stDecoration"],
section[data-testid="stSidebar"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #ddd0c4; border-radius: 2px; }
::-webkit-scrollbar-track { background: transparent; }

/* ── Primary button ── */
button[data-testid="baseButton-primary"], button[kind="primary"] {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
    border: none !important; color: #fff !important;
    font-weight: 800 !important; font-size: .95rem !important;
    border-radius: 14px !important; min-height: 3rem !important;
    letter-spacing: .01em !important;
    box-shadow: 0 4px 16px rgba(249,115,22,.35), 0 1px 3px rgba(0,0,0,.12) !important;
    transition: all .2s cubic-bezier(.4,0,.2,1) !important;
}
button[data-testid="baseButton-primary"]:hover, button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(249,115,22,.45), 0 2px 6px rgba(0,0,0,.15) !important;
}
button[data-testid="baseButton-primary"]:active, button[kind="primary"]:active {
    transform: translateY(0) !important;
}

/* ── Secondary button ── */
button[data-testid="baseButton-secondary"] {
    border: 1.5px solid #edddd0 !important; color: #f97316 !important;
    background: #fff !important; border-radius: 14px !important;
    font-weight: 700 !important; min-height: 2.6rem !important;
    font-size: .88rem !important;
    transition: all .15s !important;
}
button[data-testid="baseButton-secondary"]:hover {
    border-color: #f97316 !important;
    background: #fff7ed !important;
}

/* ── All buttons ── */
.stButton > button {
    border-radius: 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    min-height: 2.6rem !important;
    transition: all .15s ease !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 12px !important; border: 1.5px solid #edddd0 !important;
    background: #ffffff !important; color: #1a1613 !important;
    font-family: 'Inter', sans-serif !important; font-size: .95rem !important;
    padding: .65rem .9rem !important;
    transition: border-color .15s, box-shadow .15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 4px rgba(249,115,22,.12) !important;
}

/* ── Number inputs (score entry) ── */
.stNumberInput > div > div > input {
    text-align: center !important; font-size: 1.8rem !important;
    font-weight: 900 !important; color: #1a1613 !important;
    border-radius: 14px !important; border: 2px solid #edddd0 !important;
    background: #fff !important; min-height: 3.5rem !important;
    transition: border-color .15s !important;
}
.stNumberInput > div > div > input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 4px rgba(249,115,22,.12) !important;
}
/* Number input stepper buttons */
.stNumberInput button {
    border-radius: 8px !important; min-height: 1.8rem !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    border-radius: 12px !important; border: 1.5px solid #edddd0 !important;
    background: #ffffff !important; min-height: 2.8rem !important;
}

/* ── Multiselect ── */
.stMultiSelect > div > div {
    border-radius: 12px !important; border: 1.5px solid #edddd0 !important;
    background: #ffffff !important; min-height: 2.8rem !important;
}
/* Multiselect pills (tags) */
[data-baseweb="tag"] {
    background: #fff7ed !important; border: 1px solid #fcd9aa !important;
    border-radius: 20px !important; color: #c2410c !important;
    font-weight: 600 !important;
}

/* ── Radio buttons ── */
.stRadio [role="radiogroup"] { gap: .5rem !important; }
.stRadio label {
    background: #ffffff !important;
    border: 1.5px solid #edddd0 !important;
    border-radius: 12px !important; padding: .6rem 1rem !important;
    cursor: pointer !important; font-weight: 600 !important;
    font-size: .88rem !important; transition: all .15s !important;
    color: #3a2e26 !important;
}
.stRadio label:has(input:checked) {
    border-color: #f97316 !important; background: #fff7ed !important;
    color: #c2410c !important;
}

/* ── Checkbox ── */
.stCheckbox label { font-weight: 600 !important; font-size: .88rem !important; cursor: pointer !important; }

/* ── Form ── */
[data-testid="stForm"] {
    background: #ffffff !important; border: 1.5px solid #edddd0 !important;
    border-radius: 18px !important; padding: 1.3rem !important;
    box-shadow: 0 2px 16px rgba(0,0,0,.06) !important;
}

/* ── Card ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 20px !important; border: 1.5px solid #edddd0 !important;
    background: #ffffff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.06), 0 8px 24px rgba(0,0,0,.07) !important;
    transition: box-shadow .2s !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div { padding: .35rem !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f2e8df !important; border-radius: 12px !important;
    padding: 4px !important; gap: 3px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: .82rem !important; color: #9b8679 !important;
    min-height: 2.4rem !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #f97316 !important; color: #ffffff !important;
    font-weight: 700 !important; box-shadow: 0 2px 8px rgba(249,115,22,.3) !important;
}

/* ── Dark button (used in history cards) ── */
.btn-dark-wrap > div > button,
.btn-dark-wrap > div > div > button {
    background: #1a1613 !important; color: #ffffff !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 700 !important;
}
.btn-dark-wrap > div > button:hover,
.btn-dark-wrap > div > div > button:hover {
    background: #2c2420 !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.25) !important;
    transform: translateY(-1px) !important;
}

/* ── Progress ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #f97316, #fb923c) !important;
    border-radius: 100px !important;
}

/* ── Metric ── */
[data-testid="metric-container"] {
    background: #fff !important; border: 1.5px solid #edddd0 !important;
    border-radius: 14px !important; padding: .8rem !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* ── Divider ── */
hr { border-color: #edddd0 !important; }

/* ── Widget labels ── */
label[data-testid="stWidgetLabel"] > div > p {
    font-weight: 700 !important; font-size: .72rem !important;
    text-transform: uppercase !important; letter-spacing: .09em !important;
    color: #9b8679 !important;
}
/* ── Caption ── */
.stCaption { color: #9b8679 !important; font-size: .75rem !important; }

/* ── Expander (default) ── */
details { background: #fff !important; border: 1.5px solid #edddd0 !important; border-radius: 14px !important; }

/* ── Tournament banner expander (styled dark card) ── */
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] details {
    background: linear-gradient(135deg, #1a1613 0%, #2c2420 55%, #3d3330 100%) !important;
    border: none !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,.20), 0 1px 4px rgba(0,0,0,.12) !important;
    overflow: hidden !important;
    margin-bottom: .5rem !important;
}
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] summary {
    padding: 1.1rem 1.5rem !important;
    min-height: 68px !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] summary:hover {
    background: rgba(255,255,255,.04) !important;
}
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] summary p,
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] summary span:not([data-testid]) {
    color: #fff !important;
    font-weight: 800 !important;
    font-size: .93rem !important;
    letter-spacing: -.01em !important;
}
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {
    color: rgba(255,255,255,.45) !important;
}
[data-testid="stMarkdownContainer"]:has(.bf-tourn-exp-marker) ~ [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] svg {
    fill: rgba(255,255,255,.45) !important;
}

/* ── Container (border=True) accent left border ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    position: relative !important;
}
/* First container on page gets orange left strip via pseudo-element would require JS;
   instead we add a subtle top-border highlight */
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,.10), 0 8px 28px rgba(0,0,0,.08) !important;
}

/* ── Spacing helpers ── */
.block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; }
</style>
"""

_COMPONENT_CSS = """
<style>

/* ════════════════════════════════════════════
   TOP BAR
════════════════════════════════════════════ */
.bf-topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, #1a1613 0%, #2c2420 100%);
    border-radius: 20px; padding: .85rem 1.4rem; margin-bottom: 1.2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.22), 0 1px 4px rgba(0,0,0,.1);
}
.bf-topbar-left { display: flex; align-items: center; gap: .75rem; }
.bf-topbar-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #f97316, #ea580c);
    border-radius: 12px; display: flex; align-items: center;
    justify-content: center; font-size: 1.25rem;
    box-shadow: 0 4px 12px rgba(249,115,22,.45);
    flex-shrink: 0;
}
.bf-topbar-name { font-size: 1.05rem; font-weight: 900; color: #fff; letter-spacing: -.02em; line-height: 1.2; }
.bf-topbar-role { font-size: .68rem; color: rgba(255,255,255,.45); font-weight: 500; letter-spacing: .03em; }
.bf-topbar-badge {
    background: rgba(249,115,22,.2); border: 1px solid rgba(249,115,22,.3);
    color: #fb923c; border-radius: 100px; padding: .24rem .85rem;
    font-size: .73rem; font-weight: 700; white-space: nowrap;
}

/* ════════════════════════════════════════════
   LOGIN
════════════════════════════════════════════ */
.bf-login-header {
    background: linear-gradient(135deg, #1a1613 0%, #2c2420 100%);
    border-radius: 20px 20px 0 0; padding: 1.8rem 1.5rem 1.5rem;
    text-align: center; margin: -.35rem -.35rem 1rem;
}
.bf-login-icon-wrap {
    width: 72px; height: 72px;
    background: linear-gradient(135deg, #f97316, #ea580c);
    border-radius: 20px; margin: 0 auto .9rem;
    display: flex; align-items: center; justify-content: center;
    font-size: 2.2rem; line-height: 1;
    box-shadow: 0 8px 24px rgba(249,115,22,.45);
}
.bf-login-title {
    font-size: 1.75rem; font-weight: 900; color: #fff;
    letter-spacing: -.04em; margin: 0 0 .25rem;
}
.bf-login-sub { font-size: .8rem; color: rgba(255,255,255,.5); font-weight: 500; }

/* ════════════════════════════════════════════
   FIELD LABELS
════════════════════════════════════════════ */
.bf-field-label {
    font-size: .69rem; font-weight: 800; letter-spacing: .1em;
    text-transform: uppercase; color: #9b8679; margin-bottom: .25rem;
}
.bf-hint {
    background: #fff7ed; border: 1px solid #fcd9aa;
    border-radius: 10px; padding: .55rem .9rem;
    font-size: .78rem; color: #c2410c; font-weight: 600;
}

/* ════════════════════════════════════════════
   SECTION LABEL
════════════════════════════════════════════ */
.bf-sec {
    font-size: .64rem; font-weight: 800; letter-spacing: .14em;
    text-transform: uppercase; color: #c09070;
    margin: 1.1rem 0 .5rem;
    display: flex; align-items: center; gap: .5rem;
}
.bf-sec::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, #edddd0, transparent); }

/* ════════════════════════════════════════════
   TOURNAMENT BANNER
════════════════════════════════════════════ */
.bf-banner {
    background: linear-gradient(135deg, #1a1613 0%, #2c2420 55%, #3d3330 100%);
    border-radius: 18px; padding: 1.1rem 1.5rem; margin-bottom: 1rem;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 4px 20px rgba(0,0,0,.18); position: relative; overflow: hidden;
}
.bf-banner::before {
    content: '🎾'; position: absolute; right: 1rem; top: 50%;
    transform: translateY(-50%); font-size: 5rem; opacity: .07; line-height: 1;
}
.bf-banner h2 {
    color: #fff !important; font-size: 1.1rem !important;
    font-weight: 900 !important; margin: 0 0 .15rem !important; letter-spacing: -.03em !important;
}
.bf-banner .meta { color: rgba(255,255,255,.5); font-size: .73rem; }
.bf-banner .badge {
    background: #f97316; border-radius: 100px;
    padding: .3rem .95rem; color: #fff; font-weight: 700; font-size: .75rem;
    white-space: nowrap; box-shadow: 0 2px 10px rgba(249,115,22,.5);
}

/* ════════════════════════════════════════════
   FORMAT DESCRIPTION
════════════════════════════════════════════ */
.bf-fmt-info {
    background: #fff; border: 1.5px solid #edddd0; border-radius: 16px;
    padding: 1rem 1.1rem; margin-top: .5rem;
}
.bf-fmt-info-name {
    font-size: .88rem; font-weight: 800; color: #f97316; margin-bottom: .3rem;
    display: flex; align-items: center; gap: .4rem;
}
.bf-fmt-info-desc { font-size: .78rem; color: #9b8679; line-height: 1.5; }

/* ════════════════════════════════════════════
   RULES CARD
════════════════════════════════════════════ */
.bf-rules {
    background: linear-gradient(135deg, #fff9f2, #fff);
    border: 1.5px solid #fcd9aa; border-radius: 16px; padding: 1rem 1.1rem;
}
.bf-rules-title {
    font-size: .65rem; font-weight: 800; letter-spacing: .14em;
    text-transform: uppercase; color: #f97316; margin-bottom: .6rem;
    display: flex; align-items: center; gap: .4rem;
}
.bf-rule-row {
    display: flex; align-items: flex-start; gap: .5rem;
    padding: .3rem 0; font-size: .79rem; color: #6b4326; line-height: 1.45;
    border-bottom: 1px solid rgba(252,217,170,.35);
}
.bf-rule-row:last-child { border-bottom: none; }
.bf-rule-icon { min-width: 1.2rem; text-align: center; font-size: .85rem; }
.bf-rule-text b { color: #c2410c; font-weight: 700; }

/* ════════════════════════════════════════════
   RANKING TABLE
════════════════════════════════════════════ */
.bf-rank-wrap {
    background: #fff; border-radius: 16px; border: 1.5px solid #edddd0;
    box-shadow: 0 2px 14px rgba(0,0,0,.07); overflow: hidden;
}
.bf-rank-row {
    display: flex; align-items: center;
    padding: .9rem 1.1rem; border-bottom: 1px solid #faf0e6; gap: .8rem;
}
.bf-rank-row:last-child { border-bottom: none; }
.bf-rank-row.p1 { background: linear-gradient(90deg, #fffbea, #fff); }
.bf-rank-row.p3 { background: linear-gradient(90deg, #fff8f5, #fff); }
.bf-rpos { font-size: 1.3rem; min-width: 2rem; text-align: center; }
.bf-rname { flex: 1; font-weight: 700; font-size: .9rem; color: #1a1613; }
.bf-rstats { display: flex; gap: .9rem; }
.bf-stat { text-align: center; min-width: 2.4rem; }
.bf-sv { font-weight: 700; font-size: .9rem; color: #1a1613; line-height: 1.1; }
.bf-sl { font-size: .57rem; color: #c09070; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; margin-top: 2px; }
.bf-pts .bf-sv { font-size: 1.15rem; color: #f97316; font-weight: 900; }

/* ════════════════════════════════════════════
   STATUS & MISC
════════════════════════════════════════════ */
.bf-badge {
    display: inline-flex; align-items: center; gap: .35rem;
    background: linear-gradient(135deg,#f97316,#ea580c);
    color: #fff; border-radius: 100px; padding: .22rem .8rem;
    font-size: .75rem; font-weight: 700;
    box-shadow: 0 2px 8px rgba(249,115,22,.35);
}
.bf-pin-ok { color: #15803d; font-size: .75rem; font-weight: 600; }
.bf-pin-no { color: #dc2626; font-size: .75rem; font-weight: 600; }
.bf-bye {
    background: #fefce8; border: 1px solid #fde047; border-radius: 10px;
    padding: .55rem .9rem; color: #854d0e; font-size: .81rem; margin-bottom: .5rem;
}
.bf-done {
    background: #f0fdf4; border: 1px solid #86efac; border-radius: 14px;
    padding: .9rem; text-align: center; color: #166534;
    font-weight: 700; font-size: .9rem; margin-bottom: .75rem;
}
.bf-champion {
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border: 2px solid #f59e0b; border-radius: 18px;
    padding: 1.3rem 1.5rem; text-align: center;
    font-size: 1.25rem; color: #78350f; font-weight: 800; margin-bottom: 1rem;
    box-shadow: 0 6px 20px rgba(245,158,11,.22);
}

/* ════════════════════════════════════════════
   BRACKET TREE
════════════════════════════════════════════ */
.bf-bracket-match {
    background: #fff; border: 1.5px solid #edddd0;
    border-radius: 12px; padding: .6rem 1rem;
    margin: .3rem 0; font-size: .84rem;
    display: flex; align-items: center; gap: .75rem;
}
.bf-bracket-match.done { border-left: 4px solid #f97316; }
.bf-bscore { font-weight: 900; color: #f97316; min-width: 4rem; text-align: center; font-size: .9rem; }
.bf-bwin { font-weight: 800; color: #f97316; }
.bf-blose { color: #c4a898; }
.bf-tree { display: flex; gap: 1.2rem; overflow-x: auto; padding: .5rem 0; }
.bf-tree-round { min-width: 160px; }
.bf-tree-rname { font-size: .62rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: #f97316; margin-bottom: .6rem; }
.bf-tree-match { background: #fff; border: 1.5px solid #edddd0; border-radius: 10px; padding: .45rem .75rem; margin-bottom: .85rem; }
.bf-tree-p { font-size: .8rem; padding: .2rem 0; color: #888; border-bottom: 1px solid #faf0e6; }
.bf-tree-p:last-child { border-bottom: none; }
.bf-tree-p.w { font-weight: 800; color: #f97316; }

/* ════════════════════════════════════════════
   MATCH DISPLAY
════════════════════════════════════════════ */
.bf-match-lbl {
    font-size: .64rem; font-weight: 800; letter-spacing: .12em;
    text-transform: uppercase; color: #c4a898; margin: .9rem 0 .3rem;
}
.bf-team { font-size: .9rem; font-weight: 700; color: #1a1613; line-height: 1.65; }

/* ════════════════════════════════════════════
   HERO
════════════════════════════════════════════ */
.bf-hero { text-align: center; padding: 1.5rem 1rem .6rem; }
.bf-hero-icon { font-size: 2.5rem; line-height: 1; margin-bottom: .25rem; }
.bf-hero-title { font-size: 2rem; font-weight: 900; color: #1a1613; letter-spacing: -.04em; margin: 0; }
.bf-hero-sub { color: #9b8679; font-size: .83rem; margin-top: .3rem; font-weight: 500; }

/* ════════════════════════════════════════════
   STAT PILL (inline stat badge)
════════════════════════════════════════════ */
.bf-stat-pill {
    display: inline-flex; align-items: center; gap: .35rem;
    background: #fff; border: 1.5px solid #edddd0;
    border-radius: 100px; padding: .3rem .8rem;
    font-size: .78rem; font-weight: 700; color: #3a2e26;
}
.bf-stat-pill span { color: #f97316; font-weight: 900; }
</style>
"""


def apply_custom_css() -> None:
    st.markdown(_CSS + _COMPONENT_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Components
# ─────────────────────────────────────────────

def topbar(badge: str = "") -> None:
    badge_html = f'<div class="bf-topbar-badge">{badge}</div>' if badge else ""
    st.markdown(
        f'<div class="bf-topbar">'
        f'  <div class="bf-topbar-left">'
        f'    <div class="bf-topbar-icon">🏖️</div>'
        f'    <div>'
        f'      <div class="bf-topbar-name">Beach&Friends</div>'
        f'      <div class="bf-topbar-role">Placar & Chaveamento</div>'
        f'    </div>'
        f'  </div>'
        f'  {badge_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def login_header() -> None:
    st.markdown(
        '<div class="bf-login-header">'
        '  <div class="bf-login-icon-wrap">🏖️</div>'
        '  <div class="bf-login-title">Beach&Friends</div>'
        '  <div class="bf-login-sub">Placar & Chaveamento Inteligente</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# kept for backward compat
def logo_header(title: str = "Beach&Friends", subtitle: str = "") -> None:
    login_header()


def hero(title: str, sub: str, icon: str = "🏖️") -> None:
    st.markdown(
        f'<div class="bf-hero">'
        f'<div class="bf-hero-icon">{icon}</div>'
        f'<div class="bf-hero-title">{title}</div>'
        f'<div class="bf-hero-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def field_label(text: str) -> None:
    st.markdown(f'<div class="bf-field-label">{text}</div>', unsafe_allow_html=True)


def section_label(text: str) -> None:
    st.markdown(f'<div class="bf-sec">{text}</div>', unsafe_allow_html=True)


def match_card_label(n: int) -> None:
    st.markdown(f'<div class="bf-match-lbl">Partida {n}</div>', unsafe_allow_html=True)


def bye_notice(players: list) -> None:
    st.markdown(
        f'<div class="bf-bye">⏸ Descansando nesta rodada: <b>{", ".join(players)}</b></div>',
        unsafe_allow_html=True,
    )


def round_done_banner(text: str = "✅ Resultados registrados!") -> None:
    st.markdown(f'<div class="bf-done">{text}</div>', unsafe_allow_html=True)


def render_banner(name: str, n: int, idx: int, total: int) -> None:
    finished = idx >= total
    badge = "Encerrado 🏁" if finished else f"Rodada {idx + 1} de {total}"
    st.markdown(
        f'<div class="bf-banner">'
        f'<div><h2>🎾 {name}</h2>'
        f'<div class="meta">{n} participantes · {total} rodada{"s" if total != 1 else ""}</div></div>'
        f'<div class="badge">{badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_format_info(icon: str, name: str, desc: str) -> None:
    st.markdown(
        f'<div class="bf-fmt-info">'
        f'  <div class="bf-fmt-info-name">{icon} {name}</div>'
        f'  <div class="bf-fmt-info-desc">{desc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_rules_card(rules: list) -> None:
    if not rules:
        return
    rows = "".join(
        f'<div class="bf-rule-row">'
        f'  <div class="bf-rule-icon">{icon}</div>'
        f'  <div class="bf-rule-text">{text}</div>'
        f'</div>'
        for icon, text in rules
    )
    st.markdown(
        f'<div class="bf-rules">'
        f'  <div class="bf-rules-title">📋 REGRAS DA PARTIDA</div>'
        f'  {rows}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_ranking_section(ranking, mode: str = "individual") -> None:
    section_label("Classificação")
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}
    row_cls = {1: "p1", 2: "p2", 3: "p3"}
    rows = ""
    for pos, name, s in ranking:
        icon = medal.get(pos, str(pos))
        cls = row_cls.get(pos, "")
        bal = s["game_balance"]
        bal_str = f"+{bal}" if bal > 0 else str(bal)
        bal_col = "#16a34a" if bal > 0 else "#dc2626" if bal < 0 else "#888"
        rows += f"""
        <div class="bf-rank-row {cls}">
          <div class="bf-rpos">{icon}</div>
          <div class="bf-rname">{name}</div>
          <div class="bf-rstats">
            <div class="bf-stat bf-pts">
              <div class="bf-sv">{s['points']}</div><div class="bf-sl">Pts</div>
            </div>
            <div class="bf-stat">
              <div class="bf-sv">{s['matches']}</div><div class="bf-sl">J</div>
            </div>
            <div class="bf-stat">
              <div class="bf-sv">{s['wins']}</div><div class="bf-sl">V</div>
            </div>
            <div class="bf-stat">
              <div class="bf-sv" style="color:{bal_col}">{bal_str}</div><div class="bf-sl">Saldo</div>
            </div>
            <div class="bf-stat">
              <div class="bf-sv">{s['games_pro']}</div><div class="bf-sl">Pró</div>
            </div>
          </div>
        </div>"""
    st.markdown(f'<div class="bf-rank-wrap">{rows}</div>', unsafe_allow_html=True)
    st.caption("Desempate: Pontos → Saldo de Games → Games Pró → Alfabético")


def render_history_match(ta, tb, result, score) -> None:
    ta_str = f"{ta[0]} & {ta[1]}" if isinstance(ta, tuple) else str(ta)
    tb_str = f"{tb[0]} & {tb[1]}" if isinstance(tb, tuple) else str(tb)
    aw = "font-weight:800;color:#f97316" if result.winner == "A" else "color:#c4a898"
    bw = "font-weight:800;color:#f97316" if result.winner == "B" else "color:#c4a898"
    sc = f"{score.games_a} × {score.games_b}"
    if result.is_super_tie:
        sc += " <sup style='color:#f97316;font-size:.7rem'>S.T.</sup>"
    c1, c2, c3 = st.columns([3, 1, 3])
    with c1:
        st.markdown(f"<span style='{aw}'>{ta_str}</span>", unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<div style='text-align:center;font-weight:800;color:#3a2e26'>{sc}</div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div style='text-align:right'><span style='{bw}'>{tb_str}</span></div>",
            unsafe_allow_html=True,
        )
