from __future__ import annotations
from typing import List, Optional
from .errors import SemanticError
from .symbol_table import SymbolInfo, SymbolTable
from .types import TypeSystem, Type, FunctionType, StructType
from src.parser.ast import *

class SemanticAnalyzer:
    def __init__(self):
        self.errors: List[SemanticError] = []
        self.symbol_table = SymbolTable()
        self.current_function: Optional[FunctionDeclNode] = None

    def analyze(self, program: ProgramNode) -> None:
        self.errors.clear()
        self.symbol_table = SymbolTable()
        self.current_function = None

        self._collect_global_declarations(program)
        for declaration in program.declarations:
            self._analyze_declaration(declaration)

    def get_errors(self) -> List[SemanticError]:
        return self.errors

    def get_symbol_table(self) -> SymbolTable:
        return self.symbol_table

    def get_decorated_ast(self, program: ProgramNode) -> ProgramNode:
        return program

    def _collect_global_declarations(self, program: ProgramNode) -> None:
        for declaration in program.declarations:
            if isinstance(declaration, FunctionDeclNode):
                self._declare_function(declaration)
            elif isinstance(declaration, StructDeclNode):
                self._declare_struct(declaration)
            elif isinstance(declaration, VarDeclNode):
                self._declare_global_variable(declaration)

    def _declare_function(self, decl: FunctionDeclNode) -> None:
        return_type = self._resolve_type_name(decl.return_type, decl)
        param_types = []
        for param in decl.params:
            param_type = self._resolve_type_name(param.param_type, param)
            param_types.append(param_type)
        function_type = FunctionType(param_types, return_type)
        symbol = SymbolInfo(
            name=decl.name,
            type=function_type,
            kind='function',
            line=decl.line,
            column=decl.column,
            initialized=True,
            params=param_types,
        )
        if not self.symbol_table.insert(decl.name, symbol):
            self._error(decl, f"Duplicate function declaration '{decl.name}'")
        decl.symbol = symbol

    def _declare_struct(self, decl: StructDeclNode) -> None:
        fields: dict[str, Type] = {}
        for field in decl.fields:
            if field.name in fields:
                self._error(field, f"Duplicate struct field '{field.name}'")
            field_type = self._resolve_type_name(field.var_type, field)
            fields[field.name] = field_type
        struct_type = StructType(decl.name, fields)
        symbol = SymbolInfo(
            name=decl.name,
            type=struct_type,
            kind='struct',
            line=decl.line,
            column=decl.column,
            initialized=True,
            fields=fields,
        )
        if not self.symbol_table.insert(decl.name, symbol):
            self._error(decl, f"Duplicate struct declaration '{decl.name}'")
        decl.symbol = symbol

    def _declare_global_variable(self, decl: VarDeclNode) -> None:
        var_type = self._resolve_type_name(decl.var_type, decl)
        initialized = decl.initializer is not None
        symbol = SymbolInfo(
            name=decl.name,
            type=var_type,
            kind='variable',
            line=decl.line,
            column=decl.column,
            initialized=initialized,
        )
        if not self.symbol_table.insert(decl.name, symbol):
            self._error(decl, f"Duplicate global variable '{decl.name}'")
        decl.symbol = symbol

    def _analyze_declaration(self, declaration: DeclarationNode) -> None:
        if isinstance(declaration, FunctionDeclNode):
            self._analyze_function(declaration)
        elif isinstance(declaration, StructDeclNode):
            pass
        elif isinstance(declaration, VarDeclNode):
            self._analyze_variable(declaration)

    def _analyze_function(self, decl: FunctionDeclNode) -> None:
        self.current_function = decl
        self.symbol_table.enter_scope()
        for param in decl.params:
            param_type = self._resolve_type_name(param.param_type, param)
            symbol = SymbolInfo(
                name=param.name,
                type=param_type,
                kind='parameter',
                line=param.line,
                column=param.column,
                initialized=True,
            )
            if not self.symbol_table.insert(param.name, symbol):
                self._error(param, f"Duplicate parameter '{param.name}'")
            param.symbol = symbol

        self._analyze_block(decl.body)
        self.symbol_table.exit_scope()
        self.current_function = None

    def _analyze_variable(self, decl: VarDeclNode) -> None:
        if decl.initializer:
            init_type = self._analyze_expression(decl.initializer)
            declared_type = self._resolve_type_name(decl.var_type, decl)
            if init_type and not declared_type.is_assignable_from(init_type):
                self._error(decl.initializer, f"Cannot assign {init_type} to variable '{decl.name}' of type {declared_type}")
        else:
            init_type = None
        decl.symbol = self.symbol_table.lookup(decl.name)

    def _analyze_block(self, block: BlockStmtNode) -> None:
        self.symbol_table.enter_scope()
        for statement in block.statements:
            self._analyze_statement(statement)
        self.symbol_table.exit_scope()

    def _analyze_statement(self, statement: StatementNode) -> None:
        if isinstance(statement, BlockStmtNode):
            self._analyze_block(statement)
        elif isinstance(statement, IfStmtNode):
            cond_type = self._analyze_expression(statement.condition)
            if cond_type and not cond_type.is_boolean():
                self._error(statement.condition, f"Condition must be bool, got {cond_type}")
            self._analyze_statement(statement.then_branch)
            if statement.else_branch:
                self._analyze_statement(statement.else_branch)
        elif isinstance(statement, WhileStmtNode):
            cond_type = self._analyze_expression(statement.condition)
            if cond_type and not cond_type.is_boolean():
                self._error(statement.condition, f"Condition must be bool, got {cond_type}")
            self._analyze_statement(statement.body)
        elif isinstance(statement, ForStmtNode):
            if statement.init:
                self._analyze_statement(statement.init)
            if statement.condition:
                cond_type = self._analyze_expression(statement.condition)
                if cond_type and not cond_type.is_boolean():
                    self._error(statement.condition, f"Condition must be bool, got {cond_type}")
            if statement.update:
                self._analyze_expression(statement.update)
            self._analyze_statement(statement.body)
        elif isinstance(statement, ReturnStmtNode):
            if not self.current_function:
                self._error(statement, 'Return statement outside of function')
                return
            return_type = self._resolve_type_name(self.current_function.return_type, self.current_function)
            if statement.value:
                value_type = self._analyze_expression(statement.value)
                if return_type and value_type and not return_type.is_assignable_from(value_type):
                    self._error(statement.value, f"Return type mismatch: expected {return_type}, got {value_type}")
            else:
                if not return_type.is_void():
                    self._error(statement, f"Return statement requires a value of type {return_type}")
        elif isinstance(statement, VarDeclNode):
            self._declare_variable(statement)
            self._analyze_variable(statement)
        elif isinstance(statement, ExprStmtNode):
            self._analyze_expression(statement.expression)
        else:
            self._error(statement, f"Unsupported statement type: {type(statement).__name__}")

    def _declare_variable(self, decl: VarDeclNode) -> None:
        var_type = self._resolve_type_name(decl.var_type, decl)
        initialized = decl.initializer is not None
        symbol = SymbolInfo(
            name=decl.name,
            type=var_type,
            kind='variable',
            line=decl.line,
            column=decl.column,
            initialized=initialized,
        )
        if not self.symbol_table.insert(decl.name, symbol):
            self._error(decl, f"Duplicate variable '{decl.name}' in this scope")
        decl.symbol = symbol

    def _analyze_expression(self, expr: ExpressionNode) -> Optional[Type]:
        if isinstance(expr, LiteralExprNode):
            expr.type = self._type_of_literal(expr.value)
            return expr.type
        if isinstance(expr, IdentifierExprNode):
            symbol = self.symbol_table.lookup(expr.name)
            if not symbol:
                self._error(expr, f"Undeclared identifier '{expr.name}'")
                expr.type = TypeSystem.VOID
                return expr.type
            expr.symbol = symbol
            expr.type = symbol.type
            if symbol.kind == 'variable' and not symbol.initialized:
                self._error(expr, f"Variable '{expr.name}' used before initialization")
            return expr.type
        if isinstance(expr, AssignmentExprNode):
            left_type = self._analyze_expression(expr.target)
            right_type = self._analyze_expression(expr.value)
            op = expr.operator
            if expr.target:
                target_symbol = self.symbol_table.lookup(expr.target.name)
            else:
                target_symbol = None
            if not isinstance(expr.target, IdentifierExprNode):
                self._error(expr.target, "Invalid assignment target")
                expr.type = TypeSystem.VOID
                return expr.type
            if not target_symbol:
                self._error(expr.target, f"Undeclared identifier '{expr.target.name}'")
                expr.type = TypeSystem.VOID
                return expr.type
            if target_symbol.kind not in {'variable', 'parameter'}:
                self._error(expr.target, f"Cannot assign to '{expr.target.name}'")
                expr.type = TypeSystem.VOID
                return expr.type
            if op == '=':
                if left_type and right_type and not left_type.is_assignable_from(right_type):
                    self._error(expr, f"Cannot assign {right_type} to {left_type}")
                expr.type = left_type or TypeSystem.VOID
                if target_symbol:
                    target_symbol.initialized = True
                return expr.type
            if op in {'+=', '-=', '*=', '/='}:
                if left_type and right_type:
                    result = TypeSystem.numeric_result_type(left_type, right_type)
                    if not result:
                        self._error(expr, f"Operator '{op}' requires numeric operands")
                        expr.type = TypeSystem.VOID
                    else:
                        expr.type = result
                        if target_symbol:
                            target_symbol.initialized = True
                    return expr.type
                expr.type = TypeSystem.VOID
                return expr.type
            self._error(expr, f"Unsupported assignment operator '{op}'")
            expr.type = TypeSystem.VOID
            return expr.type

        if isinstance(expr, BinaryExprNode):
            left_type = self._analyze_expression(expr.left)
            right_type = self._analyze_expression(expr.right)
            op = expr.operator
            if op in {'+', '-', '*', '/'}:
                if left_type and right_type:
                    result = TypeSystem.numeric_result_type(left_type, right_type)
                    if not result:
                        self._error(expr, f"Operator '{op}' requires numeric operands")
                        expr.type = TypeSystem.VOID
                    else:
                        expr.type = result
                    return expr.type
            if op == '%':
                if left_type and right_type and left_type.name == 'int' and right_type.name == 'int':
                    expr.type = TypeSystem.INT
                    return expr.type
                self._error(expr, "Operator '%' requires integer operands")
                expr.type = TypeSystem.VOID
                return expr.type
            if op in {'<', '<=', '>', '>='}:
                if left_type and right_type and left_type.is_numeric() and right_type.is_numeric():
                    expr.type = TypeSystem.BOOL
                    return expr.type
                self._error(expr, f"Operator '{op}' requires numeric operands")
                expr.type = TypeSystem.VOID
                return expr.type
            if op in {'==', '!='}:
                if left_type and right_type and left_type == right_type:
                    expr.type = TypeSystem.BOOL
                    return expr.type
                self._error(expr, f"Operator '{op}' requires operands of the same type")
                expr.type = TypeSystem.VOID
                return expr.type
            if op in {'&&', '||'}:
                if left_type and right_type and left_type.is_boolean() and right_type.is_boolean():
                    expr.type = TypeSystem.BOOL
                    return expr.type
                self._error(expr, f"Operator '{op}' requires boolean operands")
                expr.type = TypeSystem.VOID
                return expr.type
            if op in {'=', '+=', '-=', '*=', '/='}:
                if not isinstance(expr.left, IdentifierExprNode):
                    self._error(expr.left, "Invalid assignment target")
                    expr.type = TypeSystem.VOID
                    return expr.type
                left_symbol = self.symbol_table.lookup(expr.left.name)
                if not left_symbol:
                    self._error(expr.left, f"Undeclared identifier '{expr.left.name}'")
                    expr.type = TypeSystem.VOID
                    return expr.type
                if left_symbol.kind not in {'variable', 'parameter'}:
                    self._error(expr.left, f"Cannot assign to '{expr.left.name}'")
                    expr.type = TypeSystem.VOID
                    return expr.type
                if op == '=':
                    if left_type and right_type and not left_type.is_assignable_from(right_type):
                        self._error(expr, f"Cannot assign {right_type} to {left_type}")
                    expr.type = left_type or TypeSystem.VOID
                    left_symbol.initialized = True
                    return expr.type
                if left_type and right_type:
                    result = TypeSystem.numeric_result_type(left_type, right_type)
                    if not result:
                        self._error(expr, f"Operator '{op}' requires numeric operands")
                        expr.type = TypeSystem.VOID
                    else:
                        expr.type = result
                        left_symbol.initialized = True
                    return expr.type
                expr.type = TypeSystem.VOID
                return expr.type
            self._error(expr, f"Unsupported binary operator '{op}'")
            expr.type = TypeSystem.VOID
            return expr.type
        if isinstance(expr, UnaryExprNode):
            operand_type = self._analyze_expression(expr.operand)
            op = expr.operator
            if op == '!':
                if operand_type and operand_type.is_boolean():
                    expr.type = TypeSystem.BOOL
                    return expr.type
                self._error(expr, "Operator '!' requires boolean operand")
                expr.type = TypeSystem.VOID
                return expr.type
            if op == '-' or op == '+':
                if operand_type and operand_type.is_numeric():
                    expr.type = operand_type
                    return expr.type
                self._error(expr, f"Operator '{op}' requires numeric operand")
                expr.type = TypeSystem.VOID
                return expr.type
            self._error(expr, f"Unsupported unary operator '{op}'")
            expr.type = TypeSystem.VOID
            return expr.type
        if isinstance(expr, CallExprNode):
            symbol = self.symbol_table.lookup(expr.callee)
            if not symbol:
                self._error(expr, f"Undeclared function '{expr.callee}'")
                expr.type = TypeSystem.VOID
                return expr.type
            if not isinstance(symbol.type, FunctionType):
                self._error(expr, f"'{expr.callee}' is not a function")
                expr.type = TypeSystem.VOID
                return expr.type
            expr.symbol = symbol
            function_type = symbol.type
            if len(expr.arguments) != len(function_type.param_types):
                self._error(expr, f"Function '{expr.callee}' expects {len(function_type.param_types)} arguments, got {len(expr.arguments)}")
            for index, arg in enumerate(expr.arguments):
                arg_type = self._analyze_expression(arg)
                if index < len(function_type.param_types) and arg_type:
                    param_type = function_type.param_types[index]
                    if not param_type.is_assignable_from(arg_type):
                        self._error(arg, f"Argument {index + 1} of '{expr.callee}' expects {param_type}, got {arg_type}")
            expr.type = function_type.return_type
            return expr.type
        self._error(expr, f"Unsupported expression type: {type(expr).__name__}")
        return TypeSystem.VOID

    def _resolve_type_name(self, type_name: str, node: ASTNode) -> Type:
        builtin = TypeSystem.resolve(type_name)
        if builtin:
            return builtin
        symbol = self.symbol_table.lookup(type_name)
        if symbol and symbol.kind == 'struct' and isinstance(symbol.type, StructType):
            return symbol.type
        self._error(node, f"Unknown type '{type_name}'")
        return TypeSystem.VOID

    def _type_of_literal(self, value: object) -> Type:
        if isinstance(value, bool):
            return TypeSystem.BOOL
        if isinstance(value, int):
            return TypeSystem.INT
        if isinstance(value, float):
            return TypeSystem.FLOAT
        if isinstance(value, str):
            return TypeSystem.STRING
        return TypeSystem.VOID

    def _error(self, node: ASTNode, message: str) -> None:
        self.errors.append(SemanticError(message, node.line, node.column,
                                         context=(self.current_function.name if self.current_function else 'global')))
