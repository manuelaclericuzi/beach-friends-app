import streamlit as st
from datetime import datetime, date as dt_date

st.set_page_config(
    page_title="Beach&Friends",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from modules.ui_components import (apply_custom_css, login_header, hero, topbar,
                                    field_label, section_label, render_ranking_section,
                                    render_rules_card, render_format_info)
from modules.auth import hash_pin, verify, DEFAULT_ADMIN_PASSWORD
from modules import persistence
from modules.rainha_da_praia import RainhaDaPraia
from modules.duplas_fixas import DuplasFixas
from modules.mata_mata import MataMata

apply_custom_css()

# ─────────────────────────────────────────────
#  Format registry
# ─────────────────────────────────────────────

FORMATS = {
    "rainha_da_praia": {
        "cls": RainhaDaPraia, "id": "rainha_da_praia",
        "icon": "🔄",
        "label": "Rotativo — Super 8 / Rainha da Praia",
        "desc": "Parceiras trocam a cada rodada seguindo matriz matemática perfeita. Pontuação individual acumulada.",
        "min": 4, "even": False,
    },
    "duplas_fixas": {
        "cls": DuplasFixas, "id": "duplas_fixas",
        "icon": "🤝",
        "label": "Duplas Fixas — Pontos Corridos",
        "desc": "Duplas se formam uma vez e disputam todas entre si (round-robin). Vence a dupla com mais pontos.",
        "min": 4, "even": True,
    },
    "mata_mata": {
        "cls": MataMata, "id": "mata_mata",
        "icon": "⚔️",
        "label": "Mata-Mata — Chaveamento",
        "desc": "Eliminação direta. Perde, sai. Avanço automático no bracket com BYE para número ímpar.",
        "min": 2, "even": False,
    },
}
FORMAT_BY_ID  = {v["id"]: v for v in FORMATS.values()}
FORMAT_KEYS   = list(FORMATS.keys())
_FMT_ICON     = {k: v["icon"]  for k, v in FORMATS.items()}
_FMT_NAME     = {k: v["label"] for k, v in FORMATS.items()}

_FORMAT_RULES = {
    "rainha_da_praia": [
        ("🔄", "Parceiras <b>rotacionam</b> a cada rodada — sem dupla fixa"),
        ("🎾", "Set de <b>4 games</b> — vence quem chegar a <b>3 primeiro</b>"),
        ("🔥", "Empate 2–2 → <b>Super Tie-Break</b> (primeiro a 10 pts, vantagem 2)"),
        ("🏆", "Vitória = <b>3 pts</b>  ·  Derrota = <b>0 pts</b>"),
        ("⚖️", "Desempate: Pontos → Saldo de games → Games pró → Alfabético"),
    ],
    "duplas_fixas": [
        ("🤝", "Duplas <b>fixas</b> formadas antes do torneio"),
        ("🎾", "Set de <b>4 games</b> — vence quem chegar a <b>3 primeiro</b>"),
        ("🔥", "Empate 2–2 → <b>Super Tie-Break</b> (primeiro a 10 pts, vantagem 2)"),
        ("🏆", "Vitória = <b>3 pts</b>  ·  Derrota = <b>0 pts</b>"),
        ("📊", "Round-robin: todas as duplas se enfrentam"),
    ],
    "mata_mata": [
        ("⚔️", "<b>Eliminação direta</b> — perde, sai"),
        ("🎾", "Set de <b>4 games</b> — vence quem chegar a <b>3 primeiro</b>"),
        ("🔥", "Empate 2–2 → <b>Super Tie-Break</b> (primeiro a 10 pts, vantagem 2)"),
        ("🔄", "<b>BYE automático</b> para número ímpar de participantes"),
        ("🏆", "Vencedora avança automaticamente no bracket"),
    ],
}


# ─────────────────────────────────────────────
#  Session bootstrap
# ─────────────────────────────────────────────

def _init():
    if "data" not in st.session_state:
        st.session_state["data"] = persistence.load()

    if "role" not in st.session_state:
        qp = st.query_params
        r  = qp.get("r", "")
        p  = qp.get("p", "")
        if r == "admin":
            st.session_state["role"] = "admin"
            st.session_state["player_name"] = None
        elif r == "player" and p:
            players = st.session_state["data"].get("players", {})
            if p in players:
                st.session_state["role"] = "player"
                st.session_state["player_name"] = p
            else:
                st.session_state["role"] = None
                st.session_state["player_name"] = None
                st.query_params.clear()
        else:
            st.session_state["role"] = None
            st.session_state["player_name"] = None

    if "player_name" not in st.session_state:
        st.session_state["player_name"] = None
    if "tournament" not in st.session_state:
        _restore_tournament()


def _restore_tournament():
    rec = st.session_state["data"].get("tournament")
    if rec:
        fmt = FORMAT_BY_ID.get(rec.get("format"))
        if fmt:
            try:
                st.session_state["tournament"] = fmt["cls"].from_dict(rec["data"])
                return
            except Exception:
                pass
    st.session_state["tournament"] = None


def _persist():
    t = st.session_state.get("tournament")
    if t:
        st.session_state["data"]["tournament"] = {
            "format": t.format_id, "data": t.to_dict(),
        }
    persistence.save(st.session_state["data"])


def _logout():
    st.session_state["role"] = None
    st.session_state["player_name"] = None
    st.query_params.clear()
    st.rerun()


# ─────────────────────────────────────────────
#  Login
# ─────────────────────────────────────────────

def render_login():
    players_dict = st.session_state["data"].get("players", {})
    player_names = sorted(players_dict.keys())

    st.markdown("<div style='height:3vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.container(border=True):
            login_header()

            field_label("Tipo de acesso")
            role_sel = st.radio(
                "role",
                ["🎾  Jogadora", "🔑  Administradora"],
                horizontal=True,
                label_visibility="collapsed",
                key="login_role",
            )
            is_admin = "Admin" in role_sel

            player_sel = None
            is_first   = False

            if not is_admin:
                field_label("Escolha seu nome")
                if player_names:
                    player_sel = st.selectbox(
                        "player", player_names,
                        label_visibility="collapsed", key="login_player",
                    )
                    is_first = not players_dict[player_sel].get("pin_hash")
                    if is_first:
                        st.markdown(
                            '<div class="bf-hint">✨ Primeiro acesso — crie seu <b>PIN de 4+ dígitos</b>.</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.warning("Nenhuma jogadora cadastrada ainda.")
                    st.stop()

            field_label("Criar PIN" if is_first else ("Senha" if is_admin else "PIN"))
            pin_input = st.text_input(
                "pin", placeholder="••••••••", type="password",
                label_visibility="collapsed", key="login_pin",
            )

            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            enter = st.button("Entrar  →", type="primary", use_container_width=True, key="btn_login")
            st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)

    role_legacy = "Administradora" if is_admin else "Jogadora do Torneio"
    if enter:
        _handle_login(role_legacy, player_sel, pin_input, players_dict, is_first)


def _handle_login(role_sel, player_sel, pin, players_dict, is_first):
    pin = pin.strip()
    if not pin:
        st.error("Digite sua senha ou PIN.")
        return

    if role_sel == "Administradora":
        if verify(pin, st.session_state["data"]["admin_password_hash"]):
            st.session_state["role"] = "admin"
            st.session_state["player_name"] = None
            st.query_params["r"] = "admin"
            st.rerun()
        else:
            _, col, _ = st.columns([1, 1.4, 1])
            with col:
                st.error("Senha incorreta.")
        return

    if len(pin) < 4:
        _, col, _ = st.columns([1, 1.4, 1])
        with col:
            st.error("O PIN deve ter pelo menos 4 dígitos.")
        return

    if is_first:
        st.session_state["data"]["players"][player_sel]["pin_hash"] = hash_pin(pin)
        _persist()
        st.session_state["role"] = "player"
        st.session_state["player_name"] = player_sel
        st.query_params.update({"r": "player", "p": player_sel})
        st.rerun()
    else:
        stored = players_dict[player_sel].get("pin_hash")
        if verify(pin, stored):
            st.session_state["role"] = "player"
            st.session_state["player_name"] = player_sel
            st.query_params.update({"r": "player", "p": player_sel})
            st.rerun()
        else:
            _, col, _ = st.columns([1, 1.4, 1])
            with col:
                st.error("PIN incorreto. Tente novamente.")


# ─────────────────────────────────────────────
#  Player view
# ─────────────────────────────────────────────

def render_player():
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30_000, limit=None, key="player_refresh")

    name = st.session_state["player_name"]

    fresh = persistence.load()
    st.session_state["data"] = fresh
    fmt = FORMAT_BY_ID.get((fresh.get("tournament") or {}).get("format"))
    if fmt:
        try:
            st.session_state["tournament"] = fmt["cls"].from_dict(
                fresh["tournament"]["data"])
        except Exception:
            st.session_state["tournament"] = None
    t = st.session_state.get("tournament")

    c1, c2 = st.columns([6, 1])
    with c1:
        topbar(f"👤 {name}")
    with c2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            _logout()

    # ── Personal stats banner ─────────────────────
    _render_player_banner(name, t, fresh)

    ptabs = st.tabs(["🏆  Torneio", "📊  Ranking", "⏳  Histórico"])

    with ptabs[0]:
        if t is None:
            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            col = st.columns([1, 2, 1])[1]
            with col:
                with st.container(border=True):
                    st.markdown(
                        '<div style="text-align:center;padding:2rem 1rem">'
                        '<div style="font-size:3.5rem">🏖️</div>'
                        '<div style="font-size:1.1rem;font-weight:700;color:#1a1a1a;margin:.5rem 0">'
                        'Nenhum torneio ativo</div>'
                        '<div style="font-size:.85rem;color:#c49070">'
                        'Aguarde a administradora iniciar o torneio.</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
        else:
            t.render(can_edit=False)

    with ptabs[1]:
        _render_player_ranking(fresh)

    with ptabs[2]:
        _tab_history(can_edit=False, player_filter=name)


def _render_player_banner(name: str, t, data: dict):
    """Gradient card showing the logged-in player's current stats."""
    # Try current tournament first, then accumulated ranking
    pts, matches, balance = 0, 0, 0

    if t is not None and t.format_id == "rainha_da_praia":
        ps = t.player_stats.get(name, {})
        pts     = ps.get("points", 0)
        matches = ps.get("matches", 0)
        balance = ps.get("game_balance", 0)
    else:
        ranking = data.get("ranking", {})
        if name in ranking:
            r       = ranking[name]
            pts     = r.get("points", 0)
            matches = r.get("matches", 0)
            balance = r.get("game_balance", 0)

    if pts == 0 and matches == 0:
        return  # nothing to show yet

    bal_str = f"+{balance}" if balance > 0 else str(balance)
    source  = "torneio atual" if t else "ranking acumulado"

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#f97316,#ea580c);'
        f'border-radius:18px;padding:1rem 1.5rem;margin-bottom:1rem;'
        f'display:flex;align-items:center;justify-content:space-between;'
        f'box-shadow:0 6px 20px rgba(249,115,22,.3)">'
        f'<div>'
        f'<div style="font-size:.65rem;font-weight:700;color:rgba(255,255,255,.65);'
        f'text-transform:uppercase;letter-spacing:.1em">Minha Quadra · {source}</div>'
        f'<div style="font-size:1rem;font-weight:900;color:#fff;margin-top:.2rem">'
        f'Olá, {name}! 🎾</div>'
        f'</div>'
        f'<div style="display:flex;gap:1.5rem">'
        f'<div style="text-align:center">'
        f'<div style="font-size:1.5rem;font-weight:900;color:#fff">{pts}</div>'
        f'<div style="font-size:.62rem;color:rgba(255,255,255,.65)">pts</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div style="font-size:1.5rem;font-weight:900;color:#fff">{matches}</div>'
        f'<div style="font-size:.62rem;color:rgba(255,255,255,.65)">jogos</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div style="font-size:1.5rem;font-weight:900;color:#fff">{bal_str}</div>'
        f'<div style="font-size:.62rem;color:rgba(255,255,255,.65)">saldo</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_player_ranking(data: dict):
    ranking: dict = data.get("ranking", {})
    if not ranking:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#c49070;font-size:.9rem">'
            '📊  Ranking ainda sem dados.<br>'
            '<span style="font-size:.8rem">Será atualizado ao fim de cada torneio.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    sorted_ranking = sorted(
        ranking.items(),
        key=lambda x: (-x[1].get("points", 0), -x[1].get("game_balance", 0), x[0]),
    )
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    for i, (name, s) in enumerate(sorted_ranking):
        pos      = medals.get(i, f"{i + 1}º")
        gb       = s.get("game_balance", 0)
        gb_color = "#16a34a" if gb >= 0 else "#dc2626"
        gb_str   = f"+{gb}" if gb > 0 else str(gb)
        wins     = s.get("wins", 0)
        total    = s.get("matches", 0)
        pct      = f"{round(wins / total * 100)}%" if total else "—"
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
            with c1:
                st.markdown(
                    f'<div style="font-weight:800;font-size:.95rem">{pos} {name}</div>'
                    f'<div style="font-size:.7rem;color:#c49070">'
                    f'{s.get("tournaments", 0)} torneio(s)</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.25rem;font-weight:900;color:#f97316">'
                    f'{s.get("points", 0)}</div>'
                    f'<div style="font-size:.67rem;color:#c49070">pts</div></div>',
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.05rem;font-weight:700;color:{gb_color}">'
                    f'{gb_str}</div>'
                    f'<div style="font-size:.67rem;color:#c49070">saldo</div></div>',
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.05rem;font-weight:700">{pct}</div>'
                    f'<div style="font-size:.67rem;color:#c49070">% vitória</div></div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────
#  Admin view
# ─────────────────────────────────────────────

def render_admin():
    c1, c2 = st.columns([6, 1])
    with c1:
        topbar("🔑 Administradora")
    with c2:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            _logout()

    tabs = st.tabs(["🏆  Torneio", "👥  Jogadoras", "📊  Ranking", "⏳  Histórico", "⚙️  Config"])
    with tabs[0]:
        _tab_tournament()
    with tabs[1]:
        _tab_players()
    with tabs[2]:
        _tab_ranking()
    with tabs[3]:
        _tab_history(can_edit=True)
    with tabs[4]:
        _tab_settings()


# ─────────────────────────────────────────────
#  Ranking / archive helpers
# ─────────────────────────────────────────────

def _extract_standings(t) -> dict:
    from modules.scoring import empty_stats
    standings: dict = {}
    if t.format_id == "rainha_da_praia":
        standings = {k: dict(v) for k, v in t.player_stats.items()}
    elif t.format_id == "duplas_fixas":
        for team in getattr(t, "teams", []):
            ts = t.team_stats.get(team["name"], empty_stats())
            for player in team["players"]:
                standings[player] = dict(ts)
    elif t.format_id == "mata_mata":
        from modules.scoring import empty_stats as es
        for p in t.participants:
            standings[p] = {**es(), "matches": 1}
        if t.champion:
            standings[t.champion] = {**es(), "matches": 1, "wins": 1, "points": 3}
    return standings


def _get_ranking_snapshot(t) -> list:
    standings = _extract_standings(t)
    return sorted(
        [{"name": n, **s} for n, s in standings.items()],
        key=lambda x: (-x.get("points", 0), -x.get("game_balance", 0), x["name"])
    )


def _register_in_ranking(t) -> None:
    data    = st.session_state["data"]
    ranking = data.setdefault("ranking", {})
    for player, stats in _extract_standings(t).items():
        if player not in ranking:
            ranking[player] = {"tournaments": 0, "matches": 0,
                               "wins": 0, "points": 0, "game_balance": 0}
        r = ranking[player]
        r["tournaments"]  += 1
        r["matches"]      += stats.get("matches", 0)
        r["wins"]         += stats.get("wins", 0)
        r["points"]       += stats.get("points", 0)
        r["game_balance"] += stats.get("game_balance", 0)
    _persist()


def _archive_tournament_with_meta(t, name: str, location: str, date_str: str) -> None:
    data    = st.session_state["data"]
    history = data.setdefault("tournament_history", [])
    players = list(getattr(t, "players", getattr(t, "participants", [])))
    history.append({
        "format":           t.format_id,
        "format_name":      getattr(t, "format_name", t.format_id),
        "name":             name,
        "location":         location,
        "date":             date_str,
        "n_players":        len(players),
        "players":          players,
        "ranking_snapshot": _get_ranking_snapshot(t),
        "data":             t.to_dict(),
        "archived_at":      datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    if len(history) > 30:
        history[:] = history[-30:]


# ─────────────────────────────────────────────
#  History tab  (shared admin + player)
# ─────────────────────────────────────────────

def _tab_history(can_edit: bool = True, player_filter: str = ""):
    data    = st.session_state["data"]
    history = data.get("tournament_history", [])

    # ── Detail view mode ─────────────────────────────
    viewing = st.session_state.get("hist_viewing")
    if viewing:
        h_found = next((x for x in history if x.get("archived_at") == viewing), None)
        if h_found:
            _render_history_detail(h_found, can_edit)
        else:
            st.session_state.pop("hist_viewing", None)
            st.rerun()
        return

    # ── Empty state ───────────────────────────────────
    if not history:
        st.markdown(
            '<div style="text-align:center;padding:3rem 1rem;color:#c49070">'
            '⏳  Nenhum torneio arquivado ainda.<br>'
            '<span style="font-size:.8rem">Encerre um torneio para vê-lo aqui.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Filters ───────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:.55rem;margin-bottom:.8rem">'
        '<span style="font-size:1rem">🔍</span>'
        '<span style="font-weight:900;font-size:.9rem;letter-spacing:.06em;'
        'color:#1a1613;text-transform:uppercase">Filtrar Histórico de Torneios</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    fc1, fc2, fc3 = st.columns(3, gap="medium")
    with fc1:
        field_label("Data do Torneio")
        date_filter = st.date_input(
            "hs_date_in", value=None,
            label_visibility="collapsed", key="hs_date",
            format="DD/MM/YYYY",
        )
    with fc2:
        field_label("Local / Arena")
        search_loc = st.text_input(
            "hs_loc_in", placeholder="Pesquisar por clube ou praia...",
            label_visibility="collapsed", key="hs_loc",
        )
    with fc3:
        field_label("Selecione uma Atleta")
        all_participants = sorted({p for h in history for p in h.get("players", [])})
        opts = ["Todas as jogadoras"] + all_participants
        default_idx = opts.index(player_filter) if player_filter in opts else 0
        search_player = st.selectbox(
            "hs_player_sel", opts, index=default_idx,
            label_visibility="collapsed", key="hs_player",
        )

    _has_filter = (
        bool(date_filter)
        or bool(st.session_state.get("hs_loc"))
        or st.session_state.get("hs_player", "Todas as jogadoras") != "Todas as jogadoras"
    )
    if _has_filter:
        if st.button("× Limpar filtros", key="hs_clear"):
            for k in ("hs_date", "hs_loc", "hs_player"):
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # ── Apply filters ─────────────────────────────────
    filtered = list(reversed(history))
    if date_filter:
        filtered = [h for h in filtered if h.get("date", "") == str(date_filter)]
    if search_loc:
        filtered = [h for h in filtered
                    if search_loc.lower() in h.get("location", "").lower()]
    if search_player != "Todas as jogadoras":
        filtered = [h for h in filtered if search_player in h.get("players", [])]

    count_txt = (
        f"{len(filtered)} torneio{'s' if len(filtered) != 1 else ''} "
        f"encontrado{'s' if len(filtered) != 1 else ''}"
    )
    st.markdown(
        f'<div style="font-size:.73rem;color:#9b8679;margin-bottom:.6rem">{count_txt}</div>',
        unsafe_allow_html=True,
    )

    if not filtered:
        st.info("Nenhum torneio encontrado com esses filtros.")
        return

    # ── Card grid (2 columns) ─────────────────────────
    for row_start in range(0, len(filtered), 2):
        cols = st.columns(2, gap="medium")
        for col_i, h in enumerate(filtered[row_start: row_start + 2]):
            with cols[col_i]:
                _render_history_card(h)
        st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)


def _render_history_card(h: dict):
    """Compact tournament card shown in the 2-column history grid."""
    fmt_label = h.get("format_name", h["format"]).upper()
    name      = h.get("name", fmt_label)
    location  = h.get("location", "")
    date_str  = h.get("date", h.get("archived_at", ""))
    ranking   = h.get("ranking_snapshot", [])

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    podium_rows = ""
    for i, r in enumerate(ranking[:3]):
        medal = medals.get(i, f"{i+1}º")
        pts   = r.get("points", 0)
        podium_rows += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:.25rem 0;font-size:.83rem;border-bottom:1px solid #faf0e6">'
            f'<span style="color:#374151">{medal} {r["name"]}</span>'
            f'<span style="color:#f97316;font-weight:800">{pts} Pts</span></div>'
        )
    if not podium_rows:
        podium_rows = '<div style="font-size:.78rem;color:#9b8679;padding:.3rem 0">Sem dados de pódio.</div>'

    loc_html = (
        f'<div style="font-size:.78rem;color:#6b7280;margin:.2rem 0 .6rem;'
        f'display:flex;align-items:center;gap:.3rem">📍 {location}</div>'
        if location else
        '<div style="margin-bottom:.6rem"></div>'
    )

    with st.container(border=True):
        st.markdown(
            f'<div style="padding:.1rem 0">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'margin-bottom:.35rem">'
            f'<span style="font-size:.63rem;font-weight:700;color:#9b8679;'
            f'text-transform:uppercase;letter-spacing:.08em">{fmt_label}</span>'
            f'<span style="font-size:.72rem;color:#9b8679">{date_str}</span>'
            f'</div>'
            f'<div style="font-size:1rem;font-weight:900;color:#1a1613;margin-bottom:.2rem;'
            f'letter-spacing:-.02em">{name}</div>'
            f'{loc_html}'
            f'<div style="font-size:.63rem;font-weight:800;letter-spacing:.1em;'
            f'color:#9b8679;text-transform:uppercase;margin-bottom:.3rem">'
            f'Pódio do Dia:</div>'
            f'<div style="margin-bottom:.5rem">{podium_rows}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        key_safe = (h.get("archived_at", "")
                    .replace("/", "").replace(":", "").replace(" ", "_"))
        st.markdown('<div class="btn-dark-wrap">', unsafe_allow_html=True)
        if st.button("🔍 Ver Detalhes Completos", key=f"view_{key_safe}",
                     use_container_width=True):
            st.session_state["hist_viewing"] = h.get("archived_at", "")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def _render_history_detail(h: dict, can_edit: bool):
    """Full-page detail view for a single archived tournament."""
    name     = h.get("name", h.get("format_name", "Torneio"))
    location = h.get("location", "")
    date_str = h.get("date", h.get("archived_at", ""))
    ranking  = h.get("ranking_snapshot", [])
    players  = h.get("players", [])
    fmt_name = h.get("format_name", h["format"])

    if st.button("← Voltar ao Histórico", key="hist_back"):
        st.session_state.pop("hist_viewing", None)
        st.rerun()

    meta_parts = []
    if location:
        meta_parts.append(f"📍 {location}")
    if date_str:
        meta_parts.append(f"📅 {date_str}")
    meta_parts.append(f"{len(players)} participantes")

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1613,#2c2420);'
        f'border-radius:16px;padding:1rem 1.4rem;margin:.5rem 0 1rem">'
        f'<div style="color:rgba(255,255,255,.5);font-size:.68rem;text-transform:uppercase;'
        f'letter-spacing:.1em">{fmt_name}</div>'
        f'<div style="color:#fff;font-weight:900;font-size:1.15rem;margin:.2rem 0 .15rem">'
        f'{name}</div>'
        f'<div style="color:rgba(255,255,255,.5);font-size:.75rem">'
        f'{"  ·  ".join(meta_parts)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    dtabs = st.tabs(["🏆 Pódio & Ranking", "📋 Rodadas Completas"])

    with dtabs[0]:
        if not ranking:
            st.info("Sem dados de ranking para este torneio.")
        else:
            medals = {0: "🥇", 1: "🥈", 2: "🥉"}
            for i, r in enumerate(ranking):
                pos    = medals.get(i, f"{i+1}º")
                pts    = r.get("points", 0)
                gb     = r.get("game_balance", 0)
                gb_str = f"+{gb}" if gb > 0 else str(gb)
                gb_col = "#16a34a" if gb >= 0 else "#dc2626"
                wins   = r.get("wins", 0)
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3.5, 1, 1, 1])
                    with c1:
                        st.markdown(
                            f'<div style="font-weight:800;font-size:.95rem">'
                            f'{pos} {r["name"]}</div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        st.markdown(
                            f'<div style="text-align:center">'
                            f'<div style="font-size:1.2rem;font-weight:900;color:#f97316">'
                            f'{pts}</div>'
                            f'<div style="font-size:.62rem;color:#9b8679">pts</div></div>',
                            unsafe_allow_html=True,
                        )
                    with c3:
                        st.markdown(
                            f'<div style="text-align:center">'
                            f'<div style="font-weight:700">{wins}</div>'
                            f'<div style="font-size:.62rem;color:#9b8679">vitórias</div></div>',
                            unsafe_allow_html=True,
                        )
                    with c4:
                        st.markdown(
                            f'<div style="text-align:center">'
                            f'<div style="font-weight:700;color:{gb_col}">{gb_str}</div>'
                            f'<div style="font-size:.62rem;color:#9b8679">saldo</div></div>',
                            unsafe_allow_html=True,
                        )

    with dtabs[1]:
        fmt_obj = FORMAT_BY_ID.get(h["format"])
        if fmt_obj and h.get("data"):
            try:
                t_hist = fmt_obj["cls"].from_dict(h["data"])
                t_hist.render(can_edit=False)
            except Exception as e:
                st.error(f"Erro ao carregar rodadas: {e}")
        else:
            st.info("Dados de rodadas não disponíveis.")

    if can_edit:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        del_key = f"del_hist_{h.get('archived_at', '')}"
        if st.session_state.get(del_key):
            cy, cn = st.columns(2)
            with cy:
                if st.button("✅ Confirmar exclusão", key=f"yes_{del_key}",
                             type="primary", use_container_width=True):
                    hist_list = st.session_state["data"]["tournament_history"]
                    idx_rm = next(
                        (i for i, x in enumerate(hist_list)
                         if x.get("archived_at") == h.get("archived_at")), None,
                    )
                    if idx_rm is not None:
                        hist_list.pop(idx_rm)
                    st.session_state.pop(del_key, None)
                    st.session_state.pop("hist_viewing", None)
                    _persist()
                    st.rerun()
            with cn:
                if st.button("❌ Cancelar", key=f"no_{del_key}", use_container_width=True):
                    st.session_state.pop(del_key, None)
                    st.rerun()
        else:
            if st.button("🗑️ Remover do Histórico", key=f"btn_{del_key}",
                         use_container_width=True):
                st.session_state[del_key] = True
                st.rerun()


# ─────────────────────────────────────────────
#  Tournament tab
# ─────────────────────────────────────────────

def _tab_tournament():
    t    = st.session_state.get("tournament")
    data = st.session_state["data"]

    if t is not None:
        if st.session_state.get("show_archive_form"):
            _render_archive_form(t)
        else:
            _, c2, c3 = st.columns([3.5, 2, 1.5])
            with c2:
                if st.button("📊  Registrar no Ranking", use_container_width=True):
                    _register_in_ranking(t)
                    st.success("✅ Resultados registrados no Ranking Geral!")
            with c3:
                if st.button("🏁  Encerrar Torneio", use_container_width=True):
                    st.session_state["show_archive_form"] = True
                    st.rerun()
            t.render(can_edit=True)

    elif st.session_state.get("pending_fmt"):
        _register_participants_ui()

    else:
        _pick_format_ui()


# ─────────────────────────────────────────────
#  Archive form
# ─────────────────────────────────────────────

def _render_archive_form(t):
    # Header
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1613,#2c2420);'
        f'border-radius:16px;padding:.9rem 1.3rem;margin-bottom:1rem">'
        f'<div style="color:rgba(255,255,255,.5);font-size:.7rem">Encerrar torneio</div>'
        f'<div style="color:#fff;font-weight:800;font-size:1rem">'
        f'{getattr(t, "format_name", t.format_id)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_form, col_prev = st.columns([3, 2], gap="large")

    with col_form:
        with st.container(border=True):
            section_label("📝 Dados do Torneio")

            field_label("Nome do Torneio")
            default_name = f"Torneio {getattr(t, 'format_name', t.format_id)}"
            arc_name = st.text_input("arc_name_in",
                                     value=st.session_state.get("arc_name", default_name),
                                     label_visibility="collapsed", key="arc_name")

            field_label("Local / Arena")
            arc_loc  = st.text_input("arc_loc_in",
                                     value=st.session_state.get("arc_loc", ""),
                                     label_visibility="collapsed", key="arc_loc")

            field_label("Data de Realização")
            arc_date = st.date_input("arc_date_in",
                                     value=dt_date.today(),
                                     label_visibility="collapsed", key="arc_date")

            st.markdown(
                '<div style="font-size:.75rem;color:#c49070;padding:.6rem .8rem;'
                'background:#fff9f2;border-radius:10px;margin-top:.5rem">'
                'As pontuações e rodadas serão preservadas no Histórico.</div>',
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            ca, cb = st.columns(2)
            with ca:
                if st.button("✅  Finalizar & Salvar", type="primary", use_container_width=True):
                    if not arc_name.strip():
                        st.error("Informe o nome do torneio.")
                    else:
                        _archive_tournament_with_meta(t, arc_name.strip(),
                                                      arc_loc.strip(), str(arc_date))
                        for k in ("show_archive_form", "arc_name", "arc_loc"):
                            st.session_state.pop(k, None)
                        st.session_state["tournament"] = None
                        st.session_state["data"]["tournament"] = None
                        _persist()
                        st.rerun()
            with cb:
                if st.button("← Cancelar", use_container_width=True):
                    st.session_state.pop("show_archive_form", None)
                    st.rerun()

    with col_prev:
        section_label("📊 Ranking Final")
        snapshot = _get_ranking_snapshot(t)
        medals   = {0: "🥇", 1: "🥈", 2: "🥉"}
        for i, r in enumerate(snapshot[:6]):
            pos    = medals.get(i, f"{i+1}º")
            pts    = r.get("points", 0)
            gb     = r.get("game_balance", 0)
            gb_str = f"+{gb}" if gb > 0 else str(gb)
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:.4rem 0;border-bottom:1px solid #faf0e6;font-size:.88rem">'
                f'<span>{pos} <b>{r["name"]}</b></span>'
                f'<span style="color:#f97316;font-weight:900">{pts} pts &nbsp;'
                f'<span style="font-size:.72rem;color:#9b8679">{gb_str}</span></span></div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────
#  Step 1 — pick format
# ─────────────────────────────────────────────

def _pick_format_ui():
    st.markdown(
        '<div style="text-align:center;padding:1.8rem 1rem 1.5rem">'
        '<div style="font-size:3rem;margin-bottom:.6rem">🎾</div>'
        '<h2 style="font-size:1.35rem;font-weight:900;color:#1a1613;margin:0 0 .4rem;'
        'letter-spacing:-.02em">Selecione o Formato do Torneio</h2>'
        '<p style="font-size:.83rem;color:#9b8679;max-width:420px;margin:0 auto;'
        'line-height:1.5">Escolha um dos formatos de Beach Tennis abaixo para começar '
        'a marcar e gerar o ranking de forma automática.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    _FMT_CARDS = [
        ("rainha_da_praia", "👑", "Rainha (Super 8)",
         "Troca de parceiras automática a cada jogo. Pontuação 100% individual."),
        ("duplas_fixas",    "👥", "Duplas Fixas",
         "Duplas jogam entre si no modo pontos corridos clássico."),
        ("mata_mata",       "🏆", "Chave de Mata-Mata",
         "Cruzamento eliminatório com chaves de quartas, semis e final."),
    ]

    c1, c2, c3 = st.columns(3, gap="medium")
    for col, (fmt_id, icon, label, desc) in zip([c1, c2, c3], _FMT_CARDS):
        with col:
            with st.container(border=True):
                st.markdown(
                    f'<div style="text-align:center;padding:.9rem .5rem .3rem">'
                    f'<div style="font-size:2rem;margin-bottom:.45rem">{icon}</div>'
                    f'<div style="font-weight:800;font-size:.95rem;color:#1a1613;'
                    f'margin-bottom:.4rem">{label}</div>'
                    f'<div style="font-size:.78rem;color:#9b8679;min-height:2.8em;'
                    f'line-height:1.45;padding:0 .3rem">{desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Selecionar Torneio", key=f"fmt_{fmt_id}",
                             use_container_width=True):
                    st.session_state["pending_fmt"] = fmt_id
                    st.session_state["tourn_participants"] = sorted(
                        st.session_state["data"].get("players", {}).keys()
                    )
                    st.rerun()


# ─────────────────────────────────────────────
#  Step 2 — register participants
# ─────────────────────────────────────────────

def _register_participants_ui():
    fmt_id       = st.session_state["pending_fmt"]
    fmt          = FORMATS[fmt_id]
    players_dict = st.session_state["data"].get("players", {})
    all_reg      = sorted(players_dict.keys())

    if "tourn_participants" not in st.session_state:
        st.session_state["tourn_participants"] = list(all_reg)

    participants: list = st.session_state["tourn_participants"]

    # Wizard header
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.75rem;'
        f'background:linear-gradient(135deg,#1a1613,#2c2420);'
        f'border-radius:16px;padding:.85rem 1.2rem;margin-bottom:1rem">'
        f'<div style="font-size:1.5rem">{fmt["icon"]}</div>'
        f'<div>'
        f'<div style="color:#fff;font-weight:800;font-size:.95rem">{fmt["label"]}</div>'
        f'<div style="color:rgba(255,255,255,.45);font-size:.72rem">'
        f'Passo 2 de 2 — cadastre as participantes</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns([5, 7], gap="large")

    with col_l:
        with st.container(border=True):
            section_label("👥  Participantes do Torneio")

            if not participants:
                st.markdown(
                    '<div style="text-align:center;padding:1.2rem;'
                    'color:#c49070;font-size:.85rem">Nenhuma participante ainda.<br>'
                    '<span style="font-size:.75rem">Adicione à direita →</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                for p in list(participants):
                    pc1, pc2 = st.columns([6, 1])
                    with pc1:
                        st.markdown(
                            f'<div style="font-size:.88rem;padding:.25rem 0;'
                            f'font-weight:600;color:#1a1613">🎾 {p}</div>',
                            unsafe_allow_html=True,
                        )
                    with pc2:
                        if st.button("✕", key=f"rm_pt_{p}"):
                            participants.remove(p)
                            st.rerun()

            total   = len(participants)
            col_c   = "#f97316" if total >= fmt["min"] else "#dc2626"
            req_msg = ""
            if fmt["even"] and total % 2 != 0:
                col_c   = "#dc2626"
                req_msg = " · precisa ser par"
            st.markdown(
                f'<div style="display:inline-flex;align-items:center;gap:.5rem;'
                f'background:{col_c}1a;border:1.5px solid {col_c}55;'
                f'border-radius:100px;padding:.3rem .9rem;margin-top:.5rem">'
                f'<span style="font-size:1rem;font-weight:900;color:{col_c}">{total}</span>'
                f'<span style="font-size:.78rem;font-weight:600;color:#3a2e26">'
                f'participante{"s" if total != 1 else ""}{req_msg}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        if st.button("← Voltar ao formato", use_container_width=True):
            st.session_state.pop("pending_fmt", None)
            st.session_state.pop("tourn_participants", None)
            st.rerun()

    with col_r:
        with st.container(border=True):
            not_added = [p for p in all_reg if p not in participants]
            if not_added:
                section_label("➕  Jogadoras Cadastradas")
                sel_c, btn_c = st.columns([5, 2])
                with sel_c:
                    chosen = st.selectbox("sel", ["— selecione —"] + not_added,
                                          label_visibility="collapsed", key="pt_sel")
                with btn_c:
                    if st.button("Adicionar", key="add_reg_pt", use_container_width=True):
                        if chosen != "— selecione —":
                            participants.append(chosen)
                            st.rerun()
            else:
                st.markdown(
                    '<div style="font-size:.8rem;color:#9b8679;padding:.3rem 0">'
                    '✔ Todas as jogadoras cadastradas já estão na lista.</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<hr style="border-color:#edddd0;margin:.8rem 0">',
                        unsafe_allow_html=True)

            section_label("👤  Adicionar convidada / novo nome")
            ni1, ni2 = st.columns([5, 2])
            with ni1:
                new_name = st.text_input("nn", placeholder="Ex: Rafaela...",
                                         label_visibility="collapsed", key="pt_new_name")
            with ni2:
                if st.button("Adicionar", key="add_new_pt", use_container_width=True):
                    n = new_name.strip()
                    if n and n.lower() not in {x.lower() for x in participants}:
                        participants.append(n)
                        st.rerun()
                    elif n:
                        st.error("Nome já está na lista.")

            if new_name.strip():
                save_perm = st.checkbox("Salvar como jogadora permanente",
                                        key="save_perm", value=False)
                if save_perm:
                    st.caption("Ficará cadastrada na aba Jogadoras para próximos torneios.")
            else:
                save_perm = False

        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

        if st.button("🏆  Iniciar Torneio!", type="primary", use_container_width=True):
            if save_perm and new_name.strip():
                nm = new_name.strip()
                if nm not in st.session_state["data"]["players"]:
                    st.session_state["data"]["players"][nm] = {"pin_hash": None}

            ok = _do_create(list(participants), fmt_id)
            if ok is False:
                st.session_state.pop("pending_fmt", None)
                st.session_state.pop("tourn_participants", None)


def _do_create(players: list, fmt_id: str):
    fmt    = FORMATS.get(fmt_id) or FORMATS[FORMAT_KEYS[0]]
    errors = []
    if len(players) < fmt["min"]:
        errors.append(f"Mínimo de {fmt['min']} participantes para este formato.")
    if fmt["even"] and len(players) % 2 != 0:
        errors.append("Este formato exige número par de jogadoras.")
    if len(players) != len({p.lower() for p in players}):
        errors.append("Há nomes duplicados na lista.")
    if errors:
        for e in errors:
            st.error(e)
        return True

    t = fmt["cls"](players)
    st.session_state["tournament"] = t
    st.session_state["data"]["tournament"] = {"format": t.format_id, "data": t.to_dict()}
    _persist()
    st.rerun()
    return False


# ─────────────────────────────────────────────
#  Players tab
# ─────────────────────────────────────────────

def _tab_players():
    data    = st.session_state["data"]
    players = data.setdefault("players", {})
    ranking = data.get("ranking", {})
    t       = st.session_state.get("tournament")

    # ── Header ────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:.55rem;margin-bottom:1.2rem">'
        '<span style="font-size:1.2rem">👥</span>'
        '<span style="font-weight:900;font-size:1rem;letter-spacing:.05em;'
        'color:#1a1613;text-transform:uppercase">Gestão de Atletas</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── New player form + PIN instructions ─────────────
    col_form, col_info = st.columns([3, 2], gap="large")

    with col_form:
        section_label("Novo Registo")
        with st.form("add_player", clear_on_submit=True):
            field_label("Nome de Arena")
            new_name = st.text_input(
                "np", placeholder="Ex: Dani Sakai",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(
                "Adicionar Jogadora", type="primary", use_container_width=True,
            )
        if submitted:
            n = new_name.strip()
            if not n:
                st.error("Nome não pode ser vazio.")
            elif n.lower() in {x.lower() for x in players}:
                st.error("Já existe uma jogadora com esse nome.")
            else:
                players[n] = {"pin_hash": None}
                _persist()
                st.success(f"✅ {n} adicionada!")
                st.rerun()
        st.markdown(
            '<div style="font-size:.74rem;color:#c49070;margin-top:.3rem">'
            '🔒 Requer autenticação administrativa para editar.</div>',
            unsafe_allow_html=True,
        )

    with col_info:
        st.markdown(
            '<div style="background:#fffbeb;border:1.5px solid #fde68a;'
            'border-radius:14px;padding:1rem 1.1rem">'
            '<div style="font-size:.7rem;font-weight:800;letter-spacing:.1em;'
            'color:#d97706;margin-bottom:.5rem">💡 INSTRUÇÕES DE PIN</div>'
            '<div style="font-size:.8rem;color:#78350f;line-height:1.55">'
            'Cada atleta possui um código de 4 dígitos. Partilhe este número '
            'confidencialmente com cada amiga. Com o PIN, elas poderão fazer login '
            'no topo da aplicação, permitindo acesso aos dados individuais '
            'personalizados diretamente no telemóvel!</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Players table ─────────────────────────────────
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    section_label("Lista Geral de Atletas")

    if not players:
        st.markdown(
            '<div style="text-align:center;padding:2rem;color:#c49070">'
            '🏖️  Nenhuma jogadora cadastrada ainda.</div>',
            unsafe_allow_html=True,
        )
    else:
        hc1, hc2, hc3, hc4 = st.columns([4, 2, 2.5, 1])
        for col, lbl in zip([hc1, hc2, hc3, hc4],
                             ["ATLETA", "PIN EXCLUSIVO", "PARTIDAS JOGADAS", ""]):
            col.markdown(
                f'<div style="font-size:.62rem;font-weight:800;letter-spacing:.1em;'
                f'color:#9b8679;text-transform:uppercase;padding:.3rem 0">{lbl}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            '<div style="border-top:2px solid #edddd0;margin-bottom:.15rem"></div>',
            unsafe_allow_html=True,
        )

        for pname, info in sorted(players.items()):
            has_pin = bool(info.get("pin_hash"))

            # Match count: current tournament → ranking fallback
            m_count = 0
            if t is not None:
                if t.format_id == "rainha_da_praia":
                    m_count = t.player_stats.get(pname, {}).get("matches", 0)
                elif t.format_id == "duplas_fixas":
                    for team in getattr(t, "teams", []):
                        if pname in team["players"]:
                            m_count = t.team_stats.get(team["name"], {}).get("matches", 0)
                            break
            if m_count == 0:
                m_count = ranking.get(pname, {}).get("matches", 0)

            rc1, rc2, rc3, rc4 = st.columns([4, 2, 2.5, 1])
            with rc1:
                st.markdown(
                    f'<div style="font-weight:700;font-size:.92rem;'
                    f'padding:.45rem 0;color:#1a1613">{pname}</div>',
                    unsafe_allow_html=True,
                )
            with rc2:
                pin_html = (
                    '<span style="background:#f3f4f6;border:1px solid #e5e7eb;'
                    'border-radius:6px;padding:.22rem .65rem;font-family:monospace;'
                    'font-size:.88rem;color:#374151;letter-spacing:.15em">****</span>'
                    if has_pin else
                    '<span style="color:#dc2626;font-size:.78rem;font-weight:600">'
                    'Sem PIN</span>'
                )
                st.markdown(
                    f'<div style="padding:.45rem 0">{pin_html}</div>',
                    unsafe_allow_html=True,
                )
            with rc3:
                st.markdown(
                    f'<div style="text-align:center;font-weight:700;'
                    f'font-size:.92rem;padding:.45rem 0">{m_count}</div>',
                    unsafe_allow_html=True,
                )
            with rc4:
                if st.button("✕", key=f"del_{pname}", help=f"Remover {pname}"):
                    del players[pname]
                    _persist()
                    st.rerun()

            st.markdown(
                '<div style="border-bottom:1px solid #faf0e6;margin:0 0 .05rem"></div>',
                unsafe_allow_html=True,
            )

    # ── Advanced actions ──────────────────────────────
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    with st.expander("⚙️ Ações avançadas · importar / redefinir PINs"):
        tab_bulk, tab_reset = st.tabs(["📋 Importar lista", "🔓 Redefinir PINs"])

        with tab_bulk:
            st.caption("Cole vários nomes de uma vez — um por linha.")
            bulk_raw = st.text_area(
                "bulk", placeholder="Ana Paula\nBia\nCarol",
                height=130, label_visibility="collapsed", key="bulk_add",
            )
            if st.button("📋 Importar Lista", type="primary", use_container_width=True):
                names = [x.strip() for x in bulk_raw.strip().splitlines() if x.strip()]
                added, skipped = [], []
                for nm in names:
                    if nm.lower() in {x.lower() for x in players}:
                        skipped.append(nm)
                    else:
                        players[nm] = {"pin_hash": None}
                        added.append(nm)
                if added:
                    _persist()
                    st.success(f"✅ {len(added)} adicionada(s): {', '.join(added)}")
                if skipped:
                    st.warning(f"⚠️ Já existiam: {', '.join(skipped)}")
                if added:
                    st.rerun()

        with tab_reset:
            if players:
                sel_reset = st.selectbox(
                    "Jogadora", ["— todas —"] + sorted(players.keys()),
                    key="sel_rst_pin",
                )
                if st.button("🔓 Redefinir PIN selecionado", use_container_width=True,
                             key="do_rst_pin"):
                    if sel_reset == "— todas —":
                        for nm in players:
                            players[nm]["pin_hash"] = None
                        _persist()
                        st.success("Todos os PINs foram redefinidos.")
                    else:
                        players[sel_reset]["pin_hash"] = None
                        _persist()
                        st.success(f"PIN de {sel_reset} redefinido.")
                    st.rerun()
            else:
                st.caption("Nenhuma jogadora cadastrada.")


# ─────────────────────────────────────────────
#  Ranking tab
# ─────────────────────────────────────────────

def _tab_ranking():
    data    = st.session_state["data"]
    ranking = data.get("ranking", {})

    h1, h2 = st.columns([5, 1])
    with h1:
        section_label("📊  Ranking Geral")
    with h2:
        if ranking and st.button("🗑 Limpar", use_container_width=True):
            data["ranking"] = {}
            _persist()
            st.rerun()

    if not ranking:
        st.markdown(
            '<div style="text-align:center;padding:2.5rem 1rem;'
            'color:#c49070;font-size:.9rem">'
            '📊  Nenhum dado ainda.<br>'
            '<span style="font-size:.8rem">Encerre um torneio e clique em '
            '<b>Registrar no Ranking</b> para acumular resultados.</span></div>',
            unsafe_allow_html=True,
        )
        return

    sorted_ranking = sorted(
        ranking.items(),
        key=lambda x: (-x[1].get("points", 0), -x[1].get("game_balance", 0), x[0]),
    )
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

    for i, (name, s) in enumerate(sorted_ranking):
        pos      = medals.get(i, f"{i + 1}º")
        gb       = s.get("game_balance", 0)
        gb_color = "#16a34a" if gb >= 0 else "#dc2626"
        gb_str   = f"+{gb}" if gb > 0 else str(gb)
        total    = s.get("matches", 0)
        wins     = s.get("wins", 0)
        pct      = f"{round(wins / total * 100)}%" if total else "—"

        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 1, 1])
            with c1:
                st.markdown(
                    f'<div style="font-weight:800;font-size:.97rem;color:#1a1a1a">'
                    f'{pos}  {name}</div>'
                    f'<div style="font-size:.72rem;color:#c49070">'
                    f'{s.get("tournaments", 0)} torneio(s)</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.35rem;font-weight:900;color:#f97316">'
                    f'{s.get("points", 0)}</div>'
                    f'<div style="font-size:.68rem;color:#c49070">pts</div></div>',
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#1a1a1a">{wins}</div>'
                    f'<div style="font-size:.68rem;color:#c49070">vitórias</div></div>',
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#1a1a1a">{total}</div>'
                    f'<div style="font-size:.68rem;color:#c49070">jogos</div></div>',
                    unsafe_allow_html=True,
                )
            with c5:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.1rem;font-weight:700;color:{gb_color}">{gb_str}</div>'
                    f'<div style="font-size:.68rem;color:#c49070">saldo</div></div>',
                    unsafe_allow_html=True,
                )
            with c6:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#1a1a1a">{pct}</div>'
                    f'<div style="font-size:.68rem;color:#c49070">% vitória</div></div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────
#  Settings tab
# ─────────────────────────────────────────────

def _tab_settings():
    section_label("Alterar Senha Administrativa")
    with st.form("change_pwd"):
        cur  = st.text_input("Senha atual",     type="password")
        new1 = st.text_input("Nova senha",       type="password")
        new2 = st.text_input("Confirme a senha", type="password")
        if st.form_submit_button("Salvar Nova Senha", type="primary"):
            data = st.session_state["data"]
            if not verify(cur, data["admin_password_hash"]):
                st.error("Senha atual incorreta.")
            elif new1 != new2:
                st.error("As senhas não coincidem.")
            elif len(new1.strip()) < 4:
                st.error("Mínimo de 4 caracteres.")
            else:
                data["admin_password_hash"] = hash_pin(new1.strip())
                _persist()
                st.success("Senha alterada!")

    st.markdown("---")
    section_label("Histórico de Torneios Arquivados")
    data    = st.session_state["data"]
    history = data.get("tournament_history", [])
    if history:
        ca, cb = st.columns([4, 1])
        with ca:
            st.caption(f"{len(history)} torneio(s) arquivado(s)")
        with cb:
            if st.button("🗑 Limpar tudo", use_container_width=True):
                data["tournament_history"] = []
                _persist()
                st.rerun()
    else:
        st.caption("Nenhum torneio arquivado ainda.")

    st.markdown("---")
    section_label("Informações")
    st.markdown(
        f'<div style="font-size:.82rem;color:#c49070;line-height:2">'
        f'Senha padrão: <code style="background:#fff7ed;padding:.1rem .4rem;'
        f'border-radius:5px;color:#c2410c">{DEFAULT_ADMIN_PASSWORD}</code><br>'
        f'Dados: <code style="background:#fff7ed;padding:.1rem .4rem;'
        f'border-radius:5px;color:#c2410c">data/app_data.json</code></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    _init()
    role = st.session_state["role"]
    if role is None:
        render_login()
    elif role == "admin":
        render_admin()
    else:
        render_player()


if __name__ == "__main__":
    main()
