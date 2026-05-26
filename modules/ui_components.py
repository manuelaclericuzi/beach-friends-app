from typing import List, Optional
import streamlit as st

# ─────────────────────────────────────────────
#  CSS — reliable selectors for Streamlit 1.56
# ─────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Global ── */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, sans-serif !important;
}
.stApp, .main, section.main > div {
    background-color: #fef9f4 !important;
}
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* ── Hide sidebar ── */
section[data-testid="stSidebar"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #fef9f4; }
::-webkit-scrollbar-thumb { background: #f0d4b8; border-radius: 3px; }

/* ── Primary button — orange gradient ── */
button[data-testid="baseButton-primary"],
button[kind="primary"] {
    background: linear-gradient(135deg, #f97316 0%, #fbbf24 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: .9rem !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(249,115,22,.35) !important;
    transition: all .2s !important;
}
button[data-testid="baseButton-primary"]:hover,
button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(249,115,22,.45) !important;
}

/* ── Secondary button ── */
button[data-testid="baseButton-secondary"] {
    border: 1.5px solid #f0d4b8 !important;
    color: #f97316 !important;
    background: transparent !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}

/* ── All buttons radius ── */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 12px !important;
    border: 1.5px solid #f0d4b8 !important;
    background: #ffffff !important;
    color: #1a1a1a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: .9rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249,115,22,.15) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    border-radius: 12px !important;
    border: 1.5px solid #f0d4b8 !important;
    background: #ffffff !important;
}

/* ── Number input ── */
.stNumberInput > div > div > input {
    text-align: center !important;
    font-size: 1.4rem !important;
    font-weight: 800 !important;
    color: #1a1a1a !important;
    border-radius: 10px !important;
    border: 1.5px solid #f0d4b8 !important;
    background: #fff !important;
}

/* ── Form container ── */
[data-testid="stForm"] {
    background: #ffffff !important;
    border: 1.5px solid #f0e4d0 !important;
    border-radius: 18px !important;
    padding: 1.5rem !important;
    box-shadow: 0 2px 12px rgba(200,100,20,.07) !important;
}

/* ── Bordered container (card) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 22px !important;
    border: 1.5px solid #f0e4d0 !important;
    background: #ffffff !important;
    box-shadow: 0 12px 40px rgba(200,100,30,.10) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.5rem 0.5rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #fff3e8 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid #f0d4b8 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: .83rem !important;
    color: #c2773d !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #ffffff !important;
    color: #f97316 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #f97316, #fbbf24) !important;
    border-radius: 100px !important;
}

/* ── Expander ── */
details {
    background: #fff !important;
    border: 1px solid #f0e4d0 !important;
    border-radius: 12px !important;
}

/* ── Divider ── */
hr {
    border-color: #f0e4d0 !important;
    margin: 1rem 0 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* ── Labels ── */
label[data-testid="stWidgetLabel"] > div > p {
    font-weight: 700 !important;
    font-size: .75rem !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
    color: #c49070 !important;
}

/* ── Metric ── */
[data-testid="metric-container"] {
    background: #fff !important;
    border: 1px solid #f0e4d0 !important;
    border-radius: 14px !important;
    padding: .75rem 1rem .5rem !important;
}

/* ── Caption ── */
.stCaption {
    color: #c49070 !important;
    font-size: .75rem !important;
}
</style>
"""

# ─────────────────────────────────────────────
#  Custom HTML components
# ─────────────────────────────────────────────

_COMPONENT_CSS = """
<style>
/* ── Login card inner ── */
.bf-logo {
    width: 72px; height: 72px;
    background: linear-gradient(135deg,#f97316,#fbbf24);
    border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 1.1rem;
    font-size: 2.2rem; line-height: 72px; text-align: center;
    box-shadow: 0 8px 24px rgba(249,115,22,.40);
}
.bf-title {
    text-align: center;
    font-size: 2rem; font-weight: 900;
    color: #1a1a1a; letter-spacing: -.04em;
    margin: 0 0 .25rem;
}
.bf-sub {
    text-align: center;
    font-size: .85rem; color: #c49070;
    margin: 0 0 2rem; font-weight: 500;
}
.bf-field-label {
    font-size: .7rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase;
    color: #c49070; margin-bottom: .2rem;
}
.bf-hint {
    background: #fff7ed; border: 1px solid #fcd9aa;
    border-radius: 10px; padding: .6rem .9rem;
    font-size: .8rem; color: #c2410c; font-weight: 500;
    margin: .5rem 0;
}

/* ── Tournament banner ── */
.bf-banner {
    background: linear-gradient(135deg,#f97316 0%,#fb923c 55%,#fbbf24 100%);
    border-radius: 18px; padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 6px 24px rgba(249,115,22,.28);
}
.bf-banner h2 {
    color: #fff !important; font-size: 1.25rem !important;
    font-weight: 900 !important; margin: 0 !important; letter-spacing: -.03em;
}
.bf-banner .meta { color: rgba(255,255,255,.75); font-size: .78rem; margin-top:.2rem; }
.bf-banner .badge {
    background: rgba(255,255,255,.22); border-radius: 100px;
    padding: .4rem 1.1rem; color:#fff; font-weight:700; font-size:.82rem;
    white-space:nowrap;
}

/* ── Section label ── */
.bf-sec {
    font-size: .68rem; font-weight: 800;
    letter-spacing: .12em; text-transform: uppercase;
    color: #d4956a; margin: 1.2rem 0 .5rem;
}

/* ── Match label ── */
.bf-match-lbl {
    font-size: .68rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase;
    color: #d4b89a; margin: .9rem 0 .4rem;
}

/* ── Team label ── */
.bf-team {
    font-size: .92rem; font-weight: 700;
    color: #1a1a1a; line-height: 1.65;
}

/* ── Bye / done notices ── */
.bf-bye {
    background: #fff7ed; border: 1px solid #fcd9aa;
    border-radius: 10px; padding: .6rem .9rem;
    color: #c2410c; font-size: .83rem; margin-bottom: .75rem;
}
.bf-done {
    background: #f0fdf4; border: 1px solid #86efac;
    border-radius: 12px; padding: 1rem;
    text-align: center; color: #166534;
    font-weight: 700; font-size: .95rem; margin-bottom: 1rem;
}

/* ── Ranking ── */
.bf-rank-wrap {
    background: #fff; border-radius: 16px;
    border: 1.5px solid #f0e4d0;
    box-shadow: 0 2px 12px rgba(200,100,20,.08);
    overflow: hidden; margin-top: .5rem;
}
.bf-rank-row {
    display: flex; align-items: center;
    padding: .85rem 1.1rem;
    border-bottom: 1px solid #fef0e4;
    transition: background .12s;
}
.bf-rank-row:last-child { border-bottom: none; }
.bf-rank-row.p1 { background: linear-gradient(90deg,#fffbeb,#fff); }
.bf-rank-row.p2 { background: #fafafa; }
.bf-rank-row.p3 { background: linear-gradient(90deg,#fff8f5,#fff); }
.bf-rpos { font-size: 1.3rem; min-width: 2.2rem; text-align: center; }
.bf-rname {
    flex: 1; font-weight: 700; font-size: .9rem;
    color: #1a1a1a; margin-left: .7rem;
}
.bf-rstats { display: flex; gap: 1.1rem; align-items: center; }
.bf-stat { text-align: center; }
.bf-sv { font-weight: 700; font-size: .92rem; color: #1a1a1a; line-height: 1; }
.bf-sl {
    font-size: .6rem; color: #d4b89a; font-weight: 700;
    letter-spacing: .07em; text-transform: uppercase; margin-top: 2px;
}
.bf-pts .bf-sv { font-size: 1.1rem; color: #f97316; font-weight: 900; }

/* ── Admin badge ── */
.bf-badge {
    display: inline-flex; align-items: center; gap: .4rem;
    background: linear-gradient(135deg,#f97316,#fbbf24);
    color: #fff; border-radius: 100px;
    padding: .25rem .85rem; font-size: .78rem; font-weight: 700;
    box-shadow: 0 2px 8px rgba(249,115,22,.3);
}

/* ── Player cards (admin panel) ── */
.bf-player-row {
    display: flex; align-items: center; justify-content: space-between;
    background: #fff; border: 1.5px solid #f0e4d0;
    border-radius: 12px; padding: .7rem 1rem; margin-bottom: .4rem;
}
.bf-pin-ok { color: #16a34a; font-size: .78rem; font-weight: 700; }
.bf-pin-no { color: #f97316; font-size: .78rem; font-weight: 700; }

/* ── Champion ── */
.bf-champion {
    background: linear-gradient(135deg,#fef3c7,#fde68a);
    border: 2px solid #f59e0b; border-radius: 16px;
    padding: 1.1rem 1.5rem; text-align: center;
    font-size: 1.2rem; color: #92400e; font-weight: 700;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 16px rgba(245,158,11,.2);
}

/* ── Bracket ── */
.bf-bracket-match {
    display: flex; align-items: center; gap: .75rem;
    background: #fff; border: 1.5px solid #f0e4d0;
    border-radius: 12px; padding: .7rem 1rem;
    margin: .3rem 0; font-size: .88rem;
}
.bf-bracket-match.done { border-left: 4px solid #f97316; }
.bf-bscore {
    font-weight: 900; color: #f97316;
    min-width: 4.5rem; text-align: center; font-size: .95rem;
}
.bf-bwin { font-weight: 800; color: #f97316; }
.bf-blose { color: #c4a898; }

/* ── Bracket tree ── */
.bf-tree { display: flex; gap: 1.5rem; overflow-x: auto; padding: 1rem 0; }
.bf-tree-round { min-width: 170px; }
.bf-tree-rname {
    font-size: .65rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase;
    color: #f97316; margin-bottom: .75rem;
}
.bf-tree-match {
    background: #fff; border: 1.5px solid #f0e4d0;
    border-radius: 12px; padding: .5rem .8rem; margin-bottom: 1rem;
}
.bf-tree-p {
    font-size: .83rem; padding: .22rem 0;
    color: #888; border-bottom: 1px solid #fef0e4;
}
.bf-tree-p:last-child { border-bottom: none; }
.bf-tree-p.w { font-weight: 800; color: #f97316; }

/* ── App hero ── */
.bf-hero {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
}
.bf-hero-icon { font-size: 3rem; line-height: 1; margin-bottom: .3rem; }
.bf-hero-title {
    font-size: 2.4rem; font-weight: 900;
    color: #1a1a1a; letter-spacing: -.04em; margin: 0;
}
.bf-hero-sub { color: #c49070; font-size: .9rem; margin-top: .3rem; font-weight: 500; }
</style>
"""


def apply_custom_css() -> None:
    st.markdown(_CSS + _COMPONENT_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def logo_header(title: str = "Beach&Friends", subtitle: str = "Placar & Chaveamento Inteligente") -> None:
    st.markdown(
        f'<div class="bf-logo">🏖️</div>'
        f'<div class="bf-title">{title}</div>'
        f'<div class="bf-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )


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


def round_done_banner(text: str = "✅ Resultados registrados com sucesso!") -> None:
    st.markdown(f'<div class="bf-done">{text}</div>', unsafe_allow_html=True)


def render_banner(name: str, n: int, idx: int, total: int) -> None:
    finished = idx >= total
    badge = "Encerrado 🏁" if finished else f"Rodada {idx + 1} / {total}"
    st.markdown(
        f'<div class="bf-banner">'
        f'<div><h2>🎾 {name}</h2>'
        f'<div class="meta">{n} participantes · {total} rodadas</div></div>'
        f'<div class="badge">{badge}</div>'
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
        bal_col = "#16a34a" if bal > 0 else "#dc2626" if bal < 0 else "#999"
        rows += f"""
        <div class="bf-rank-row {cls}">
            <div class="bf-rpos">{icon}</div>
            <div class="bf-rname">{name}</div>
            <div class="bf-rstats">
                <div class="bf-stat bf-pts">
                    <div class="bf-sv">{s['points']}</div>
                    <div class="bf-sl">Pts</div>
                </div>
                <div class="bf-stat">
                    <div class="bf-sv">{s['matches']}</div>
                    <div class="bf-sl">J</div>
                </div>
                <div class="bf-stat">
                    <div class="bf-sv">{s['wins']}</div>
                    <div class="bf-sl">V</div>
                </div>
                <div class="bf-stat">
                    <div class="bf-sv" style="color:{bal_col}">{bal_str}</div>
                    <div class="bf-sl">Saldo</div>
                </div>
                <div class="bf-stat">
                    <div class="bf-sv">{s['games_pro']}</div>
                    <div class="bf-sl">Pró</div>
                </div>
            </div>
        </div>"""
    st.markdown(f'<div class="bf-rank-wrap">{rows}</div>', unsafe_allow_html=True)
    st.caption("Desempate: Pontos → Saldo de Games → Games Pró → Ordem Alfabética")


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
        st.markdown(f"<div style='text-align:center;font-weight:700;color:#1a1a1a'>{sc}</div>",
                    unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div style='text-align:right'><span style='{bw}'>{tb_str}</span></div>",
                    unsafe_allow_html=True)
