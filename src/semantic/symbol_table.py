from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from .types import Type

@dataclass
class SymbolInfo:
    name: str
    type: Type
    kind: str
    line: int
    column: int
    initialized: bool = True
    params: Optional[List[Type]] = None
    fields: Optional[Dict[str, Type]] = None

    def __str__(self) -> str:
        parts = [f'{self.kind} {self.name}: {self.type}']
        if self.params is not None:
            params = ', '.join(str(p) for p in self.params)
            parts.append(f'params=({params})')
        if self.fields is not None:
            fields = ', '.join(f'{k}: {v}' for k, v in self.fields.items())
            parts.append(f'fields={{ {fields} }}')
        return ' '.join(parts)

class SymbolTable:
    def __init__(self):
        self.scopes: List[Dict[str, SymbolInfo]] = [{}]

    def enter_scope(self) -> None:
        self.scopes.append({})

    def exit_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()

    def insert(self, name: str, symbol_info: SymbolInfo) -> bool:
        scope = self.scopes[-1]
        if name in scope:
            return False
        scope[name] = symbol_info
        return True

    def lookup_local(self, name: str) -> Optional[SymbolInfo]:
        return self.scopes[-1].get(name)

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def dump(self) -> str:
        lines = []
        for index, scope in enumerate(self.scopes):
            lines.append(f'Scope {index}:')
            if not scope:
                lines.append('  (empty)')
            for symbol in scope.values():
                lines.append(f'  {symbol}')
        return '\n'.join(lines)
