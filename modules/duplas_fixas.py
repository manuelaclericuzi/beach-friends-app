from typing import List, Dict, Tuple, Optional
import streamlit as st

from .base_format import BaseTournamentFormat
from .scoring import (MatchScore, MatchResult, compute_result, compute_ranking,
                      empty_stats, is_valid_score,
                      score_to_dict, result_to_dict, dict_to_score, dict_to_result)
from .rainha_da_praia import _render_score_form, _render_round_readonly, _save


# ─────────────────────────────────────────────
#  Round-robin schedule (Berger)
# ─────────────────────────────────────────────

def _round_robin(teams: List[str]) -> List[List[Tuple[str, str]]]:
    n = len(teams)
    if n % 2 == 1:
        teams = teams + ["__BYE__"]
        n += 1
    rotation = list(range(1, n))
    rounds = []
    for _ in range(n - 1):
        current = [0] + rotation
        matches = [
            (teams[current[i]], teams[current[n - 1 - i]])
            for i in range(n // 2)
            if "__BYE__" not in (teams[current[i]], teams[current[n - 1 - i]])
        ]
        rounds.append(matches)
        rotation = [rotation[-1]] + rotation[:-1]
    return rounds


# ─────────────────────────────────────────────
#  Format class
# ─────────────────────────────────────────────

class DuplasFixas(BaseTournamentFormat):
    format_id = "duplas_fixas"
    format_name = "Duplas Fixas"
    format_description = (
        "Duplas fixas disputam um round-robin completo (pontos corridos)."
    )
    min_players = 4
    requires_even = True

    def __init__(self, players: List[str]):
        self.players = players
        self.phase: str = "formation"
        self.teams: List[Dict] = []
        self.team_stats: Dict[str, Dict] = {}
        self.rounds: List[Dict] = []
        self.current_round_idx: int = 0
        self._suggested: List[Tuple[str, str]] = [
            (players[i], players[i + 1]) for i in range(0, len(players) - 1, 2)
        ]

    # ── serialisation ───────────────────────────

    def to_dict(self) -> Dict:
        rounds_s = []
        for rnd in self.rounds:
            matches_s = [
                {
                    "team_a": m["team_a"], "team_b": m["team_b"],
                    "result": result_to_dict(m["result"]) if m["result"] else None,
                    "score": score_to_dict(m["score"]) if m["score"] else None,
                }
                for m in rnd["matches"]
            ]
            rounds_s.append({**rnd, "matches": matches_s})
        return {
            "players": self.players,
            "phase": self.phase,
            "teams": self.teams,
            "team_stats": self.team_stats,
            "rounds": rounds_s,
            "current_round_idx": self.current_round_idx,
            "suggested": [list(p) for p in self._suggested],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "DuplasFixas":
        obj = cls.__new__(cls)
        obj.players = d["players"]
        obj.phase = d["phase"]
        obj.teams = d["teams"]
        obj.team_stats = d["team_stats"]
        obj.current_round_idx = d["current_round_idx"]
        obj._suggested = [tuple(p) for p in d.get("suggested", [])]
        rounds = []
        for rnd in d["rounds"]:
            matches = [
                {
                    "team_a": m["team_a"], "team_b": m["team_b"],
                    "result": dict_to_result(m["result"]) if m["result"] else None,
                    "score": dict_to_score(m["score"]) if m["score"] else None,
                }
                for m in rnd["matches"]
            ]
            rounds.append({**rnd, "matches": matches})
        obj.rounds = rounds
        return obj

    # ── public API ───────────────────────────────

    def confirm_teams(self, pairs: List[Tuple[str, str]]) -> Optional[str]:
        all_p = [p for t in pairs for p in t]
        if len(set(all_p)) < len(all_p):
            return "Cada jogadora pode estar em apenas uma dupla."
        if set(all_p) != set(self.players):
            return "Todas as jogadoras devem ser alocadas."

        self.teams = [{"name": f"{p1} & {p2}", "players": [p1, p2]} for p1, p2 in pairs]
        self.team_stats = {t["name"]: empty_stats() for t in self.teams}

        team_names = [t["name"] for t in self.teams]
        self.rounds = [
            {
                "number": i + 1,
                "matches": [
                    {"team_a": ta, "team_b": tb, "result": None, "score": None}
                    for ta, tb in matches
                ],
                "completed": False,
            }
            for i, matches in enumerate(_round_robin(team_names))
        ]
        self.phase = "tournament"
        return None

    def submit_round(self, round_idx: int, scores: List[MatchScore]) -> None:
        rnd = self.rounds[round_idx]
        for match, score in zip(rnd["matches"], scores):
            result = compute_result(score)
            match["result"] = result
            match["score"] = score
            self._apply(match["team_a"], match["team_b"], result)
        rnd["completed"] = True

    def get_ranking(self):
        return compute_ranking(self.team_stats)

    def _apply(self, name_a: str, name_b: str, r: MatchResult):
        sa, sb = self.team_stats[name_a], self.team_stats[name_b]
        sa["matches"] += 1; sa["points"] += r.points_a
        sa["games_pro"] += r.games_pro_a; sa["games_against"] += r.games_pro_b
        sa["game_balance"] += r.game_balance_a
        if r.winner == "A": sa["wins"] += 1

        sb["matches"] += 1; sb["points"] += r.points_b
        sb["games_pro"] += r.games_pro_b; sb["games_against"] += r.games_pro_a
        sb["game_balance"] += r.game_balance_b
        if r.winner == "B": sb["wins"] += 1

    # ── render ───────────────────────────────────

    def render(self, can_edit: bool = False) -> None:
        if self.phase == "formation":
            if can_edit:
                self._render_formation()
            else:
                st.info("Aguardando o administrador confirmar as duplas.")
            return

        from .ui_components import render_banner, render_ranking_section, render_history_match
        render_banner(self.format_name, len(self.players),
                      self.current_round_idx, len(self.rounds))

        tabs = st.tabs(["🏸 Rodada Atual", "🏆 Ranking", "📋 Histórico"])
        with tabs[0]:
            self._render_round(can_edit)
        with tabs[1]:
            render_ranking_section(self.get_ranking(), "team")
        with tabs[2]:
            self._render_history()

    def _render_formation(self):
        from .ui_components import section_label
        st.markdown(
            '<div class="app-header"><div class="header-icon">🎾</div>'
            '<h1>Duplas Fixas</h1>'
            '<p class="subtitle">Monte as duplas para iniciar o torneio</p></div>',
            unsafe_allow_html=True,
        )
        section_label("Formação das Duplas")
        with st.form("team_formation"):
            pairs = []
            for i in range(len(self.players) // 2):
                c1, c2 = st.columns(2)
                s1 = self._suggested[i][0] if i < len(self._suggested) else self.players[0]
                s2 = self._suggested[i][1] if i < len(self._suggested) else self.players[1]
                with c1:
                    p1 = st.selectbox(f"Dupla {i+1} — Jogadora 1", self.players,
                                      index=self.players.index(s1), key=f"tf_p1_{i}")
                with c2:
                    p2 = st.selectbox(f"Dupla {i+1} — Jogadora 2", self.players,
                                      index=self.players.index(s2), key=f"tf_p2_{i}")
                pairs.append((p1, p2))
            submitted = st.form_submit_button(
                "🏆  Confirmar Duplas e Gerar Tabela",
                type="primary", use_container_width=True
            )
        if submitted:
            err = self.confirm_teams(pairs)
            if err:
                st.error(err)
            else:
                _save()
                st.rerun()

    def _render_round(self, can_edit: bool):
        from .ui_components import bye_notice, round_done_banner
        idx = self.current_round_idx
        if idx >= len(self.rounds):
            round_done_banner("🏁 Torneio encerrado!")
            return

        rnd = self.rounds[idx]
        # Resolve display names → player names via self.teams
        display_matches = []
        for m in rnd["matches"]:
            ta_info = next((t["players"] for t in self.teams if t["name"] == m["team_a"]), None)
            tb_info = next((t["players"] for t in self.teams if t["name"] == m["team_b"]), None)
            display_matches.append({
                **m,
                "team_a": tuple(ta_info) if ta_info else m["team_a"],
                "team_b": tuple(tb_info) if tb_info else m["team_b"],
                "_name_a": m["team_a"],
                "_name_b": m["team_b"],
            })

        st.progress(idx / len(self.rounds),
                    text=f"Rodada {rnd['number']} de {len(self.rounds)}")

        if rnd["completed"]:
            round_done_banner()
            if can_edit:
                if st.button("▶ Próxima Rodada", type="primary", use_container_width=True):
                    self.current_round_idx += 1
                    _save()
                    st.rerun()
            return

        if not can_edit:
            _render_round_readonly({"matches": display_matches})
            return

        # Build adapted matches with display teams but original names for scoring
        def on_submit(scores):
            self.submit_round(idx, scores)
            _save()
            st.rerun()

        _render_score_form(f"df_{idx}", display_matches, on_submit)

    def _render_history(self):
        from .ui_components import render_history_match
        done = [r for r in self.rounds if r["completed"]]
        if not done:
            st.info("Nenhuma rodada concluída ainda.")
            return
        for rnd in done:
            with st.expander(f"Rodada {rnd['number']}", expanded=False):
                for m in rnd["matches"]:
                    if m["result"]:
                        ta_info = next((t["players"] for t in self.teams if t["name"] == m["team_a"]), None)
                        tb_info = next((t["players"] for t in self.teams if t["name"] == m["team_b"]), None)
                        ta = tuple(ta_info) if ta_info else m["team_a"]
                        tb = tuple(tb_info) if tb_info else m["team_b"]
                        render_history_match(ta, tb, m["result"], m["score"])
