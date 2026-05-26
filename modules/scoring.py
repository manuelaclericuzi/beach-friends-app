from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

# ─────────────────────────────────────────────
#  Data types
# ─────────────────────────────────────────────

@dataclass
class MatchScore:
    games_a: int
    games_b: int
    super_tie_winner: Optional[str] = None  # 'A' or 'B'


@dataclass
class MatchResult:
    winner: str
    points_a: int
    points_b: int
    games_pro_a: int
    games_pro_b: int
    game_balance_a: int
    game_balance_b: int
    is_super_tie: bool


VALID_SCORES = {(4, 0), (3, 1), (2, 2), (1, 3), (0, 4)}


# ─────────────────────────────────────────────
#  Core logic
# ─────────────────────────────────────────────

def is_valid_score(ga: int, gb: int) -> bool:
    return (ga, gb) in VALID_SCORES


def compute_result(score: MatchScore) -> MatchResult:
    ga, gb = score.games_a, score.games_b
    if ga == 2 and gb == 2:
        # Super Tie-Break: standardised as 3-2 for saldo purposes
        if score.super_tie_winner == "A":
            return MatchResult("A", 3, 0, 3, 2, 1, -1, True)
        return MatchResult("B", 0, 3, 2, 3, -1, 1, True)
    if ga > gb:
        return MatchResult("A", 3, 0, ga, gb, ga - gb, gb - ga, False)
    return MatchResult("B", 0, 3, ga, gb, ga - gb, gb - ga, False)


def empty_stats() -> Dict:
    return {"matches": 0, "wins": 0, "points": 0,
            "games_pro": 0, "games_against": 0, "game_balance": 0}


def compute_ranking(stats: Dict[str, Dict]) -> List[Tuple[int, str, Dict]]:
    """Sort: Points DESC → Game Balance DESC → Games Pro DESC → Name ASC."""
    ordered = sorted(
        stats.items(),
        key=lambda x: (-x[1]["points"], -x[1]["game_balance"],
                       -x[1]["games_pro"], x[0])
    )
    return [(i + 1, name, s) for i, (name, s) in enumerate(ordered)]


# ─────────────────────────────────────────────
#  Serialisation helpers (for JSON persistence)
# ─────────────────────────────────────────────

def score_to_dict(s: MatchScore) -> dict:
    return {"games_a": s.games_a, "games_b": s.games_b,
            "super_tie_winner": s.super_tie_winner}


def result_to_dict(r: MatchResult) -> dict:
    return r.__dict__.copy()


def dict_to_score(d: dict) -> MatchScore:
    return MatchScore(d["games_a"], d["games_b"], d.get("super_tie_winner"))


def dict_to_result(d: dict) -> MatchResult:
    return MatchResult(**d)
