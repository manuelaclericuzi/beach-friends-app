from typing import List, Optional
import streamlit as st

# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, sans-serif !important;
}
.stApp, .main, section.main > div {
    background-color: #faf8f5 !important;
}
#MainMenu, footer, header, .stDeployButton,
div[data-testid="stDecoration"],
section[data-testid="stSidebar"] {
    display: none !important; visibility: hidden !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #ddd0c4; border-radius: 3px; }

/* Primary button */
button[data-testid="baseButton-primary"], button[kind="primary"] {
    background: linear-gradient(135deg, #f97316 0%, #fb923c 100%) !important;
    border: none !important; color: #fff !important;
    font-weight: 700 !important; font-size: .88rem !important;
    border-radius: 10px !important; letter-spacing: .01em !important;
    box-shadow: 0 3px 12px rgba(249,115,22,.30) !important;
    transition: all .18s ease !important;
}
button[data-testid="baseButton-primary"]:hover, button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(249,115,22,.40) !important;
}

/* Secondary button */
button[data-testid="baseButton-secondary"] {
    border: 1.5px solid #e8d5c0 !important;
    color: #f97316 !important; background: #fff !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.stButton > button {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 10px !important; border: 1.5px solid #e8d5c0 !important;
    background: #ffffff !important; color: #1c1917 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249,115,22,.12) !important;
}

/* Number input */
.stNumberInput > div > div > input {
    text-align: center !important; font-size: 1.5rem !important;
    font-weight: 800 !important; color: #1c1917 !important;
    border-radius: 10px !important; border: 1.5px solid #e8d5c0 !important;
    background: #fff !important;
}

/* Selectbox */
.stSelectbox > div > div {
    border-radius: 10px !important; border: 1.5px solid #e8d5c0 !important;
    background: #ffffff !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    border-radius: 10px !important; border: 1.5px solid #e8d5c0 !important;
    background: #ffffff !important;
}

/* Form */
[data-testid="stForm"] {
    background: #ffffff !important; border: 1.5px solid #e8d5c0 !important;
    border-radius: 16px !important; padding: 1.25rem !important;
    box-shadow: 0 2px 16px rgba(0,0,0,.05) !important;
}

/* Card */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important; border: 1.5px solid #e8d5c0 !important;
    background: #ffffff !important;
    box-shadow: 0 4px 20px rgba(0,0,0,.06) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div { padding: 0.4rem !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #f0e8df !important; border-radius: 10px !important;
    padding: 3px !important; gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: .82rem !important; color: #a07050 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #ffffff !important; color: #f97316 !important;
    font-weight: 700 !important; box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
}

/* Checkbox */
.stCheckbox label { font-size: .88rem !important; font-weight: 600 !important; color: #1c1917 !important; }

/* Progress */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #f97316, #fb923c) !important;
    border-radius: 100px !important;
}

/* Alerts */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* Expander */
details { background: #fff !important; border: 1.5px solid #e8d5c0 !important; border-radius: 12px !important; }

/* Divider */
hr { border-color: #e8d5c0 !important; margin: .75rem 0 !important; }

/* Metric */
[data-testid="metric-container"] {
    background: #fff !important; border: 1.5px solid #e8d5c0 !important;
    border-radius: 12px !important; padding: .75rem !important;
}

/* Widget labels */
label[data-testid="stWidgetLabel"] > div > p {
    font-weight: 700 !important; font-size: .72rem !important;
    text-transform: uppercase !important; letter-spacing: .08em !important;
    color: #a07050 !important;
}

/* Caption */
.stCaption { color: #a07050 !important; font-size: .74rem !important; }
</style>
"""

_COMPONENT_CSS = """
<style>

/* ══════════════════════════════════════════
   TOP BAR
══════════════════════════════════════════ */
.bf-topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: linear-gradient(135deg, #1c1917 0%, #292524 100%);
    border-radius: 18px; padding: .9rem 1.5rem; margin-bottom: 1.3rem;
    box-shadow: 0 6px 24px rgba(0,0,0,.22);
}
.bf-topbar-left { display: flex; align-items: center; gap: .8rem; }
.bf-topbar-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #f97316, #fb923c);
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 1.2rem;
    box-shadow: 0 3px 10px rgba(249,115,22,.40);
}
.bf-topbar-name { font-size: 1.05rem; font-weight: 900; color: #fff; letter-spacing: -.02em; }
.bf-topbar-sub { font-size: .68rem; color: rgba(255,255,255,.45); font-weight: 500; }
.bf-topbar-badge {
    background: rgba(249,115,22,.2); border: 1px solid rgba(249,115,22,.35);
    color: #fb923c; border-radius: 100px; padding: .25rem .9rem;
    font-size: .73rem; font-weight: 700;
}

/* ══════════════════════════════════════════
   LOGIN
══════════════════════════════════════════ */
.bf-logo {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, #f97316, #fbbf24);
    border-radius: 24px; display: flex; align-items: center;
    justify-content: center; margin: 0 auto 1.2rem;
    font-size: 2.4rem; line-height: 1;
    box-shadow: 0 12px 32px rgba(249,115,22,.38);
}
.bf-title {
    text-align: center; font-size: 1.9rem; font-weight: 900;
    color: #1c1917; letter-spacing: -.04em; margin: 0 0 .2rem;
}
.bf-sub {
    text-align: center; font-size: .82rem; color: #a07050;
    margin: 0 0 1.8rem; font-weight: 500;
}
.bf-field-label {
    font-size: .69rem; font-weight: 800; letter-spacing: .1em;
    text-transform: uppercase; color: #a07050; margin-bottom: .2rem;
}
.bf-hint {
    background: #fff7ed; border: 1px solid #fcd9aa;
    border-radius: 8px; padding: .55rem .85rem;
    font-size: .78rem; color: #c2410c; font-weight: 500; margin: .4rem 0;
}

/* ══════════════════════════════════════════
   SECTION LABEL
══════════════════════════════════════════ */
.bf-sec {
    font-size: .65rem; font-weight: 800; letter-spacing: .14em;
    text-transform: uppercase; color: #c09070;
    margin: 1.1rem 0 .55rem;
    display: flex; align-items: center; gap: .6rem;
}
.bf-sec::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, #e8d5c0, transparent);
}

/* ══════════════════════════════════════════
   TOURNAMENT BANNER (dentro do torneio ativo)
══════════════════════════════════════════ */
.bf-banner {
    background: linear-gradient(135deg, #1c1917 0%, #292524 55%, #44403c 100%);
    border-radius: 16px; padding: 1.1rem 1.5rem; margin-bottom: 1rem;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 4px 20px rgba(0,0,0,.16); position: relative; overflow: hidden;
}
.bf-banner::before {
    content: '🎾'; position: absolute; right: 1.2rem; top: 50%;
    transform: translateY(-50%); font-size: 5rem; opacity: .06; line-height: 1;
}
.bf-banner h2 {
    color: #fff !important; font-size: 1.1rem !important;
    font-weight: 900 !important; margin: 0 0 .18rem !important; letter-spacing: -.025em !important;
}
.bf-banner .meta { color: rgba(255,255,255,.5); font-size: .73rem; }
.bf-banner .badge {
    background: rgba(249,115,22,.85); border-radius: 100px;
    padding: .3rem .95rem; color: #fff; font-weight: 700; font-size: .75rem;
    white-space: nowrap; box-shadow: 0 2px 8px rgba(249,115,22,.4);
}

/* ══════════════════════════════════════════
   FORMATO CARDS (seleção)
══════════════════════════════════════════ */
.bf-fmt-card {
    background: #fff; border: 2px solid #e8d5c0; border-radius: 16px;
    padding: 1rem 1.1rem; cursor: pointer;
    transition: all .15s ease; margin-bottom: .5rem;
}
.bf-fmt-card:hover { border-color: #f97316; box-shadow: 0 4px 16px rgba(249,115,22,.15); }
.bf-fmt-card.selected {
    border-color: #f97316; background: #fff8f2;
    box-shadow: 0 4px 16px rgba(249,115,22,.18);
}
.bf-fmt-icon { font-size: 1.8rem; line-height: 1; margin-bottom: .4rem; }
.bf-fmt-name { font-size: .92rem; font-weight: 800; color: #1c1917; margin-bottom: .2rem; }
.bf-fmt-desc { font-size: .75rem; color: #a07050; line-height: 1.45; }

/* ══════════════════════════════════════════
   RULES DISPLAY
══════════════════════════════════════════ */
.bf-rules {
    background: linear-gradient(135deg, #fff8f0, #fffcf9);
    border: 1.5px solid #fcd9aa; border-radius: 14px;
    padding: 1rem 1.1rem;
}
.bf-rules-title {
    font-size: .68rem; font-weight: 800; letter-spacing: .12em;
    text-transform: uppercase; color: #f97316; margin-bottom: .65rem;
}
.bf-rule-row {
    display: flex; align-items: flex-start; gap: .5rem;
    padding: .28rem 0; font-size: .8rem; color: #6b4326; line-height: 1.4;
    border-bottom: 1px solid rgba(252,217,170,.4);
}
.bf-rule-row:last-child { border-bottom: none; }
.bf-rule-icon { min-width: 1.2rem; text-align: center; }
.bf-rule-text b { color: #c2410c; }

/* ══════════════════════════════════════════
   MATCH HISTORY
══════════════════════════════════════════ */
.bf-bracket-match {
    background: #fff; border: 1.5px solid #e8d5c0;
    border-radius: 12px; padding: .6rem .95rem;
    margin: .3rem 0; font-size: .84rem;
    display: flex; align-items: center; gap: .75rem;
}
.bf-bracket-match.done { border-left: 4px solid #f97316; }
.bf-bscore { font-weight: 900; color: #f97316; min-width: 4rem; text-align: center; font-size: .9rem; }
.bf-bwin { font-weight: 800; color: #f97316; }
.bf-blose { color: #c4a898; }

/* ══════════════════════════════════════════
   RANKING TABLE
══════════════════════════════════════════ */
.bf-rank-wrap {
    background: #fff; border-radius: 14px; border: 1.5px solid #e8d5c0;
    box-shadow: 0 2px 12px rgba(0,0,0,.06); overflow: hidden; margin-top: .4rem;
}
.bf-rank-row {
    display: flex; align-items: center; padding: .85rem 1.1rem;
    border-bottom: 1px solid #faf0e6; gap: .8rem;
}
.bf-rank-row:last-child { border-bottom: none; }
.bf-rank-row.p1 { background: linear-gradient(90deg,#fffaeb,#fff); }
.bf-rank-row.p3 { background: linear-gradient(90deg,#fff8f5,#fff); }
.bf-rpos { font-size: 1.3rem; min-width: 2.1rem; text-align: center; }
.bf-rname { flex: 1; font-weight: 700; font-size: .88rem; color: #1c1917; }
.bf-rstats { display: flex; gap: .9rem; }
.bf-stat { text-align: center; min-width: 2.4rem; }
.bf-sv { font-weight: 700; font-size: .9rem; color: #1c1917; line-height: 1.1; }
.bf-sl { font-size: .58rem; color: #c09070; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; margin-top: 2px; }
.bf-pts .bf-sv { font-size: 1.1rem; color: #f97316; font-weight: 900; }

/* ══════════════════════════════════════════
   STATUS & NOTICES
══════════════════════════════════════════ */
.bf-badge {
    display: inline-flex; align-items: center; gap: .35rem;
    background: linear-gradient(135deg,#f97316,#fb923c);
    color: #fff; border-radius: 100px; padding: .22rem .8rem;
    font-size: .75rem; font-weight: 700;
    box-shadow: 0 2px 8px rgba(249,115,22,.3);
}
.bf-pin-ok { color: #15803d; font-size: .75rem; font-weight: 600; }
.bf-pin-no { color: #dc2626; font-size: .75rem; font-weight: 600; }
.bf-bye {
    background: #fefce8; border: 1px solid #fde047; border-radius: 10px;
    padding: .55rem .9rem; color: #854d0e; font-size: .81rem; margin-bottom: .5rem;
}
.bf-done {
    background: #f0fdf4; border: 1px solid #86efac; border-radius: 12px;
    padding: .85rem; text-align: center; color: #166534;
    font-weight: 700; font-size: .88rem; margin-bottom: .75rem;
}
.bf-champion {
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border: 2px solid #f59e0b; border-radius: 16px;
    padding: 1.2rem 1.5rem; text-align: center;
    font-size: 1.2rem; color: #78350f; font-weight: 800; margin-bottom: 1rem;
    box-shadow: 0 6px 20px rgba(245,158,11,.2);
}

/* ══════════════════════════════════════════
   BRACKET TREE
══════════════════════════════════════════ */
.bf-tree { display: flex; gap: 1.2rem; overflow-x: auto; padding: .5rem 0; }
.bf-tree-round { min-width: 160px; }
.bf-tree-rname {
    font-size: .62rem; font-weight: 800; letter-spacing: .12em;
    text-transform: uppercase; color: #f97316; margin-bottom: .6rem;
}
.bf-tree-match {
    background: #fff; border: 1.5px solid #e8d5c0;
    border-radius: 10px; padding: .45rem .75rem; margin-bottom: .85rem;
}
.bf-tree-p { font-size: .8rem; padding: .2rem 0; color: #888; border-bottom: 1px solid #faf0e6; }
.bf-tree-p:last-child { border-bottom: none; }
.bf-tree-p.w { font-weight: 800; color: #f97316; }

/* ══════════════════════════════════════════
   MISC
══════════════════════════════════════════ */
.bf-match-lbl {
    font-size: .65rem; font-weight: 800; letter-spacing: .1em;
    text-transform: uppercase; color: #c4a898; margin: .8rem 0 .35rem;
}
.bf-team { font-size: .9rem; font-weight: 700; color: #1c1917; line-height: 1.65; }
.bf-hero { text-align: center; padding: 1.8rem 1rem .6rem; }
.bf-hero-icon { font-size: 2.6rem; line-height: 1; margin-bottom: .25rem; }
.bf-hero-title { font-size: 2rem; font-weight: 900; color: #1c1917; letter-spacing: -.04em; margin: 0; }
.bf-hero-sub { color: #a07050; font-size: .83rem; margin-top: .3rem; font-weight: 500; }
</style>
"""


def apply_custom_css() -> None:
    st.markdown(_CSS + _COMPONENT_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Components
# ─────────────────────────────────────────────

def topbar(badge: str = "") -> None:
    badge_html = (f'<div class="bf-topbar-badge">{badge}</div>' if badge else "")
    st.markdown(
        f'<div class="bf-topbar">'
        f'  <div class="bf-topbar-left">'
        f'    <div class="bf-topbar-icon">🏖️</div>'
        f'    <div>'
        f'      <div class="bf-topbar-name">Beach&Friends</div>'
        f'      <div class="bf-topbar-sub">Placar & Chaveamento</div>'
        f'    </div>'
        f'  </div>'
        f'  {badge_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def logo_header(title: str = "Beach&Friends",
                subtitle: str = "Placar & Chaveamento Inteligente") -> None:
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
        f'<div><h2>{name}</h2>'
        f'<div class="meta">{n} participantes · {total} rodadas</div></div>'
        f'<div class="badge">{badge}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_rules_card(rules: list) -> None:
    rows = "".join(
        f'<div class="bf-rule-row">'
        f'<div class="bf-rule-icon">{icon}</div>'
        f'<div class="bf-rule-text">{text}</div>'
        f'</div>'
        for icon, text in rules
    )
    st.markdown(
        f'<div class="bf-rules">'
        f'<div class="bf-rules-title">📋 Regras da Partida</div>'
        f'{rows}</div>',
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
            f"<div style='text-align:center;font-weight:700;color:#1c1917'>{sc}</div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div style='text-align:right'><span style='{bw}'>{tb_str}</span></div>",
            unsafe_allow_html=True,
        )
