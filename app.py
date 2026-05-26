import streamlit as st
from datetime import datetime

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
FORMAT_BY_ID = {v["id"]: v for v in FORMATS.values()}
FORMAT_KEYS = list(FORMATS.keys())

# Regras por formato (ícone, texto HTML)
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

_FMT_ICON = {k: v["icon"] for k, v in FORMATS.items()}
_FMT_NAME = {k: v["label"] for k, v in FORMATS.items()}


# ─────────────────────────────────────────────
#  Session bootstrap  (with refresh persistence)
# ─────────────────────────────────────────────

def _init():
    if "data" not in st.session_state:
        st.session_state["data"] = persistence.load()

    if "role" not in st.session_state:
        # Try to restore session from URL query params (survives page refresh)
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
                # Player was removed; clear stale params
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
#  Login screen
# ─────────────────────────────────────────────

def render_login():
    players_dict: dict = st.session_state["data"].get("players", {})
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
            is_first = False

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
                "pin",
                placeholder="••••••••",
                type="password",
                label_visibility="collapsed",
                key="login_pin",
            )

            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            enter = st.button(
                "Entrar  →",
                type="primary", use_container_width=True, key="btn_login",
            )
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
#  Player view  (read-only)
# ─────────────────────────────────────────────

def render_player():
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30_000, limit=None, key="player_refresh")

    name = st.session_state["player_name"]

    # Reload live data on every cycle
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

    ptabs = st.tabs(["🏆  Torneio", "📊  Ranking"])

    with ptabs[0]:
        if t is None:
            # Show history if available
            history = fresh.get("tournament_history", [])
            if history:
                _render_history_section(history, can_edit=False)
            else:
                st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
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
        pos = medals.get(i, f"{i + 1}º")
        gb = s.get("game_balance", 0)
        gb_color = "#16a34a" if gb >= 0 else "#dc2626"
        gb_str = f"+{gb}" if gb > 0 else str(gb)
        wins = s.get("wins", 0)
        total = s.get("matches", 0)
        pct = f"{round(wins / total * 100)}%" if total else "—"
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

    tabs = st.tabs(["🏆  Torneio", "👥  Jogadoras", "📊  Ranking", "⚙️  Config"])
    with tabs[0]:
        _tab_tournament()
    with tabs[1]:
        _tab_players()
    with tabs[2]:
        _tab_ranking()
    with tabs[3]:
        _tab_settings()


# ─────────────────────────────────────────────
#  Ranking helpers
# ─────────────────────────────────────────────

def _extract_standings(t) -> dict:
    """Return {player_name: stats_dict} from any tournament format."""
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


def _register_in_ranking(t) -> None:
    data = st.session_state["data"]
    ranking: dict = data.setdefault("ranking", {})
    standings = _extract_standings(t)

    for player, stats in standings.items():
        if player not in ranking:
            ranking[player] = {
                "tournaments": 0, "matches": 0,
                "wins": 0, "points": 0, "game_balance": 0,
            }
        r = ranking[player]
        r["tournaments"] += 1
        r["matches"]      += stats.get("matches", 0)
        r["wins"]         += stats.get("wins", 0)
        r["points"]       += stats.get("points", 0)
        r["game_balance"] += stats.get("game_balance", 0)

    _persist()


def _archive_tournament(t) -> None:
    """Save a completed tournament to history before clearing it."""
    data = st.session_state["data"]
    history: list = data.setdefault("tournament_history", [])
    n_players = len(getattr(t, "players", getattr(t, "participants", [])))
    history.append({
        "format":      t.format_id,
        "format_name": getattr(t, "format_name", t.format_id),
        "n_players":   n_players,
        "data":        t.to_dict(),
        "archived_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    # Keep last 30 tournaments
    if len(history) > 30:
        history[:] = history[-30:]


# ─────────────────────────────────────────────
#  Tournament history
# ─────────────────────────────────────────────

def _render_history_section(history: list, can_edit: bool = True) -> None:
    """Show past tournaments as clickable expandable cards."""
    section_label("📚 Torneios Anteriores")
    for h in reversed(history):
        fmt_icon  = _FMT_ICON.get(h["format"], "🏆")
        fmt_label = h.get("format_name", _FMT_NAME.get(h["format"], h["format"]))
        n_pl      = h.get("n_players", "?")
        when      = h.get("archived_at", "")
        title     = f"{fmt_icon} {fmt_label}  ·  {n_pl} participantes  ·  {when}"
        with st.expander(title, expanded=False):
            fmt = FORMAT_BY_ID.get(h["format"])
            if fmt:
                try:
                    t_hist = fmt["cls"].from_dict(h["data"])
                    t_hist.render(can_edit=False)
                except Exception as e:
                    st.error(f"Erro ao carregar torneio: {e}")
            else:
                st.warning("Formato desconhecido.")
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)


# ── Tab: Torneio ─────────────────────────────

def _tab_tournament():
    t = st.session_state.get("tournament")
    data = st.session_state["data"]
    history: list = data.get("tournament_history", [])

    if t is None:
        # Past tournaments first
        if history:
            _render_history_section(history, can_edit=True)
        _create_tournament_ui()
    else:
        # Action bar
        _, c2, c3 = st.columns([3.5, 2, 1.5])
        with c2:
            if st.button("📊  Registrar no Ranking", use_container_width=True):
                _register_in_ranking(t)
                st.success("✅ Resultados registrados no Ranking Geral!")
        with c3:
            if st.button("🗑  Encerrar Torneio", use_container_width=True):
                _archive_tournament(t)
                st.session_state["tournament"] = None
                data["tournament"] = None
                _persist()
                st.rerun()
        t.render(can_edit=True)


# ─────────────────────────────────────────────
#  Tournament creation  (reorganized layout)
# ─────────────────────────────────────────────

def _create_tournament_ui():
    players_dict = st.session_state["data"].get("players", {})
    all_players  = sorted(players_dict.keys())

    if "tourn_guests" not in st.session_state:
        st.session_state["tourn_guests"] = []

    st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
    col_l, col_r = st.columns([5, 7], gap="large")

    # ── LEFT — participants + format ──────────────────
    with col_l:
        # Card: Participantes
        with st.container(border=True):
            section_label("👥  Participantes")

            if all_players:
                selected_players = st.multiselect(
                    "Participantes",
                    options=all_players,
                    default=all_players,
                    placeholder="Selecione as participantes...",
                    label_visibility="collapsed",
                    key="tourn_ms",
                )
            else:
                selected_players = []
                st.markdown(
                    '<div style="font-size:.82rem;color:#9b8679;padding:.4rem 0">'
                    'Nenhuma cadastrada. Use <b>Jogadoras</b> ou adicione convidadas abaixo.</div>',
                    unsafe_allow_html=True,
                )

            # Quick guest add
            field_label("Adicionar convidada")
            gi1, gi2 = st.columns([5, 1])
            with gi1:
                guest_in = st.text_input(
                    "g", placeholder="Ex: Rafaela...",
                    label_visibility="collapsed", key="guest_in",
                )
            with gi2:
                if st.button("➕", key="btn_guest", use_container_width=True):
                    g = guest_in.strip()
                    existing = {x.lower() for x in all_players + st.session_state["tourn_guests"]}
                    if g and g.lower() not in existing:
                        st.session_state["tourn_guests"].append(g)
                        st.rerun()

            # Guest chips
            for g in list(st.session_state["tourn_guests"]):
                gc1, gc2 = st.columns([6, 1])
                with gc1:
                    st.markdown(
                        f'<div style="font-size:.84rem;padding:.2rem 0;color:#1a1613">'
                        f'👤 <b>{g}</b></div>',
                        unsafe_allow_html=True,
                    )
                with gc2:
                    if st.button("✕", key=f"rmg_{g}"):
                        st.session_state["tourn_guests"].remove(g)
                        st.rerun()

            # Participant count badge
            total = len(selected_players) + len(st.session_state["tourn_guests"])
            col_c = "#f97316" if total >= 2 else "#dc2626"
            st.markdown(
                f'<div style="display:inline-flex;align-items:center;gap:.5rem;'
                f'background:{col_c}1a;border:1.5px solid {col_c}55;border-radius:100px;'
                f'padding:.3rem .9rem;margin-top:.4rem">'
                f'<span style="font-size:1rem;font-weight:900;color:{col_c}">{total}</span>'
                f'<span style="font-size:.78rem;font-weight:600;color:#3a2e26">'
                f'participante{"s" if total != 1 else ""}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # Card: Format
        with st.container(border=True):
            section_label("🏆  Formato do Torneio")
            fmt_labels = [f"{FORMATS[k]['icon']}  {FORMATS[k]['label']}" for k in FORMAT_KEYS]
            fmt_sel = st.radio(
                "fmt", fmt_labels,
                label_visibility="collapsed", key="tourn_fmt_radio",
            )
            fmt_idx = fmt_labels.index(fmt_sel)
            fmt_id  = FORMAT_KEYS[fmt_idx]

    # ── RIGHT — rules + create button ────────────────
    with col_r:
        fmt = FORMATS[fmt_id]
        render_format_info(fmt["icon"], fmt["label"], fmt["desc"])
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        render_rules_card(_FORMAT_RULES.get(fmt_id, []))

        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

        if st.button("🏆  Criar Torneio", type="primary", use_container_width=True):
            all_selected = list(selected_players) + list(st.session_state["tourn_guests"])
            err = _do_create(all_selected, fmt_id)
            if not err:
                st.session_state["tourn_guests"] = []


def _do_create(players: list, fmt_id: str) -> bool:
    """Create tournament; returns True on error."""
    fmt = FORMATS.get(fmt_id) or FORMATS[FORMAT_KEYS[0]]
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


# ── Tab: Jogadoras ───────────────────────────

def _tab_players():
    data = st.session_state["data"]
    players: dict = data.setdefault("players", {})

    h1, h2 = st.columns([5, 1])
    with h1:
        section_label("Jogadoras Cadastradas")
    with h2:
        n_total = len(players)
        st.markdown(
            f'<div style="background:#f97316;color:white;border-radius:20px;'
            f'padding:.2rem .9rem;text-align:center;font-weight:800;'
            f'font-size:.95rem;margin-top:.25rem">{n_total}</div>',
            unsafe_allow_html=True,
        )

    if not players:
        st.markdown(
            '<div style="text-align:center;padding:2.5rem 1rem;color:#c49070;font-size:.9rem">'
            '🏖️  Nenhuma jogadora cadastrada ainda.<br>'
            '<span style="font-size:.8rem">Adicione abaixo para começar.</span></div>',
            unsafe_allow_html=True,
        )
    else:
        player_list = sorted(players.items())
        for i in range(0, len(player_list), 2):
            cols = st.columns(2, gap="small")
            for j, (name, info) in enumerate(player_list[i : i + 2]):
                with cols[j]:
                    has_pin = bool(info.get("pin_hash"))
                    with st.container(border=True):
                        top1, top2 = st.columns([3, 1])
                        with top1:
                            badge = (
                                '🔒 <span style="color:#16a34a;font-size:.73rem">PIN definido</span>'
                                if has_pin else
                                '⚠️ <span style="color:#dc2626;font-size:.73rem">Sem PIN</span>'
                            )
                            st.markdown(
                                f'<div style="font-weight:700;font-size:.92rem;color:#1a1a1a">'
                                f'{name}</div>'
                                f'<div style="margin-top:.15rem">{badge}</div>',
                                unsafe_allow_html=True,
                            )
                        with top2:
                            if st.button("✕", key=f"del_{name}", help=f"Remover {name}"):
                                del players[name]
                                _persist()
                                st.rerun()
                        if has_pin:
                            if st.button("🔓 Redefinir PIN", key=f"rst_{name}",
                                         use_container_width=True):
                                players[name]["pin_hash"] = None
                                _persist()
                                st.success(f"PIN de {name} redefinido.")
                                st.rerun()

        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.button("🔓  Redefinir TODOS os PINs", use_container_width=True):
            for nm in players:
                players[nm]["pin_hash"] = None
            _persist()
            st.success("Todos os PINs foram redefinidos.")

    st.markdown("---")
    section_label("Adicionar Jogadoras")

    tab_single, tab_bulk = st.tabs(["➕  Uma por vez", "📋  Importar lista"])

    with tab_single:
        with st.form("add_player", clear_on_submit=True):
            new_name = st.text_input("Nome", placeholder="Ex: Ana Paula")
            if st.form_submit_button("➕  Adicionar", type="primary"):
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

    with tab_bulk:
        st.caption("Cole vários nomes de uma vez — um por linha.")
        bulk_raw = st.text_area(
            "bulk",
            placeholder="Ana Paula\nBia\nCarol\nDani\nFernanda",
            height=130,
            label_visibility="collapsed",
            key="bulk_add",
        )
        if st.button("📋  Importar Lista", type="primary", use_container_width=True):
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
                st.warning(f"⚠️ Já existiam (ignoradas): {', '.join(skipped)}")
            if added:
                st.rerun()


# ── Tab: Ranking ─────────────────────────────

def _tab_ranking():
    data = st.session_state["data"]
    ranking: dict = data.get("ranking", {})

    h1, h2 = st.columns([5, 1])
    with h1:
        section_label("📊  Ranking Geral")
    with h2:
        if ranking and st.button("🗑 Limpar", use_container_width=True,
                                 help="Apaga todo o histórico de ranking"):
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
        pos = medals.get(i, f"{i + 1}º")
        gb = s.get("game_balance", 0)
        gb_color = "#16a34a" if gb >= 0 else "#dc2626"
        gb_str = f"+{gb}" if gb > 0 else str(gb)
        total = s.get("matches", 0)
        wins  = s.get("wins", 0)
        pct   = f"{round(wins / total * 100)}%" if total else "—"

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


# ── Tab: Config ──────────────────────────────

def _tab_settings():
    section_label("Alterar Senha Administrativa")
    with st.form("change_pwd"):
        cur  = st.text_input("Senha atual", type="password")
        new1 = st.text_input("Nova senha", type="password")
        new2 = st.text_input("Confirme a nova senha", type="password")
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
    section_label("Histórico de Torneios")
    data = st.session_state["data"]
    history: list = data.get("tournament_history", [])
    if history:
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.caption(f"{len(history)} torneio(s) arquivado(s)")
        with col_b:
            if st.button("🗑 Limpar histórico", use_container_width=True):
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
