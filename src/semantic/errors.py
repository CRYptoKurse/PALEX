from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SemanticError:
    message: str
    line: int
    column: int
    context: str = ''

    def __str__(self) -> str:
        result = f"semantic error: {self.message} at {self.line}:{self.column}"
        if self.context:
            result += f" (in {self.context})"
        return result
