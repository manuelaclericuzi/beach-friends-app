import math
from typing import List, Dict, Optional

import streamlit as st

from .base_format import BaseTournamentFormat
from .scoring import (MatchScore, MatchResult, compute_result, is_valid_score,
                      score_to_dict, result_to_dict, dict_to_score, dict_to_result)
from .rainha_da_praia import _save


def _bracket_size(n: int) -> int:
    return 2 ** math.ceil(math.log2(max(n, 2)))


def _round_name(n_matches: int) -> str:
    return {1: "Final", 2: "Semifinal", 4: "Quartas de Final",
            8: "Oitavas de Final"}.get(n_matches, f"Rodada de {n_matches * 2}")


def _build_bracket(participants: List[Optional[str]]) -> List[Dict]:
    """Create the full bracket skeleton from a seeded participant list."""
    n = len(participants)  # must be power of 2
    rounds = []
    # First round
    matches = []
    for i in range(0, n, 2):
        pa, pb = participants[i], participants[i + 1]
        is_bye = pa is None or pb is None
        winner = (pa if pb is None else pb) if is_bye else None
        matches.append({"id": f"r0m{i//2}", "p_a": pa, "p_b": pb,
                        "winner": winner, "result": None, "score": None, "is_bye": is_bye})
    rounds.append({"name": _round_name(n // 2), "matches": matches, "completed": False})

    # Remaining rounds (empty, filled as bracket progresses)
    size = n // 4
    r = 1
    while size >= 1:
        rounds.append({
            "name": _round_name(size),
            "matches": [
                {"id": f"r{r}m{i}", "p_a": None, "p_b": None,
                 "winner": None, "result": None, "score": None, "is_bye": False}
                for i in range(size)
            ],
            "completed": False,
        })
        size //= 2
        r += 1

    return rounds


def _propagate(rounds: List[Dict]) -> None:
    """Advance winners through the bracket; auto-resolve byes."""
    for r_idx in range(len(rounds) - 1):
        rnd = rounds[r_idx]
        next_rnd = rounds[r_idx + 1]
        for m_idx, m in enumerate(rnd["matches"]):
            if m["winner"] is not None:
                slot = m_idx // 2
                if m_idx % 2 == 0:
                    next_rnd["matches"][slot]["p_a"] = m["winner"]
                else:
                    next_rnd["matches"][slot]["p_b"] = m["winner"]
        # Auto-resolve byes in next round
        for nm in next_rnd["matches"]:
            if nm["winner"] is None:
                if nm["p_a"] is None and nm["p_b"] is not None:
                    nm["winner"] = nm["p_b"]; nm["is_bye"] = True
                elif nm["p_b"] is None and nm["p_a"] is not None:
                    nm["winner"] = nm["p_a"]; nm["is_bye"] = True
        # Mark current round complete if all decided
        if all(m["winner"] is not None for m in rnd["matches"]):
            rnd["completed"] = True


# ─────────────────────────────────────────────
#  Format class
# ─────────────────────────────────────────────

class MataMata(BaseTournamentFormat):
    format_id = "mata_mata"
    format_name = "Mata-Mata"
    format_description = (
        "Chaveamento eliminatório com avanço automático. "
        "Administrador pode usar duplas ou participantes individuais."
    )
    min_players = 2
    requires_even = False

    def __init__(self, participants: List[str]):
        self.participants = participants
        self.phase = "setup"          # "setup" | "bracket"
        self.rounds: List[Dict] = []
        self.current_round_idx = 0
        self.champion: Optional[str] = None
        self.tournament_date: str = ""
        # setup state
        self._entries: List[str] = []

    # ── serialisation ───────────────────────────

    def to_dict(self) -> Dict:
        rounds_s = []
        for rnd in self.rounds:
            matches_s = [
                {**m,
                 "result": result_to_dict(m["result"]) if m["result"] else None,
                 "score": score_to_dict(m["score"]) if m["score"] else None}
                for m in rnd["matches"]
            ]
            rounds_s.append({**rnd, "matches": matches_s})
        return {
            "participants": self.participants,
            "phase": self.phase,
            "rounds": rounds_s,
            "current_round_idx": self.current_round_idx,
            "champion": self.champion,
            "entries": self._entries,
            "tournament_date": self.tournament_date,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "MataMata":
        obj = cls.__new__(cls)
        obj.participants = d["participants"]
        obj.phase = d["phase"]
        obj.current_round_idx = d["current_round_idx"]
        obj.champion = d["champion"]
        obj.tournament_date = d.get("tournament_date", "")
        obj._entries = d.get("entries", [])
        rounds = []
        for rnd in d["rounds"]:
            matches = [
                {**m,
                 "result": dict_to_result(m["result"]) if m["result"] else None,
                 "score": dict_to_score(m["score"]) if m["score"] else None}
                for m in rnd["matches"]
            ]
            rounds.append({**rnd, "matches": matches})
        obj.rounds = rounds
        return obj

    # ── public API ───────────────────────────────

    def start_bracket(self, entries: List[str]) -> Optional[str]:
        if len(entries) < 2:
            return "Mínimo de 2 participantes."
        dupes = len(entries) != len(set(entries))
        if dupes:
            return "Há nomes duplicados."
        self._entries = entries
        bs = _bracket_size(len(entries))
        seeded = entries + [None] * (bs - len(entries))
        self.rounds = _build_bracket(seeded)
        _propagate(self.rounds)
        self.phase = "bracket"
        return None

    def submit_match(self, round_idx: int, match_idx: int, score: MatchScore) -> None:
        m = self.rounds[round_idx]["matches"][match_idx]
        result = compute_result(score)
        m["result"] = result
        m["score"] = score
        m["winner"] = m["p_a"] if result.winner == "A" else m["p_b"]
        _propagate(self.rounds)
        # Check if last round is done
        last = self.rounds[-1]
        if last["completed"] and last["matches"][0]["winner"]:
            self.champion = last["matches"][0]["winner"]

    # ── render ───────────────────────────────────

    def render(self, can_edit: bool = False) -> None:
        if self.phase == "setup":
            if can_edit:
                self._render_setup()
            else:
                st.info("Aguardando o administrador iniciar o chaveamento.")
            return
        self._render_bracket(can_edit)

    def _render_setup(self):
        from .ui_components import section_label
        st.markdown(
            '<div class="app-header"><div class="header-icon">⚔️</div>'
            '<h1>Mata-Mata</h1>'
            '<p class="subtitle">Configure os participantes do chaveamento</p></div>',
            unsafe_allow_html=True,
        )
        section_label("Participantes  (um por linha — pode ser jogadora ou dupla)")

        suggestions = "\n".join(self.participants)
        raw = st.text_area("Participantes", suggestions, height=200,
                           label_visibility="collapsed")

        st.caption("Dica: para duplas, escreva  'Ana & Bia'. "
                   "Byes serão adicionados automaticamente se necessário.")

        if st.button("🏆  Gerar Chaveamento", type="primary", use_container_width=True):
            entries = [e.strip() for e in raw.splitlines() if e.strip()]
            err = self.start_bracket(entries)
            if err:
                st.error(err)
            else:
                _save()
                st.rerun()

    def _render_bracket(self, can_edit: bool):
        from .ui_components import render_banner

        # Header
        total_r = len(self.rounds)
        active_r = next((i for i, r in enumerate(self.rounds) if not r["completed"]), total_r)
        render_banner(self.format_name, len(self._entries), active_r, total_r)

        if self.champion:
            st.markdown(
                f'<div class="champion-banner">🏆 Campeã: <b>{self.champion}</b></div>',
                unsafe_allow_html=True,
            )

        tabs = st.tabs(["⚔️ Chaveamento", "🌳 Árvore"])
        with tabs[0]:
            self._render_rounds(can_edit)
        with tabs[1]:
            self._render_tree()

    def _render_rounds(self, can_edit: bool):
        from .ui_components import round_done_banner, match_card_label

        for r_idx, rnd in enumerate(self.rounds):
            st.markdown(f"#### {rnd['name']}")

            for m_idx, m in enumerate(rnd["matches"]):
                if m["is_bye"] and m["winner"]:
                    label_a = m["p_a"] or "—"
                    label_b = m["p_b"] or "—"
                    st.markdown(
                        f"<div style='color:#aaa;font-size:.85rem;margin:.3rem 0'>"
                        f"BYE: <b>{m['winner']}</b> avança  "
                        f"({label_a} vs {label_b})</div>",
                        unsafe_allow_html=True,
                    )
                    continue

                pa = m["p_a"] or "—"
                pb = m["p_b"] or "—"

                if m["winner"]:
                    win_a = m["winner"] == m["p_a"]
                    sc = m["score"]
                    sc_str = f"{sc.games_a}×{sc.games_b}" if sc else ""
                    if m["result"] and m["result"].is_super_tie:
                        sc_str += " (S.T.)"
                    st.markdown(
                        f"<div class='bracket-match done'>"
                        f"<span class='{'bw' if win_a else 'bl'}'>{pa}</span>"
                        f"<span class='bscore'>{sc_str}</span>"
                        f"<span class='{'bl' if win_a else 'bw'}'>{pb}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                elif pa != "—" and pb != "—" and can_edit:
                    # Score input
                    with st.form(f"mm_{r_idx}_{m_idx}"):
                        match_card_label(m_idx + 1)
                        c1, c2, c3, c4, c5 = st.columns([3, 1, 0.4, 1, 3])
                        with c1:
                            st.markdown(f"<div class='team-label'><b>{pa}</b></div>",
                                        unsafe_allow_html=True)
                        with c2:
                            ga = st.number_input("A", 0, 4, 0, key=f"mm_ga_{r_idx}_{m_idx}",
                                                 label_visibility="collapsed")
                        with c3:
                            st.markdown("<div style='text-align:center;padding-top:6px;"
                                        "font-size:1.1rem;font-weight:700;color:#bbb'>×</div>",
                                        unsafe_allow_html=True)
                        with c4:
                            gb = st.number_input("B", 0, 4, 0, key=f"mm_gb_{r_idx}_{m_idx}",
                                                 label_visibility="collapsed")
                        with c5:
                            st.markdown(f"<div class='team-label' style='text-align:right'>"
                                        f"<b>{pb}</b></div>", unsafe_allow_html=True)
                        st_sel = st.selectbox(
                            "Super Tie-Break",
                            ["— sem super tie", f"🏆 {pa}", f"🏆 {pb}"],
                            key=f"mm_st_{r_idx}_{m_idx}",
                        )
                        submitted = st.form_submit_button(
                            "Registrar", type="primary", use_container_width=True
                        )
                    if submitted:
                        self._on_submit(r_idx, m_idx, ga, gb, st_sel, pa, pb)
                elif pa != "—" and pb != "—":
                    st.markdown(
                        f"<div class='bracket-match'><span>{pa}</span>"
                        f"<span class='bscore'>vs</span>"
                        f"<span style='text-align:right'>{pb}</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='color:#ccc;font-size:.85rem;margin:.3rem 0'>"
                        f"Aguardando partidas anteriores...</div>",
                        unsafe_allow_html=True,
                    )
            st.markdown("---")

    def _on_submit(self, r_idx, m_idx, ga, gb, st_sel, pa, pb):
        if not is_valid_score(ga, gb):
            st.error(f"Placar {ga}×{gb} inválido.")
            return
        stw = None
        if ga == 3 and gb == 3:
            if st_sel == "— sem super tie":
                st.error("3×3 exige indicar o Super Tie-Break.")
                return
            stw = "A" if pa in st_sel else "B"
        self.submit_match(r_idx, m_idx, MatchScore(ga, gb, stw))
        _save()
        st.rerun()

    def _render_tree(self):
        """Visual bracket tree using HTML."""
        rounds_html = ""
        for rnd in self.rounds:
            matches_html = ""
            for m in rnd["matches"]:
                pa = m["p_a"] or "—"
                pb = m["p_b"] or "—"
                win = m.get("winner")
                a_style = "font-weight:700;color:#f97316" if win and win == m["p_a"] else ""
                b_style = "font-weight:700;color:#f97316" if win and win == m["p_b"] else ""
                matches_html += f"""
                <div class="tree-match">
                    <div class="tree-player {'tree-winner' if win == m['p_a'] else ''}">{pa}</div>
                    <div class="tree-player {'tree-winner' if win == m['p_b'] else ''}">{pb}</div>
                </div>"""
            rounds_html += f"""
            <div class="tree-round">
                <div class="tree-round-name">{rnd['name']}</div>
                {matches_html}
            </div>"""

        st.markdown(f'<div class="bracket-tree">{rounds_html}</div>',
                    unsafe_allow_html=True)
