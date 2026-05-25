from typing import List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# ----------------------------------------------------------------------
# Visitor pattern
# ----------------------------------------------------------------------
class ASTVisitor(ABC):
    @abstractmethod
    def visit_program(self, node: 'ProgramNode'): pass
    @abstractmethod
    def visit_function_decl(self, node: 'FunctionDeclNode'): pass
    @abstractmethod
    def visit_struct_decl(self, node: 'StructDeclNode'): pass
    @abstractmethod
    def visit_var_decl(self, node: 'VarDeclNode'): pass
    @abstractmethod
    def visit_param(self, node: 'ParamNode'): pass
    @abstractmethod
    def visit_block_stmt(self, node: 'BlockStmtNode'): pass
    @abstractmethod
    def visit_if_stmt(self, node: 'IfStmtNode'): pass
    @abstractmethod
    def visit_while_stmt(self, node: 'WhileStmtNode'): pass
    @abstractmethod
    def visit_for_stmt(self, node: 'ForStmtNode'): pass
    @abstractmethod
    def visit_return_stmt(self, node: 'ReturnStmtNode'): pass
    @abstractmethod
    def visit_expr_stmt(self, node: 'ExprStmtNode'): pass
    @abstractmethod
    def visit_literal_expr(self, node: 'LiteralExprNode'): pass
    @abstractmethod
    def visit_identifier_expr(self, node: 'IdentifierExprNode'): pass
    @abstractmethod
    def visit_binary_expr(self, node: 'BinaryExprNode'): pass
    @abstractmethod
    def visit_unary_expr(self, node: 'UnaryExprNode'): pass
    @abstractmethod
    def visit_call_expr(self, node: 'CallExprNode'): pass
    @abstractmethod
    def visit_assignment_expr(self, node: 'AssignmentExprNode'): pass

# ----------------------------------------------------------------------
# Base Node
# ----------------------------------------------------------------------
class ASTNode(ABC):
    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column
        self.type: Optional[Any] = None
        self.symbol: Optional[Any] = None

    @abstractmethod
    def accept(self, visitor: ASTVisitor): pass

# ----------------------------------------------------------------------
# Declaration nodes
# ----------------------------------------------------------------------
class DeclarationNode(ASTNode):
    pass

class ProgramNode(DeclarationNode):
    def __init__(self, declarations: List[DeclarationNode], line: int, column: int):
        super().__init__(line, column)
        self.declarations = declarations

    def accept(self, visitor: ASTVisitor):
        visitor.visit_program(self)

class FunctionDeclNode(DeclarationNode):
    def __init__(self, name: str, return_type: str, params: List['ParamNode'], body: 'BlockStmtNode', line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.return_type = return_type
        self.params = params
        self.body = body

    def accept(self, visitor: ASTVisitor):
        visitor.visit_function_decl(self)

class StructDeclNode(DeclarationNode):
    def __init__(self, name: str, fields: List['VarDeclNode'], line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.fields = fields

    def accept(self, visitor: ASTVisitor):
        visitor.visit_struct_decl(self)

class VarDeclNode(DeclarationNode):
    def __init__(self, var_type: str, name: str, initializer: Optional['ExpressionNode'], line: int, column: int):
        super().__init__(line, column)
        self.var_type = var_type
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: ASTVisitor):
        visitor.visit_var_decl(self)

class ParamNode(ASTNode):
    def __init__(self, param_type: str, name: str, line: int, column: int):
        super().__init__(line, column)
        self.param_type = param_type
        self.name = name

    def accept(self, visitor: ASTVisitor):
        visitor.visit_param(self)

# ----------------------------------------------------------------------
# Statement nodes
# ----------------------------------------------------------------------
class StatementNode(ASTNode):
    pass

class BlockStmtNode(StatementNode):
    def __init__(self, statements: List[StatementNode], line: int, column: int):
        super().__init__(line, column)
        self.statements = statements

    def accept(self, visitor: ASTVisitor):
        visitor.visit_block_stmt(self)

class IfStmtNode(StatementNode):
    def __init__(self, condition: 'ExpressionNode', then_branch: StatementNode, else_branch: Optional[StatementNode], line: int, column: int):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: ASTVisitor):
        visitor.visit_if_stmt(self)

class WhileStmtNode(StatementNode):
    def __init__(self, condition: 'ExpressionNode', body: StatementNode, line: int, column: int):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def accept(self, visitor: ASTVisitor):
        visitor.visit_while_stmt(self)

class ForStmtNode(StatementNode):
    def __init__(self, init: Optional[StatementNode], condition: Optional['ExpressionNode'], update: Optional['ExpressionNode'], body: StatementNode, line: int, column: int):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

    def accept(self, visitor: ASTVisitor):
        visitor.visit_for_stmt(self)

class ReturnStmtNode(StatementNode):
    def __init__(self, value: Optional['ExpressionNode'], line: int, column: int):
        super().__init__(line, column)
        self.value = value

    def accept(self, visitor: ASTVisitor):
        visitor.visit_return_stmt(self)

class ExprStmtNode(StatementNode):
    def __init__(self, expression: 'ExpressionNode', line: int, column: int):
        super().__init__(line, column)
        self.expression = expression

    def accept(self, visitor: ASTVisitor):
        visitor.visit_expr_stmt(self)

# ----------------------------------------------------------------------
# Expression nodes
# ----------------------------------------------------------------------
class ExpressionNode(ASTNode):
    pass

class LiteralExprNode(ExpressionNode):
    def __init__(self, value: Any, line: int, column: int):
        super().__init__(line, column)
        self.value = value

    def accept(self, visitor: ASTVisitor):
        visitor.visit_literal_expr(self)

class IdentifierExprNode(ExpressionNode):
    def __init__(self, name: str, line: int, column: int):
        super().__init__(line, column)
        self.name = name

    def accept(self, visitor: ASTVisitor):
        visitor.visit_identifier_expr(self)

class BinaryExprNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, operator: str, right: ExpressionNode, line: int, column: int):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: ASTVisitor):
        visitor.visit_binary_expr(self)

class UnaryExprNode(ExpressionNode):
    def __init__(self, operator: str, operand: ExpressionNode, line: int, column: int):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: ASTVisitor):
        visitor.visit_unary_expr(self)

class CallExprNode(ExpressionNode):
    def __init__(self, callee: str, arguments: List[ExpressionNode], line: int, column: int):
        super().__init__(line, column)
        self.callee = callee
        self.arguments = arguments

    def accept(self, visitor: ASTVisitor):
        visitor.visit_call_expr(self)

class AssignmentExprNode(ExpressionNode):
    def __init__(self, target: IdentifierExprNode, operator: str, value: ExpressionNode, line: int, column: int):
        super().__init__(line, column)
        self.target = target
        self.operator = operator
        self.value = value

    def accept(self, visitor: ASTVisitor):
        visitor.visit_assignment_expr(self)