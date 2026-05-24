from typing import List, Optional
from ..lexer.token import Token, TokenType
from .ast import *

class ParserError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at {line}:{column}")

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: List[str] = []

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    def is_at_end(self) -> bool:
        return self.pos >= len(self.tokens) or self.current().type == TokenType.END_OF_FILE

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.END_OF_FILE, "", 0, 0)

    def peek(self) -> TokenType:
        return self.current().type

    def previous(self) -> Token:
        return self.tokens[self.pos - 1] if self.pos > 0 else Token(TokenType.ERROR, "", 0, 0)

    def advance(self) -> Token:
        if not self.is_at_end():
            self.pos += 1
        return self.previous()

    def match(self, *types: TokenType) -> bool:
        if not self.is_at_end() and self.peek() in types:
            self.advance()
            return True
        return False

    def check(self, typ: TokenType) -> bool:
        return not self.is_at_end() and self.peek() == typ

    def consume(self, typ: TokenType, message: str) -> Token:
        if self.check(typ):
            return self.advance()
        self._error(self.current(), message)
        # Возвращаем токен ошибки для продолжения
        return Token(TokenType.ERROR, "", self.current().line, self.current().column)

    def _error(self, token: Token, message: str):
        err = f"Syntax error at {token.line}:{token.column}: {message}, got '{token.lexeme}'"
        self.errors.append(err)

    def _synchronize(self):
        """Синхронизация после ошибки: пропускаем токены до точки синхронизации."""
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return
            if self.peek() in {TokenType.KW_IF, TokenType.KW_WHILE, TokenType.KW_FOR,
                               TokenType.KW_RETURN, TokenType.KW_FN, TokenType.KW_STRUCT,
                               TokenType.LBRACE, TokenType.RBRACE}:
                return
            self.advance()

    # ------------------------------------------------------------------
    # Основной метод parse
    # ------------------------------------------------------------------
    def parse(self) -> ProgramNode:
        declarations = []
        while not self.is_at_end():
            decl = self.parse_declaration()
            if decl:
                declarations.append(decl)
            else:
                # Если не удалось распознать объявление, пропускаем токен во избежание бесконечного цикла
                self.advance()
        return ProgramNode(declarations, 1, 1)

    # ------------------------------------------------------------------
    # Декларации
    # ------------------------------------------------------------------
    def parse_declaration(self) -> Optional[DeclarationNode]:
        if self.match(TokenType.KW_FN):
            return self.parse_function_decl()
        if self.match(TokenType.KW_STRUCT):
            return self.parse_struct_decl()
        if self._is_var_decl_start():
            var_decl = self.parse_var_decl()
            if var_decl:
                self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
                return var_decl
        return None

    def parse_function_decl(self) -> FunctionDeclNode:
        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name")
        name = name_token.lexeme
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parse_parameters()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        ret_type = "void"
        if self.match(TokenType.ARROW):
            ret_type = self.parse_type()
        # Требуем открывающую скобку тела
        if not self.check(TokenType.LBRACE):
            self._error(self.current(), "Expected '{' to start function body")
        body = self.parse_block()
        return FunctionDeclNode(name, ret_type, params, body, name_token.line, name_token.column)

    def parse_parameters(self) -> List[ParamNode]:
        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                param_type = self.parse_type()
                name_token = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                params.append(ParamNode(param_type, name_token.lexeme, name_token.line, name_token.column))
                if not self.match(TokenType.COMMA):
                    break
        return params

    def parse_struct_decl(self) -> StructDeclNode:
        name_token = self.consume(TokenType.IDENTIFIER, "Expected struct name")
        self.consume(TokenType.LBRACE, "Expected '{' after struct name")
        fields = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            field = self.parse_var_decl()
            if field:
                self.consume(TokenType.SEMICOLON, "Expected ';' after struct field")
                fields.append(field)
        self.consume(TokenType.RBRACE, "Expected '}' to close struct")
        return StructDeclNode(name_token.lexeme, fields, name_token.line, name_token.column)

    def parse_var_decl(self) -> Optional[VarDeclNode]:
        if not self._is_type():
            return None
        var_type = self.parse_type()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        init = None
        if self.match(TokenType.ASSIGN):
            init = self.parse_expression()
        return VarDeclNode(var_type, name_token.lexeme, init, name_token.line, name_token.column)

    def parse_type(self) -> str:
        if self.match(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_VOID):
            return self.previous().lexeme
        ident = self.consume(TokenType.IDENTIFIER, "Expected type name")
        return ident.lexeme

    # ------------------------------------------------------------------
    # Инструкции (statements)
    # ------------------------------------------------------------------
    def parse_statement(self) -> Optional[StatementNode]:
        if self.match(TokenType.LBRACE):
            return self.parse_block()
        if self.match(TokenType.KW_IF):
            return self.parse_if_stmt()
        if self.match(TokenType.KW_WHILE):
            return self.parse_while_stmt()
        if self.match(TokenType.KW_FOR):
            return self.parse_for_stmt()
        if self.match(TokenType.KW_RETURN):
            return self.parse_return_stmt()
        if self._is_var_decl_start():
            var_decl = self.parse_var_decl()
            if var_decl:
                self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
                return var_decl
        # Иначе expression statement
        expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmtNode(expr, expr.line, expr.column)

    def parse_block(self) -> BlockStmtNode:
        if self.previous().type == TokenType.LBRACE:
            lbrace = self.previous()
        else:
            lbrace = self.current()
            self.consume(TokenType.LBRACE, "Expected '{' to start block")
        statements = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        self.consume(TokenType.RBRACE, "Expected '}' to close block")
        return BlockStmtNode(statements, lbrace.line, lbrace.column)

    def parse_if_stmt(self) -> IfStmtNode:
        kw = self.previous()
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        cond = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        then_branch = self.parse_statement()  # ← заменили parse_block на parse_statement
        else_branch = None
        if self.match(TokenType.KW_ELSE):
            else_branch = self.parse_statement()  # ← и здесь
        return IfStmtNode(cond, then_branch, else_branch, kw.line, kw.column)

    def parse_while_stmt(self) -> WhileStmtNode:
        kw = self.previous()
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        cond = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        body = self.parse_statement()  # ← заменили parse_block на parse_statement
        return WhileStmtNode(cond, body, kw.line, kw.column)

    def parse_for_stmt(self) -> ForStmtNode:
        kw = self.previous()
        self.consume(TokenType.LPAREN, "Expected '(' after 'for'")
        # init
        if self.match(TokenType.SEMICOLON):
            init = None
        else:
            if self._is_var_decl_start():
                init = self.parse_var_decl()
                if init:
                    self.consume(TokenType.SEMICOLON, "Expected ';' after for init")
            else:
                init = self.parse_expression()
                self.consume(TokenType.SEMICOLON, "Expected ';' after for init")
        # condition
        if self.check(TokenType.SEMICOLON):
            cond = None
        else:
            cond = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after for condition")
        # update
        if self.check(TokenType.RPAREN):
            update = None
        else:
            update = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after for clauses")
        body = self.parse_statement()
        return ForStmtNode(init, cond, update, body, kw.line, kw.column)

    def parse_return_stmt(self) -> ReturnStmtNode:
        kw = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after return statement")
        return ReturnStmtNode(value, kw.line, kw.column)

    # ------------------------------------------------------------------
    # Выражения (precedence climbing)
    # ------------------------------------------------------------------
    def parse_expression(self) -> ExpressionNode:
        return self.parse_assignment()

    def parse_assignment(self) -> ExpressionNode:
        left = self.parse_logical_or()
        if self.match(TokenType.ASSIGN, TokenType.ASSIGN_ADD, TokenType.ASSIGN_SUB,
                      TokenType.ASSIGN_MUL, TokenType.ASSIGN_DIV):
            op = self.previous().lexeme
            if not isinstance(left, IdentifierExprNode):
                self._error(self.previous(), "Invalid left-hand side in assignment")
            right = self.parse_assignment()  # right-associative
            return AssignmentExprNode(left, op, right, left.line, left.column)
        return left

    def parse_logical_or(self) -> ExpressionNode:
        left = self.parse_logical_and()
        while self.match(TokenType.OP_OR):
            op = self.previous().lexeme
            right = self.parse_logical_and()
            left = BinaryExprNode(left, op, right, left.line, left.column)
        return left

    def parse_logical_and(self) -> ExpressionNode:
        left = self.parse_equality()
        while self.match(TokenType.OP_AND):
            op = self.previous().lexeme
            right = self.parse_equality()
            left = BinaryExprNode(left, op, right, left.line, left.column)
        return left

    def parse_equality(self) -> ExpressionNode:
        left = self.parse_relational()
        while self.match(TokenType.OP_EQ, TokenType.OP_NEQ):
            op = self.previous().lexeme
            right = self.parse_relational()
            left = BinaryExprNode(left, op, right, left.line, left.column)
        return left

    def parse_relational(self) -> ExpressionNode:
        left = self.parse_additive()
        while self.match(TokenType.OP_LT, TokenType.OP_LE, TokenType.OP_GT, TokenType.OP_GE):
            op = self.previous().lexeme
            right = self.parse_additive()
            left = BinaryExprNode(left, op, right, left.line, left.column)
        return left

    def parse_additive(self) -> ExpressionNode:
        left = self.parse_multiplicative()
        while self.match(TokenType.OP_PLUS, TokenType.OP_MINUS):
            op = self.previous().lexeme
            right = self.parse_multiplicative()
            left = BinaryExprNode(left, op, right, left.line, left.column)
        return left

    def parse_multiplicative(self) -> ExpressionNode:
        left = self.parse_unary()
        while self.match(TokenType.OP_STAR, TokenType.OP_SLASH, TokenType.OP_PERCENT):
            op = self.previous().lexeme
            right = self.parse_unary()
            left = BinaryExprNode(left, op, right, left.line, left.column)
        return left

    def parse_unary(self) -> ExpressionNode:
        if self.match(TokenType.OP_PLUS, TokenType.OP_MINUS, TokenType.OP_NOT):
            op = self.previous().lexeme
            operand = self.parse_unary()
            return UnaryExprNode(op, operand, operand.line, operand.column)
        return self.parse_primary()

    def parse_primary(self) -> ExpressionNode:
        if self.match(TokenType.KW_TRUE, TokenType.KW_FALSE):
            val = self.previous().literal if self.previous().literal is not None else (self.previous().lexeme == 'true')
            return LiteralExprNode(val, self.previous().line, self.previous().column)
        if self.match(TokenType.INT_LITERAL):
            return LiteralExprNode(self.previous().literal, self.previous().line, self.previous().column)
        if self.match(TokenType.FLOAT_LITERAL):
            return LiteralExprNode(self.previous().literal, self.previous().line, self.previous().column)
        if self.match(TokenType.STRING_LITERAL):
            return LiteralExprNode(self.previous().literal, self.previous().line, self.previous().column)
        if self.match(TokenType.IDENTIFIER):
            ident = self.previous()
            if self.check(TokenType.LPAREN):
                return self.parse_call(ident)
            # Возможен доступ к полю структуры (если добавите TokenType.DOT)
            # if self.match(TokenType.DOT):
            #     field = self.consume(TokenType.IDENTIFIER, "Expected field name")
            #     return MemberAccessExprNode(IdentifierExprNode(ident.lexeme, ...), field.lexeme, ...)
            return IdentifierExprNode(ident.lexeme, ident.line, ident.column)
        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        self._error(self.current(), f"Unexpected token in primary expression")
        return LiteralExprNode(None, self.current().line, self.current().column)

    def parse_call(self, callee_token: Token) -> CallExprNode:
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        args = []
        if not self.check(TokenType.RPAREN):
            while True:
                args.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expected ')' after arguments")
        return CallExprNode(callee_token.lexeme, args, callee_token.line, callee_token.column)

    # ------------------------------------------------------------------
    # Вспомогательное определение типа
    # ------------------------------------------------------------------
    def _is_type(self) -> bool:
        return self.peek() in {TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                               TokenType.KW_VOID, TokenType.IDENTIFIER}

    def _is_var_decl_start(self) -> bool:
        if self.peek() in {TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_VOID}:
            return True
        if self.peek() == TokenType.IDENTIFIER and self._peek_token_type(1) == TokenType.IDENTIFIER:
            return True
        return False

    def _peek_token_type(self, offset: int = 1) -> Optional[TokenType]:
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset].type
        return None