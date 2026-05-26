import streamlit as st

st.set_page_config(
    page_title="Beach&Friends",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from modules.ui_components import (apply_custom_css, logo_header, hero,
                                    field_label, section_label, render_ranking_section)
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
    "🏖️  Super 8 / Rainha da Praia": {
        "cls": RainhaDaPraia, "id": "rainha_da_praia",
        "desc": "Parceiras rotacionam com matriz matemática perfeita. Pontuação individual.",
        "min": 4, "even": False,
    },
    "🤝  Duplas Fixas — Pontos Corridos": {
        "cls": DuplasFixas, "id": "duplas_fixas",
        "desc": "Duplas fixas disputam um round-robin completo entre si.",
        "min": 4, "even": True,
    },
    "⚔️  Mata-Mata — Chaveamento": {
        "cls": MataMata, "id": "mata_mata",
        "desc": "Árvore eliminatória interativa com avanço automático da vencedora.",
        "min": 2, "even": False,
    },
}
FORMAT_BY_ID = {v["id"]: v for v in FORMATS.values()}


# ─────────────────────────────────────────────
#  Session bootstrap
# ─────────────────────────────────────────────

def _init():
    if "data" not in st.session_state:
        st.session_state["data"] = persistence.load()
    if "role" not in st.session_state:
        st.session_state["role"] = None
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
    st.rerun()


# ─────────────────────────────────────────────
#  Login screen
# ─────────────────────────────────────────────

def render_login():
    players_dict: dict = st.session_state["data"].get("players", {})
    player_names = sorted(players_dict.keys())

    # Three-column centering
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.container(border=True):
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            logo_header("Beach&Friends", "Placar & Chaveamento Inteligente")

            field_label("Quem é você?")
            role_sel = st.selectbox(
                "role", ["Jogadora do Torneio", "Administradora"],
                label_visibility="collapsed", key="login_role",
            )

            player_sel = None
            is_first = False
            if role_sel == "Jogadora do Torneio":
                field_label("Escolha seu nome")
                if player_names:
                    player_sel = st.selectbox(
                        "player", player_names,
                        label_visibility="collapsed", key="login_player",
                    )
                    is_first = not players_dict[player_sel].get("pin_hash")
                    if is_first:
                        st.markdown(
                            '<div class="bf-hint">✨ Primeiro acesso! '
                            'Crie abaixo seu <b>PIN de 4+ dígitos</b>.</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Nenhuma jogadora cadastrada ainda.")
                    st.stop()

            field_label("Criar PIN" if is_first else "PIN de Acesso")
            pin_input = st.text_input(
                "pin",
                placeholder="🔒  Digite sua senha ou PIN",
                type="password",
                label_visibility="collapsed",
                key="login_pin",
            )

            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
            enter = st.button(
                "Entrar no Torneio  →",
                type="primary", use_container_width=True,
            )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    if enter:
        _handle_login(role_sel, player_sel, pin_input, players_dict, is_first)


def _handle_login(role_sel, player_sel, pin, players_dict, is_first):
    pin = pin.strip()
    if not pin:
        st.error("Digite sua senha ou PIN.")
        return

    if role_sel == "Administradora":
        if verify(pin, st.session_state["data"]["admin_password_hash"]):
            st.session_state["role"] = "admin"
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
        st.rerun()
    else:
        stored = players_dict[player_sel].get("pin_hash")
        if verify(pin, stored):
            st.session_state["role"] = "player"
            st.session_state["player_name"] = player_sel
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
    # Auto-refresh every 30 s so players see scores in real time
    st_autorefresh(interval=30_000, limit=None, key="player_refresh")

    name = st.session_state["player_name"]
    t = st.session_state.get("tournament")

    # Always reload from storage on each auto-refresh cycle
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

    # Top bar
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown(f'<div style="padding:.6rem 0">'
                    f'<span class="bf-badge">👤 {name}</span>'
                    f'<span style="font-size:.72rem;color:#c49070;margin-left:.8rem">'
                    f'⟳ atualiza automaticamente</span></div>',
                    unsafe_allow_html=True)
    with c2:
        if st.button("Sair", use_container_width=True):
            _logout()

    if t is None:
        st.markdown("<div style='height:3rem'></div>", unsafe_allow_html=True)
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
        return

    t.render(can_edit=False)


# ─────────────────────────────────────────────
#  Admin view
# ─────────────────────────────────────────────

def render_admin():
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown('<div style="padding:.6rem 0">'
                    '<span class="bf-badge">🔑 Administradora</span></div>',
                    unsafe_allow_html=True)
    with c2:
        if st.button("Sair", use_container_width=True):
            _logout()

    tabs = st.tabs(["🏆  Torneio", "👥  Jogadoras", "⚙️  Config"])
    with tabs[0]:
        _tab_tournament()
    with tabs[1]:
        _tab_players()
    with tabs[2]:
        _tab_settings()


# ── Tab: Torneio ─────────────────────────────

def _tab_tournament():
    t = st.session_state.get("tournament")
    if t is None:
        _create_tournament_ui()
    else:
        c1, c2 = st.columns([5, 1])
        with c2:
            if st.button("🗑 Encerrar Torneio", use_container_width=True):
                st.session_state["tournament"] = None
                st.session_state["data"]["tournament"] = None
                _persist()
                st.rerun()
        t.render(can_edit=True)


def _create_tournament_ui():
    hero("Beach&Friends", "Placar & Chaveamento Inteligente")

    players_dict = st.session_state["data"].get("players", {})
    all_players = sorted(players_dict.keys())

    col_l, col_r = st.columns([3, 2], gap="large")

    selected_players: list = []
    extra_raw = ""

    with col_l:
        section_label("👥  Jogadoras no Torneio")

        if not all_players:
            st.markdown(
                '<div style="background:#fff7ed;border:2px dashed #f97316;'
                'border-radius:14px;padding:1.4rem;text-align:center;'
                'font-size:.88rem;color:#c2410c;line-height:1.8">'
                '⚠️  Nenhuma jogadora cadastrada.<br>'
                '<b>Vá até a aba Jogadoras para adicionar.</b></div>',
                unsafe_allow_html=True,
            )
        else:
            selected_players = st.multiselect(
                "Participantes",
                options=all_players,
                default=all_players,
                placeholder="Escolha as participantes...",
                label_visibility="collapsed",
                key="tourn_players",
            )

            n = len(selected_players)
            ok_color = "#f97316" if n >= 4 else "#dc2626"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:.5rem;margin:.3rem 0 .5rem">'
                f'<div style="background:{ok_color};color:white;border-radius:20px;'
                f'padding:.15rem .75rem;font-weight:800;font-size:.83rem">{n}</div>'
                f'<span style="font-size:.82rem;color:#92400e">'
                f'jogadora{"s" if n != 1 else ""} selecionada{"s" if n != 1 else ""}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with st.expander("➕  Adicionar jogadora avulsa (visitante)"):
            st.caption("Não precisa de cadastro — participará apenas deste torneio.")
            extra_raw = st.text_area(
                "extra",
                placeholder="Uma por linha:\nEx: Visitante\nEx: Convidada",
                height=90,
                label_visibility="collapsed",
                key="tourn_extra",
            )

    with col_r:
        section_label("🏆  Formato do Torneio")
        fmt_name = st.selectbox(
            "formato", list(FORMATS.keys()),
            label_visibility="collapsed",
        )
        fmt = FORMATS[fmt_name]

        st.markdown(
            f'<div style="background:#fff7ed;border-left:4px solid #f97316;'
            f'border-radius:12px;padding:.9rem 1.1rem;margin:.6rem 0;'
            f'font-size:.83rem;color:#c2410c;font-weight:500">'
            f'{fmt["desc"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="background:#fef9f4;border:1.5px solid #f0d4b8;'
            'border-radius:12px;padding:.9rem 1.1rem;'
            'font-size:.8rem;color:#92400e;line-height:1.8">'
            '<b style="font-weight:800">📋 Regras</b><br>'
            '🎾 Melhor de 4 games<br>'
            '🔥 Empate 2×2 → Super Tie-Break (10 pts)<br>'
            '🏅 Vitória = <b>3 pts</b> · Derrota = <b>0 pts</b><br>'
            '⚡ Super Tie: saldo computado como <b>3×2</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    _, btn, _ = st.columns([2, 1, 2])
    with btn:
        if st.button("🏆  Criar Torneio", type="primary", use_container_width=True):
            extra_players = [p.strip() for p in extra_raw.splitlines() if p.strip()]
            _do_create(list(selected_players) + extra_players, fmt_name)


def _do_create(players: list, fmt_name: str):
    fmt = FORMATS[fmt_name]
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
        return

    t = fmt["cls"](players)
    st.session_state["tournament"] = t
    st.session_state["data"]["tournament"] = {"format": t.format_id, "data": t.to_dict()}
    _persist()
    st.rerun()


# ── Tab: Jogadoras ───────────────────────────

def _tab_players():
    data = st.session_state["data"]
    players: dict = data.setdefault("players", {})

    # ── Header com contador ──────────────────
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
        # Grid 2 colunas de cards
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
