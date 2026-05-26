from abc import ABC, abstractmethod
from typing import ClassVar, Dict


class BaseTournamentFormat(ABC):
    format_id:          ClassVar[str] = ""
    format_name:        ClassVar[str] = ""
    format_description: ClassVar[str] = ""
    min_players:        ClassVar[int] = 4
    requires_even:      ClassVar[bool] = False

    @abstractmethod
    def render(self, can_edit: bool = False) -> None:
        """Render the full tournament UI. can_edit=False for player/read-only view."""
        ...

    @abstractmethod
    def to_dict(self) -> Dict:
        """Serialise all state to a JSON-safe dict."""
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, d: Dict) -> "BaseTournamentFormat":
        """Restore an instance from a previously serialised dict."""
        ...
