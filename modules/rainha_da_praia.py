import random
from itertools import combinations
from typing import List, Dict, Tuple, Optional

import streamlit as st

from .base_format import BaseTournamentFormat
from .scoring import (MatchScore, MatchResult, compute_result, compute_ranking,
                      empty_stats, is_valid_score,
                      score_to_dict, result_to_dict, dict_to_score, dict_to_result)


# ─────────────────────────────────────────────
#  Perfect Super 8 schedule  (8 players, 7 rounds, zero repeated partnerships)
#  Indices into the players list.
# ─────────────────────────────────────────────

_SUPER8: List[List[Tuple]] = [
    [((0, 1), (2, 3)), ((4, 5), (6, 7))],
    [((0, 2), (1, 3)), ((4, 6), (5, 7))],
    [((0, 3), (1, 2)), ((4, 7), (5, 6))],
    [((0, 4), (1, 5)), ((2, 6), (3, 7))],
    [((0, 5), (1, 4)), ((2, 7), (3, 6))],
    [((0, 6), (1, 7)), ((2, 4), (3, 5))],
    [((0, 7), (1, 6)), ((2, 5), (3, 4))],
]

# Perfect schedule for 4 players (all 3 possible pairings)
_SUPER4: List[List[Tuple]] = [
    [((0, 1), (2, 3))],
    [((0, 2), (1, 3))],
    [((0, 3), (1, 2))],
]


# ─────────────────────────────────────────────
#  General greedy schedule (any N ≥ 4)
# ─────────────────────────────────────────────

def _greedy_round(players: List[str], pcount: Dict[Tuple, int], tries: int = 400):
    n = len(players)
    n_active = n - (n % 4)
    if n_active < 4:
        return [], players[:]

    best_matches, best_bye, best_score = None, [], float("inf")
    for _ in range(tries):
        s = players[:]
        random.shuffle(s)
        active, bye = s[:n_active], s[n_active:]
        arr = []
        score = 0
        for i in range(0, n_active, 4):
            t1 = (active[i], active[i + 1])
            t2 = (active[i + 2], active[i + 3])
            score += pcount.get(tuple(sorted(t1)), 0) ** 2
            score += pcount.get(tuple(sorted(t2)), 0) ** 2
            arr.append((t1, t2))
        if score < best_score:
            best_score, best_matches, best_bye = score, arr, bye

    matches = [
        {"team_a": t1, "team_b": t2, "result": None, "score": None}
        for t1, t2 in (best_matches or [])
    ]
    return matches, best_bye


def _build_rounds(players: List[str], num_rounds: int) -> Tuple[List[Dict], Dict]:
    n = len(players)
    pcount: Dict[Tuple, int] = {tuple(sorted(p)): 0 for p in combinations(players, 2)}

    if n == 8:
        schedule = _SUPER8
    elif n == 4:
        schedule = _SUPER4
    else:
        schedule = None

    rounds = []
    for i in range(num_rounds):
        if schedule and i < len(schedule):
            matches = [
                {
                    "team_a": (players[t1[0]], players[t1[1]]),
                    "team_b": (players[t2[0]], players[t2[1]]),
                    "result": None, "score": None,
                }
                for t1, t2 in schedule[i]
            ]
            bye: List[str] = []
        else:
            matches, bye = _greedy_round(players, pcount)

        rounds.append({"number": i + 1, "matches": matches, "bye": bye, "completed": False})
        for m in matches:
            for team in (m["team_a"], m["team_b"]):
                k = tuple(sorted(team))
                pcount[k] = pcount.get(k, 0) + 1

    return rounds, pcount


# ─────────────────────────────────────────────
#  Format class
# ─────────────────────────────────────────────

class RainhaDaPraia(BaseTournamentFormat):
    format_id = "rainha_da_praia"
    format_name = "Super 8 / Rainha da Praia"
    format_description = (
        "Parceiras rotacionam a cada rodada com matriz matemática perfeita. "
        "Pontuação individual acumulada."
    )
    min_players = 4
    requires_even = False

    def __init__(self, players: List[str], num_rounds: Optional[int] = None):
        self.players = players
        self.player_stats: Dict[str, Dict] = {p: empty_stats() for p in players}
        self.current_round_idx: int = 0
        self.tournament_date: str = ""
        n = len(players)
        if num_rounds is None:
            num_rounds = 7 if n == 8 else 3 if n == 4 else min(n - 1, 8)
        self.rounds, self._pcount = _build_rounds(players, num_rounds)

    # ── serialisation ───────────────────────────

    def to_dict(self) -> Dict:
        rounds_s = []
        for rnd in self.rounds:
            matches_s = [
                {
                    "team_a": list(m["team_a"]),
                    "team_b": list(m["team_b"]),
                    "result": result_to_dict(m["result"]) if m["result"] else None,
                    "score": score_to_dict(m["score"]) if m["score"] else None,
                }
                for m in rnd["matches"]
            ]
            rounds_s.append({**rnd, "matches": matches_s})
        return {
            "players": self.players,
            "player_stats": self.player_stats,
            "rounds": rounds_s,
            "current_round_idx": self.current_round_idx,
            "pcount": [[list(k), v] for k, v in self._pcount.items()],
            "tournament_date": self.tournament_date,
            "tournament_label": getattr(self, "tournament_label", ""),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RainhaDaPraia":
        obj = cls.__new__(cls)
        obj.players = d["players"]
        obj.player_stats = d["player_stats"]
        obj.current_round_idx = d["current_round_idx"]
        obj.tournament_date  = d.get("tournament_date", "")
        obj.tournament_label = d.get("tournament_label", "")
        obj._pcount = {tuple(item[0]): item[1] for item in d.get("pcount", [])}
        rounds = []
        for rnd in d["rounds"]:
            matches = [
                {
                    "team_a": tuple(m["team_a"]),
                    "team_b": tuple(m["team_b"]),
                    "result": dict_to_result(m["result"]) if m["result"] else None,
                    "score": dict_to_score(m["score"]) if m["score"] else None,
                }
                for m in rnd["matches"]
            ]
            rounds.append({**rnd, "matches": matches})
        obj.rounds = rounds
        return obj

    # ── public API ───────────────────────────────

    def add_round(self) -> None:
        matches, bye = _greedy_round(self.players, self._pcount)
        self.rounds.append({
            "number": len(self.rounds) + 1,
            "matches": matches, "bye": bye, "completed": False,
        })
        for m in matches:
            for team in (m["team_a"], m["team_b"]):
                k = tuple(sorted(team))
                self._pcount[k] = self._pcount.get(k, 0) + 1

    def submit_round(self, round_idx: int, scores: List[MatchScore]) -> None:
        rnd = self.rounds[round_idx]
        for match, score in zip(rnd["matches"], scores):
            result = compute_result(score)
            match["result"] = result
            match["score"] = score
            self._apply(match["team_a"], match["team_b"], result)
        rnd["completed"] = True

    def get_ranking(self):
        return compute_ranking(self.player_stats)

    def _apply(self, team_a, team_b, r: MatchResult):
        for p in team_a:
            s = self.player_stats[p]
            s["matches"] += 1; s["points"] += r.points_a
            s["games_pro"] += r.games_pro_a; s["games_against"] += r.games_pro_b
            s["game_balance"] += r.game_balance_a
            if r.winner == "A": s["wins"] += 1

        for p in team_b:
            s = self.player_stats[p]
            s["matches"] += 1; s["points"] += r.points_b
            s["games_pro"] += r.games_pro_b; s["games_against"] += r.games_pro_a
            s["game_balance"] += r.game_balance_b
            if r.winner == "B": s["wins"] += 1

    def _unapply(self, team_a, team_b, r: MatchResult):
        """Reverse a previously applied match result (for score correction)."""
        for p in team_a:
            s = self.player_stats[p]
            s["matches"] -= 1; s["points"] -= r.points_a
            s["games_pro"] -= r.games_pro_a; s["games_against"] -= r.games_pro_b
            s["game_balance"] -= r.game_balance_a
            if r.winner == "A": s["wins"] -= 1

        for p in team_b:
            s = self.player_stats[p]
            s["matches"] -= 1; s["points"] -= r.points_b
            s["games_pro"] -= r.games_pro_b; s["games_against"] -= r.games_pro_a
            s["game_balance"] -= r.game_balance_b
            if r.winner == "B": s["wins"] -= 1

    def uncomplete_round(self, idx: int):
        """Reopen a completed round so results can be corrected."""
        rnd = self.rounds[idx]
        if not rnd["completed"]:
            return
        for m in rnd["matches"]:
            if m["result"]:
                self._unapply(m["team_a"], m["team_b"], m["result"])
                m["result"] = None
                m["score"] = None
        rnd["completed"] = False
        self.current_round_idx = idx

    def delete_round(self, idx: int):
        """Remove a round entirely, reversing stats if it was completed."""
        if idx < 0 or idx >= len(self.rounds):
            return
        rnd = self.rounds[idx]
        if rnd["completed"]:
            for m in rnd["matches"]:
                if m["result"]:
                    self._unapply(m["team_a"], m["team_b"], m["result"])
        # Decrement partnership counter for this round's matches
        for m in rnd["matches"]:
            for team in (m["team_a"], m["team_b"]):
                k = tuple(sorted(team))
                if k in self._pcount:
                    self._pcount[k] = max(0, self._pcount[k] - 1)
        self.rounds.pop(idx)
        # Renumber remaining rounds
        for i, r in enumerate(self.rounds):
            r["number"] = i + 1
        # Adjust current_round_idx
        if not self.rounds:
            self.current_round_idx = 0
        elif self.current_round_idx >= len(self.rounds):
            self.current_round_idx = max(0, len(self.rounds) - 1)
        elif self.current_round_idx > idx:
            self.current_round_idx -= 1

    # ── render ───────────────────────────────────

    def render(self, can_edit: bool = False) -> None:
        from .ui_components import render_ranking_section, render_history_match

        n     = len(self.players)
        total = len(self.rounds)
        idx   = self.current_round_idx
        badge = "Encerrado 🏁" if idx >= total else f"Rodada {idx + 1} de {total}"

        # Format date for display (YYYY-MM-DD → DD/MM/YYYY)
        date_display = ""
        if self.tournament_date:
            try:
                from datetime import date as _d
                date_display = _d.fromisoformat(self.tournament_date).strftime("%d/%m/%Y")
            except Exception:
                date_display = self.tournament_date
        date_part = f"  ·  {date_display}" if date_display else ""

        display_name = getattr(self, "tournament_label", "").strip() or self.format_name
        exp_label = (
            f"🎾  {display_name}{date_part}"
            f"  ·  {n} participantes  ·  {badge}"
        )

        st.markdown(
            '<span class="bf-tourn-exp-marker" style="display:none"></span>',
            unsafe_allow_html=True,
        )
        with st.expander(exp_label, expanded=True,
                         key=f"tourn_exp_{self.format_id}"):
            tabs = st.tabs(["🏸 Rodada Atual", "🏆 Ranking", "📋 Histórico"])
            with tabs[0]:
                self._render_round(can_edit)
            with tabs[1]:
                render_ranking_section(self.get_ranking(), "individual")
            with tabs[2]:
                self._render_history(render_history_match)

    def _render_round(self, can_edit: bool):
        from .ui_components import bye_notice, round_done_banner

        idx = self.current_round_idx
        if idx >= len(self.rounds):
            round_done_banner("🏁 Torneio encerrado!")
            if can_edit:
                if st.button("➕ Adicionar Rodada Extra", type="primary"):
                    self.add_round()
                    _save()
                    st.rerun()
            return

        rnd = self.rounds[idx]
        st.progress(idx / len(self.rounds),
                    text=f"Rodada {rnd['number']} de {len(self.rounds)}")
        if rnd["bye"]:
            bye_notice(rnd["bye"])

        if rnd["completed"]:
            round_done_banner()
            if can_edit:
                del_key = f"del_rnd_rp_{idx}"
                if st.session_state.get(del_key):
                    st.warning(
                        f"⚠️ Apagar **Rodada {rnd['number']}**? "
                        "Os resultados serão revertidos do ranking."
                    )
                    cy, cn = st.columns(2)
                    with cy:
                        if st.button("✅ Confirmar exclusão", key=f"yes_del_rp_{idx}",
                                     type="primary", use_container_width=True):
                            st.session_state.pop(del_key, None)
                            self.delete_round(idx)
                            _save()
                            st.rerun()
                    with cn:
                        if st.button("❌ Cancelar", key=f"no_del_rp_{idx}",
                                     use_container_width=True):
                            st.session_state.pop(del_key, None)
                            st.rerun()
                else:
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    with c1:
                        if st.button("▶ Próxima Rodada", type="primary",
                                     use_container_width=True):
                            self.current_round_idx += 1
                            _save()
                            st.rerun()
                    with c2:
                        if st.button("✏️ Corrigir", use_container_width=True,
                                     help="Reabre a rodada para corrigir resultados"):
                            self.uncomplete_round(idx)
                            _save()
                            st.rerun()
                    with c3:
                        if st.button("➕ Extra", use_container_width=True):
                            self.add_round()
                            self.current_round_idx += 1
                            _save()
                            st.rerun()
                    with c4:
                        if st.button("🗑️ Apagar", use_container_width=True,
                                     help="Remove esta rodada e reverte os resultados"):
                            st.session_state[del_key] = True
                            st.rerun()
            return

        if not can_edit:
            _render_round_readonly(rnd)
            return

        del_p_key = f"del_pending_rp_{idx}"
        # Delete option for pending (not-yet-completed) rounds
        if can_edit and st.session_state.get(del_p_key):
            st.warning(f"⚠️ Apagar **Rodada {rnd['number']}** (sem resultados)?")
            cy, cn = st.columns(2)
            with cy:
                if st.button("✅ Confirmar exclusão", key=f"yes_delp_rp_{idx}",
                             type="primary", use_container_width=True):
                    st.session_state.pop(del_p_key, None)
                    self.delete_round(idx)
                    _save()
                    st.rerun()
            with cn:
                if st.button("❌ Cancelar", key=f"no_delp_rp_{idx}",
                             use_container_width=True):
                    st.session_state.pop(del_p_key, None)
                    st.rerun()
            return

        _render_score_form(f"rp_{idx}", rnd["matches"],
                           lambda scores: self._on_submit(idx, scores))

        if can_edit:
            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Apagar esta rodada", key=f"delbtn_rp_{idx}",
                         help="Remove a rodada sem registrar resultados"):
                st.session_state[del_p_key] = True
                st.rerun()

    def _on_submit(self, idx, scores):
        self.submit_round(idx, scores)
        _save()
        st.rerun()

    def _render_history(self, render_fn):
        done = [r for r in self.rounds if r["completed"]]
        if not done:
            st.info("Nenhuma rodada concluída ainda.")
            return
        for rnd in done:
            with st.expander(f"Rodada {rnd['number']}", expanded=False):
                for m in rnd["matches"]:
                    if m["result"]:
                        render_fn(m["team_a"], m["team_b"], m["result"], m["score"])


# ─────────────────────────────────────────────
#  Shared form helpers (also used by DuplasFixas)
# ─────────────────────────────────────────────

def _render_round_readonly(rnd: Dict):
    for i, m in enumerate(rnd["matches"]):
        ta, tb = m["team_a"], m["team_b"]
        st.markdown(
            f"<div class='match-card-label'>Partida {i+1}</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([3, 1, 3])
        with c1:
            names = f"<b>{ta[0]}</b><br>{ta[1]}" if isinstance(ta, tuple) else f"<b>{ta}</b>"
            st.markdown(f"<div class='team-label'>{names}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='text-align:center;padding-top:6px;font-size:1rem;"
                        "font-weight:700;color:#aaa'>vs</div>", unsafe_allow_html=True)
        with c3:
            names = f"<b>{tb[0]}</b><br>{tb[1]}" if isinstance(tb, tuple) else f"<b>{tb}</b>"
            st.markdown(f"<div class='team-label' style='text-align:right'>{names}</div>",
                        unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#f1f5f9;margin:.5rem 0'>", unsafe_allow_html=True)


def _render_score_form(form_key: str, matches: List[Dict], on_submit):
    from .ui_components import match_card_label

    with st.form(form_key):
        rows = []
        for i, m in enumerate(matches):
            ta, tb = m["team_a"], m["team_b"]
            match_card_label(i + 1)

            c1, c2, c3, c4, c5 = st.columns([3, 1, 0.4, 1, 3])
            with c1:
                ta_n = f"{ta[0]}<br>{ta[1]}" if isinstance(ta, tuple) else str(ta)
                st.markdown(f"<div class='team-label'>{ta_n}</div>", unsafe_allow_html=True)
            with c2:
                ga = st.number_input("A", 0, 4, 0, key=f"{form_key}_ga_{i}",
                                     label_visibility="collapsed")
            with c3:
                st.markdown("<div style='text-align:center;padding-top:6px;"
                            "font-size:1.1rem;font-weight:700;color:#bbb'>×</div>",
                            unsafe_allow_html=True)
            with c4:
                gb = st.number_input("B", 0, 4, 0, key=f"{form_key}_gb_{i}",
                                     label_visibility="collapsed")
            with c5:
                tb_n = f"{tb[0]}<br>{tb[1]}" if isinstance(tb, tuple) else str(tb)
                st.markdown(f"<div class='team-label' style='text-align:right'>{tb_n}</div>",
                            unsafe_allow_html=True)

            ta_label = f"{ta[0]} & {ta[1]}" if isinstance(ta, tuple) else str(ta)
            tb_label = f"{tb[0]} & {tb[1]}" if isinstance(tb, tuple) else str(tb)
            st_sel = st.selectbox(
                "Super Tie-Break",
                ["— sem super tie", f"🏆 {ta_label}", f"🏆 {tb_label}"],
                key=f"{form_key}_st_{i}",
            )
            rows.append((ga, gb, st_sel, ta, tb))
            st.markdown("<hr style='border-color:#f0f0f0;margin:.5rem 0'>",
                        unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "✅  Registrar Resultados", type="primary", use_container_width=True
        )

    if submitted:
        scores, errors = [], []
        for i, (ga, gb, st_sel, ta, tb) in enumerate(rows):
            if not is_valid_score(ga, gb):
                errors.append(f"Partida {i+1}: placar {ga}×{gb} inválido.")
                continue
            stw = None
            if ga == 2 and gb == 2:
                if st_sel == "— sem super tie":
                    errors.append(f"Partida {i+1}: 2×2 exige indicar o Super Tie-Break.")
                    continue
                ta_label = f"{ta[0]} & {ta[1]}" if isinstance(ta, tuple) else str(ta)
                stw = "A" if ta_label in st_sel else "B"
            scores.append(MatchScore(ga, gb, stw))

        if errors:
            for e in errors:
                st.error(e)
        else:
            on_submit(scores)


def _save():
    """Save current session tournament state to disk."""
    import streamlit as st
    from . import persistence
    t = st.session_state.get("tournament")
    if t:
        st.session_state["data"]["tournament"] = {
            "format": t.format_id,
            "data": t.to_dict(),
        }
    persistence.save(st.session_state["data"])
