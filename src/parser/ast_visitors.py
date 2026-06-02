import json
from typing import Any, List
from .ast import *
# ----------------------------------------------------------------------
# Pretty printer (text)
# ----------------------------------------------------------------------
class PrettyPrinter(ASTVisitor):
    def __init__(self):
        self.indent = 0
        self.output = []

    def _indent_str(self):
        return "  " * self.indent

    def visit_program(self, node: ProgramNode):
        self.output.append("Program:")
        self.indent += 1
        for decl in node.declarations:
            decl.accept(self)
        self.indent -= 1

    def visit_function_decl(self, node: FunctionDeclNode):
        self.output.append(f"{self._indent_str()}FunctionDecl: {node.name} -> {node.return_type}")
        self.indent += 1
        params = ", ".join(f"{p.param_type} {p.name}" for p in node.params)
        self.output.append(f"{self._indent_str()}Parameters: [{params}]")
        self.output.append(f"{self._indent_str()}Body:")
        node.body.accept(self)
        self.indent -= 1

    def visit_struct_decl(self, node: StructDeclNode):
        self.output.append(f"{self._indent_str()}StructDecl: {node.name}")
        self.indent += 1
        for field in node.fields:
            field.accept(self)
        self.indent -= 1

    def visit_var_decl(self, node: VarDeclNode):
        init = f" = {self._expr_str(node.initializer)}" if node.initializer else ""
        self.output.append(f"{self._indent_str()}VarDecl: {node.var_type} {node.name}{init}")

    def visit_param(self, node: ParamNode):
        self.output.append(f"{self._indent_str()}Param: {node.param_type} {node.name}")

    def visit_block_stmt(self, node: BlockStmtNode):
        self.output.append(f"{self._indent_str()}Block")
        self.indent += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent -= 1

    def visit_if_stmt(self, node: IfStmtNode):
        cond = self._expr_str(node.condition)
        self.output.append(f"{self._indent_str()}IfStmt: condition = {cond}")
        self.indent += 1
        node.then_branch.accept(self)
        if node.else_branch:
            self.output.append(f"{self._indent_str()}Else:")
            node.else_branch.accept(self)
        self.indent -= 1

    def visit_while_stmt(self, node: WhileStmtNode):
        cond = self._expr_str(node.condition)
        self.output.append(f"{self._indent_str()}WhileStmt: condition = {cond}")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1

    def visit_for_stmt(self, node: ForStmtNode):
        init = self._stmt_str(node.init) if node.init else ""
        cond = self._expr_str(node.condition) if node.condition else ""
        update = self._expr_str(node.update) if node.update else ""
        self.output.append(f"{self._indent_str()}ForStmt: init = {init}, cond = {cond}, update = {update}")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1

    def visit_return_stmt(self, node: ReturnStmtNode):
        val = self._expr_str(node.value) if node.value else ""
        self.output.append(f"{self._indent_str()}ReturnStmt: {val}")

    def visit_expr_stmt(self, node: ExprStmtNode):
        self.output.append(f"{self._indent_str()}ExprStmt: {self._expr_str(node.expression)}")

    def visit_literal_expr(self, node: LiteralExprNode):
        self.output[-1] += str(node.value)

    def visit_identifier_expr(self, node: IdentifierExprNode):
        self.output[-1] += node.name

    def visit_binary_expr(self, node: BinaryExprNode):
        self.output[-1] += "("
        node.left.accept(self)
        self.output[-1] += f" {node.operator} "
        node.right.accept(self)
        self.output[-1] += ")"

    def visit_unary_expr(self, node: UnaryExprNode):
        self.output[-1] += f"{node.operator}("
        node.operand.accept(self)
        self.output[-1] += ")"

    def visit_call_expr(self, node: CallExprNode):
        self.output[-1] += f"{node.callee}("
        for i, arg in enumerate(node.arguments):
            arg.accept(self)
            if i < len(node.arguments)-1:
                self.output[-1] += ", "
        self.output[-1] += ")"

    def visit_assignment_expr(self, node: AssignmentExprNode):
        self.output[-1] += "("
        node.target.accept(self)
        self.output[-1] += f" {node.operator} "
        node.value.accept(self)
        self.output[-1] += ")"

    def _expr_str(self, expr: ExpressionNode) -> str:
        old_out = self.output
        self.output = [""]
        expr.accept(self)
        s = self.output[0]
        self.output = old_out
        return s

    def _stmt_str(self, stmt: StatementNode) -> str:
        old_out = self.output
        self.output = [""]
        stmt.accept(self)
        s = self.output[0]
        self.output = old_out
        return s

    def get_text(self) -> str:
        return "\n".join(self.output)

# ----------------------------------------------------------------------
# Graphviz DOT visitor
# ----------------------------------------------------------------------
class DotVisitor(ASTVisitor):
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.counter = 0

    def _new_node(self, label: str, node_type: str, line: int, col: int) -> str:
        node_id = f"n{self.counter}"
        self.counter += 1
        self.nodes.append(f'  {node_id} [label="{label}\\n{node_type}\\n{line}:{col}", shape=box];')
        return node_id

    def _add_edge(self, parent_id: str, child_id: str):
        self.edges.append(f'  {parent_id} -> {child_id};')

    def visit_program(self, node: ProgramNode):
        self.parent_stack = []
        self.prog_id = self._new_node("Program", "Program", node.line, node.column)
        self.parent_stack.append(self.prog_id)
        for decl in node.declarations:
            decl.accept(self)
        self.parent_stack.pop()

    def _visit_child(self, child: ASTNode):
        old_parent = self.parent_stack[-1] if self.parent_stack else None
        child_id = child.accept(self)
        if old_parent and child_id:
            self._add_edge(old_parent, child_id)

    def visit_function_decl(self, node: FunctionDeclNode) -> str:
        node_id = self._new_node(f"fn {node.name} -> {node.return_type}", "FunctionDecl", node.line, node.column)
        self.parent_stack.append(node_id)
        for p in node.params:
            self._visit_child(p)
        self._visit_child(node.body)
        self.parent_stack.pop()
        return node_id

    def visit_struct_decl(self, node: StructDeclNode) -> str:
        node_id = self._new_node(f"struct {node.name}", "StructDecl", node.line, node.column)
        self.parent_stack.append(node_id)
        for f in node.fields:
            self._visit_child(f)
        self.parent_stack.pop()
        return node_id

    def visit_var_decl(self, node: VarDeclNode) -> str:
        label = f"{node.var_type} {node.name}"
        if node.initializer:
            label += f" = ..."
        node_id = self._new_node(label, "VarDecl", node.line, node.column)
        if node.initializer:
            self.parent_stack.append(node_id)
            self._visit_child(node.initializer)
            self.parent_stack.pop()
        return node_id

    def visit_param(self, node: ParamNode) -> str:
        return self._new_node(f"{node.param_type} {node.name}", "Param", node.line, node.column)

    def visit_block_stmt(self, node: BlockStmtNode) -> str:
        node_id = self._new_node("Block", "Block", node.line, node.column)
        self.parent_stack.append(node_id)
        for s in node.statements:
            self._visit_child(s)
        self.parent_stack.pop()
        return node_id

    def visit_if_stmt(self, node: IfStmtNode) -> str:
        node_id = self._new_node("if", "IfStmt", node.line, node.column)
        self.parent_stack.append(node_id)
        self._visit_child(node.condition)
        self._visit_child(node.then_branch)
        if node.else_branch:
            self._visit_child(node.else_branch)
        self.parent_stack.pop()
        return node_id

    def visit_while_stmt(self, node: WhileStmtNode) -> str:
        node_id = self._new_node("while", "WhileStmt", node.line, node.column)
        self.parent_stack.append(node_id)
        self._visit_child(node.condition)
        self._visit_child(node.body)
        self.parent_stack.pop()
        return node_id

    def visit_for_stmt(self, node: ForStmtNode) -> str:
        node_id = self._new_node("for", "ForStmt", node.line, node.column)
        self.parent_stack.append(node_id)
        if node.init: self._visit_child(node.init)
        if node.condition: self._visit_child(node.condition)
        if node.update: self._visit_child(node.update)
        self._visit_child(node.body)
        self.parent_stack.pop()
        return node_id

    def visit_return_stmt(self, node: ReturnStmtNode) -> str:
        node_id = self._new_node("return", "ReturnStmt", node.line, node.column)
        if node.value:
            self.parent_stack.append(node_id)
            self._visit_child(node.value)
            self.parent_stack.pop()
        return node_id

    def visit_expr_stmt(self, node: ExprStmtNode) -> str:
        node_id = self._new_node("expr", "ExprStmt", node.line, node.column)
        self.parent_stack.append(node_id)
        self._visit_child(node.expression)
        self.parent_stack.pop()
        return node_id

    def visit_literal_expr(self, node: LiteralExprNode) -> str:
        return self._new_node(str(node.value), "Literal", node.line, node.column)

    def visit_identifier_expr(self, node: IdentifierExprNode) -> str:
        return self._new_node(node.name, "Identifier", node.line, node.column)

    def visit_binary_expr(self, node: BinaryExprNode) -> str:
        node_id = self._new_node(node.operator, "Binary", node.line, node.column)
        self.parent_stack.append(node_id)
        self._visit_child(node.left)
        self._visit_child(node.right)
        self.parent_stack.pop()
        return node_id

    def visit_unary_expr(self, node: UnaryExprNode) -> str:
        node_id = self._new_node(node.operator, "Unary", node.line, node.column)
        self.parent_stack.append(node_id)
        self._visit_child(node.operand)
        self.parent_stack.pop()
        return node_id

    def visit_call_expr(self, node: CallExprNode) -> str:
        node_id = self._new_node(f"call {node.callee}", "Call", node.line, node.column)
        self.parent_stack.append(node_id)
        for a in node.arguments:
            self._visit_child(a)
        self.parent_stack.pop()
        return node_id

    def visit_assignment_expr(self, node: AssignmentExprNode) -> str:
        node_id = self._new_node(node.operator, "Assignment", node.line, node.column)
        self.parent_stack.append(node_id)
        self._visit_child(node.target)
        self._visit_child(node.value)
        self.parent_stack.pop()
        return node_id

    def get_dot(self) -> str:
        return "digraph AST {\n" + "\n".join(self.nodes) + "\n" + "\n".join(self.edges) + "\n}\n"

# ----------------------------------------------------------------------
# JSON visitor
# ----------------------------------------------------------------------
class JsonVisitor(ASTVisitor):
    def __init__(self):
        self.result = None

    def _make_node(self, kind: str, line: int, col: int, **attrs) -> dict:
        node = {"kind": kind, "line": line, "col": col}
        node.update(attrs)
        return node

    def visit_program(self, node: ProgramNode):
        decls = [self._visit(d) for d in node.declarations]
        self.result = self._make_node("Program", node.line, node.column, declarations=decls)

    def visit_function_decl(self, node: FunctionDeclNode):
        params = [self._visit(p) for p in node.params]
        body = self._visit(node.body)
        self.result = self._make_node("FunctionDecl", node.line, node.column,
                                      name=node.name, return_type=node.return_type,
                                      params=params, body=body)

    def visit_struct_decl(self, node: StructDeclNode):
        fields = [self._visit(f) for f in node.fields]
        self.result = self._make_node("StructDecl", node.line, node.column,
                                      name=node.name, fields=fields)

    def visit_var_decl(self, node: VarDeclNode):
        init = self._visit(node.initializer) if node.initializer else None
        self.result = self._make_node("VarDecl", node.line, node.column,
                                      type=node.var_type, name=node.name, initializer=init)

    def visit_param(self, node: ParamNode):
        self.result = self._make_node("Param", node.line, node.column,
                                      type=node.param_type, name=node.name)

    def visit_block_stmt(self, node: BlockStmtNode):
        stmts = [self._visit(s) for s in node.statements]
        self.result = self._make_node("Block", node.line, node.column, statements=stmts)

    def visit_if_stmt(self, node: IfStmtNode):
        cond = self._visit(node.condition)
        then_br = self._visit(node.then_branch)
        else_br = self._visit(node.else_branch) if node.else_branch else None
        self.result = self._make_node("IfStmt", node.line, node.column,
                                      condition=cond, then_branch=then_br, else_branch=else_br)

    def visit_while_stmt(self, node: WhileStmtNode):
        cond = self._visit(node.condition)
        body = self._visit(node.body)
        self.result = self._make_node("WhileStmt", node.line, node.column,
                                      condition=cond, body=body)

    def visit_for_stmt(self, node: ForStmtNode):
        init = self._visit(node.init) if node.init else None
        cond = self._visit(node.condition) if node.condition else None
        update = self._visit(node.update) if node.update else None
        body = self._visit(node.body)
        self.result = self._make_node("ForStmt", node.line, node.column,
                                      init=init, condition=cond, update=update, body=body)

    def visit_return_stmt(self, node: ReturnStmtNode):
        value = self._visit(node.value) if node.value else None
        self.result = self._make_node("ReturnStmt", node.line, node.column, value=value)

    def visit_expr_stmt(self, node: ExprStmtNode):
        expr = self._visit(node.expression)
        self.result = self._make_node("ExprStmt", node.line, node.column, expression=expr)

    def visit_literal_expr(self, node: LiteralExprNode):
        self.result = self._make_node("Literal", node.line, node.column, value=node.value)

    def visit_identifier_expr(self, node: IdentifierExprNode):
        self.result = self._make_node("Identifier", node.line, node.column, name=node.name)

    def visit_binary_expr(self, node: BinaryExprNode):
        left = self._visit(node.left)
        right = self._visit(node.right)
        self.result = self._make_node("Binary", node.line, node.column,
                                      operator=node.operator, left=left, right=right)

    def visit_unary_expr(self, node: UnaryExprNode):
        operand = self._visit(node.operand)
        self.result = self._make_node("Unary", node.line, node.column,
                                      operator=node.operator, operand=operand)

    def visit_call_expr(self, node: CallExprNode):
        args = [self._visit(a) for a in node.arguments]
        self.result = self._make_node("Call", node.line, node.column,
                                      callee=node.callee, arguments=args)

    def visit_assignment_expr(self, node: AssignmentExprNode):
        target = self._visit(node.target)
        value = self._visit(node.value)
        self.result = self._make_node("Assignment", node.line, node.column,
                                      operator=node.operator, target=target, value=value)

    def _visit(self, node: ASTNode):
        node.accept(self)
        return self.result

    def get_json(self) -> str:
        return json.dumps(self.result, indent=2)