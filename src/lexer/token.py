from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional

class TokenType(Enum):
    # Ключевые слова
    KW_IF = auto(); KW_ELSE = auto(); KW_WHILE = auto(); KW_FOR = auto()
    KW_INT = auto(); KW_FLOAT = auto(); KW_BOOL = auto(); KW_RETURN = auto()
    KW_TRUE = auto(); KW_FALSE = auto(); KW_VOID = auto(); KW_STRUCT = auto()
    KW_FN = auto()

    # Идентификаторы и литералы
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

    # Операторы
    OP_PLUS, OP_MINUS, OP_STAR, OP_SLASH, OP_PERCENT = auto(), auto(), auto(), auto(), auto()
    OP_EQ, OP_NEQ, OP_LT, OP_LE, OP_GT, OP_GE = auto(), auto(), auto(), auto(), auto(), auto()
    OP_AND = auto()
    OP_OR = auto()          # ||
    OP_NOT = auto()         # !
    ASSIGN = auto()
    ASSIGN_ADD = auto()     # +=
    ASSIGN_SUB = auto()     # -=
    ASSIGN_MUL = auto()     # *=
    ASSIGN_DIV = auto()     # /=

    # Разделители
    LPAREN, RPAREN, LBRACE, RBRACE, SEMICOLON, COMMA = auto(), auto(), auto(), auto(), auto(), auto()
    LBRACKET, RBRACKET = auto(), auto()   # [ ]
    COLON = auto()                         # :

    # Специальные
    END_OF_FILE = auto()
    ERROR = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    literal: Optional[Any] = None

    def __str__(self):
        line_col = f"{self.line}:{self.column}"
        # Экранируем лексему для безопасного вывода внутри кавычек
        escaped_lexeme = self.lexeme.replace('\\', '\\\\').replace('"', '\\"')
        if self.literal is not None:
            return f'{line_col} {self.type.name} "{escaped_lexeme}" {self.literal}'
        else:
            return f'{line_col} {self.type.name} "{escaped_lexeme}"'