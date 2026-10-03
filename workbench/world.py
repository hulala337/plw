"""World projection types kept separate from tracker data."""
from dataclasses import dataclass

@dataclass(frozen=True)
class DisplayRect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def size(self) -> tuple[int, int]:
        return self.right - self.left, self.bottom - self.top
