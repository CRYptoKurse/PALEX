from __future__ import annotations
from typing import List, Optional, Dict
from src.parser.ast import *
from src.semantic.types import TypeSystem
from src.semantic.symbol_table import SymbolTable
from .ir import IRProgram, FunctionIR, BasicBlock, Instruction

OPERATOR_MAP = {
    '+': 'ADD',
    '-': 'SUB',
    '*': 'MUL',
    '/': 'DIV',
    '%': 'MOD',
    '&&': 'AND',
    '||': 'OR',
    '==': 'CMP_EQ',
    '!=': 'CMP_NE',
    '<': 'CMP_LT',
    '<=': 'CMP_LE',
    '>': 'CMP_GT',
    '>=': 'CMP_GE',
}

UNARY_MAP = {
    '!': 'NOT',
    '-': 'SUB',
    '+': 'MOVE',
}

class IRGenerator:
    def __init__(self, symbol_table: Optional[SymbolTable] = None, type_system: Optional[TypeSystem] = None):
        self.symbol_table = symbol_table
        self.type_system = type_system
        self.program = IRProgram()
        self.temp_counter = 0
        self.label_counter = 0
        self.variable_stack: List[Dict[str, str]] = []
        self.current_function: Optional[FunctionIR] = None
        # track last assignments within a block: var_name -> temp
        self._assignments_stack: List[Dict[str, str]] = []
        self.last_assignments: Dict[str, str] = {}

    def generate(self, ast: ProgramNode) -> IRProgram:
        self.program = IRProgram()
        self.temp_counter = 0
        self.label_counter = 0
        for declaration in ast.declarations:
            if isinstance(declaration, FunctionDeclNode):
                self._generate_function(declaration)
        return self.program

    def get_function_ir(self, name: str) -> Optional[FunctionIR]:
        return self.program.get_function(name)

    def get_all_ir(self) -> IRProgram:
        return self.program

    def _generate_function(self, decl: FunctionDeclNode) -> None:
        params = [param.name for param in decl.params]
        param_types = [param.param_type for param in decl.params]
        function_ir = FunctionIR(decl.name, decl.return_type, params, param_types)
        self.current_function = function_ir
        self.program.add_function(function_ir)

        self.variable_stack = []
        self._enter_scope()

        entry = BasicBlock('entry')
        function_ir.add_block(entry)

        # Allocate parameters and locals in entry
        for param in decl.params:
            mem_name = self._declare_variable(param.name)
            function_ir.local_allocations.append(mem_name)
            entry.add(Instruction('ALLOCA', mem_name, ['1'], comment=f'param {param.name}'))

        self._generate_block(decl.body, entry, function_ir)
        self._exit_scope()
        self.current_function = None

    def _generate_block(self, block: BlockStmtNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        self._enter_scope()
        for statement in block.statements:
            current = self._generate_statement(statement, current, function_ir)
        self._exit_scope()
        return current

    def _generate_statement(self, statement: StatementNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        if isinstance(statement, BlockStmtNode):
            return self._generate_block(statement, current, function_ir)
        if isinstance(statement, IfStmtNode):
            return self._generate_if(statement, current, function_ir)
        if isinstance(statement, WhileStmtNode):
            return self._generate_while(statement, current, function_ir)
        if isinstance(statement, ForStmtNode):
            return self._generate_for(statement, current, function_ir)
        if isinstance(statement, ReturnStmtNode):
            return self._generate_return(statement, current, function_ir)
        if isinstance(statement, VarDeclNode):
            return self._generate_variable_decl(statement, current, function_ir)
        if isinstance(statement, ExprStmtNode):
            _, current = self._generate_expression(statement.expression, current, function_ir)
            return current
        self._add_comment(current, f'Unsupported statement type: {type(statement).__name__}')
        return current

    def _generate_if(self, stmt: IfStmtNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        cond_temp, current = self._generate_expression(stmt.condition, current, function_ir)
        then_label = self._new_label('then')
        else_label = self._new_label('else')
        end_label = self._new_label('endif')

        current.add(Instruction('JUMP_IF', None, [cond_temp, then_label], comment='if true'))
        current.add(Instruction('JUMP', None, [else_label], comment='if false'))

        then_block = BasicBlock(then_label)
        function_ir.add_block(then_block)
        self._enter_scope()
        after_then = self._generate_statement(stmt.then_branch, then_block, function_ir)
        self._exit_scope()
        if not after_then.terminator():
            after_then.add(Instruction('JUMP', None, [end_label]))

        else_block = BasicBlock(else_label)
        function_ir.add_block(else_block)
        self._enter_scope()
        if stmt.else_branch:
            after_else = self._generate_statement(stmt.else_branch, else_block, function_ir)
        else:
            after_else = else_block
        self._exit_scope()
        if not after_else.terminator():
            after_else.add(Instruction('JUMP', None, [end_label]))

        end_block = BasicBlock(end_label)
        function_ir.add_block(end_block)
        return end_block

    def _generate_while(self, stmt: WhileStmtNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        cond_label = self._new_label('while_cond')
        body_label = self._new_label('while_body')
        end_label = self._new_label('while_end')

        current.add(Instruction('JUMP', None, [cond_label]))

        cond_block = BasicBlock(cond_label)
        function_ir.add_block(cond_block)
        cond_temp, cond_block = self._generate_expression(stmt.condition, cond_block, function_ir)
        cond_block.add(Instruction('JUMP_IF', None, [cond_temp, body_label], comment='while true'))
        cond_block.add(Instruction('JUMP', None, [end_label], comment='while false'))

        body_block = BasicBlock(body_label)
        function_ir.add_block(body_block)
        self._enter_scope()
        end_body = self._generate_statement(stmt.body, body_block, function_ir)
        self._exit_scope()
        if not end_body.terminator():
            end_body.add(Instruction('JUMP', None, [cond_label]))

        end_block = BasicBlock(end_label)
        function_ir.add_block(end_block)
        return end_block

    def _generate_for(self, stmt: ForStmtNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        if stmt.init:
            current = self._generate_statement(stmt.init, current, function_ir)
        cond_label = self._new_label('for_cond')
        body_label = self._new_label('for_body')
        end_label = self._new_label('for_end')

        current.add(Instruction('JUMP', None, [cond_label]))

        cond_block = BasicBlock(cond_label)
        function_ir.add_block(cond_block)
        if stmt.condition:
            cond_temp, cond_block = self._generate_expression(stmt.condition, cond_block, function_ir)
        else:
            cond_temp = 'true'
        cond_block.add(Instruction('JUMP_IF', None, [cond_temp, body_label], comment='for true'))
        cond_block.add(Instruction('JUMP', None, [end_label], comment='for false'))

        body_block = BasicBlock(body_label)
        function_ir.add_block(body_block)
        self._enter_scope()
        end_body = self._generate_statement(stmt.body, body_block, function_ir)
        if stmt.update:
            _, end_body = self._generate_expression(stmt.update, end_body, function_ir)
        self._exit_scope()
        if not end_body.terminator():
            end_body.add(Instruction('JUMP', None, [cond_label]))

        end_block = BasicBlock(end_label)
        function_ir.add_block(end_block)
        return end_block

    def _generate_return(self, stmt: ReturnStmtNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        if stmt.value:
            value, current = self._generate_expression(stmt.value, current, function_ir)
            current.add(Instruction('RETURN', None, [value]))
        else:
            current.add(Instruction('RETURN'))
        return current

    def _generate_variable_decl(self, stmt: VarDeclNode, current: BasicBlock, function_ir: FunctionIR) -> BasicBlock:
        mem_name = self._declare_variable(stmt.name)
        function_ir.local_allocations.append(mem_name)
        current.add(Instruction('ALLOCA', mem_name, ['1'], comment=f'var {stmt.name}'))
        if stmt.initializer:
            value, current = self._generate_expression(stmt.initializer, current, function_ir)
            current.add(Instruction('STORE', None, [f'[{mem_name}]', value], comment=f'{stmt.name} = init'))
        return current

    def _generate_expression(self, expr: ExpressionNode, current: BasicBlock, function_ir: FunctionIR) -> tuple[str, BasicBlock]:
        if isinstance(expr, LiteralExprNode):
            if isinstance(expr.value, bool):
                return ('true' if expr.value else 'false'), current
            return (str(expr.value), current)
        if isinstance(expr, IdentifierExprNode):
            mem_name = self._lookup_variable(expr.name)
            if not mem_name:
                mem_name = expr.name
            temp = self._new_temp()
            current.add(Instruction('LOAD', temp, [f'[{mem_name}]'], comment=f'load {expr.name}'))
            return temp, current
        if isinstance(expr, BinaryExprNode):
            if expr.operator in {'&&', '||'}:
                return self._generate_logical_expression(expr, current, function_ir)
            left, current = self._generate_expression(expr.left, current, function_ir)
            right, current = self._generate_expression(expr.right, current, function_ir)
            op = OPERATOR_MAP.get(expr.operator)
            result = self._new_temp()
            type_comment = f"type={expr.type}" if getattr(expr, 'type', None) is not None else None
            if op:
                current.add(Instruction(op, result, [left, right], comment=(f"{expr.operator}" + (f" ({type_comment})" if type_comment else ''))))
            else:
                current.add(Instruction('MOVE', result, [left], comment='unsupported binary op'))
            return result, current
        if isinstance(expr, UnaryExprNode):
            operand, current = self._generate_expression(expr.operand, current, function_ir)
            op = UNARY_MAP.get(expr.operator, 'MOVE')
            result = self._new_temp()
            type_comment = f"type={expr.type}" if getattr(expr, 'type', None) is not None else None
            if expr.operator == '+':
                current.add(Instruction(op, result, [operand], comment=('unary plus' + (f' ({type_comment})' if type_comment else ''))))
            elif expr.operator == '-':
                current.add(Instruction(op, result, ['0', operand], comment=('unary negation' + (f' ({type_comment})' if type_comment else ''))))
            else:
                current.add(Instruction(op, result, [operand], comment=('unary' + (f' ({type_comment})' if type_comment else ''))))
            return result, current
        if isinstance(expr, AssignmentExprNode):
            value, current = self._generate_expression(expr.value, current, function_ir)
            mem_name = self._lookup_variable(expr.target.name)
            if not mem_name:
                mem_name = expr.target.name
            current.add(Instruction('STORE', None, [f'[{mem_name}]', value], comment=f'{expr.target.name} ='))
            temp = self._new_temp()
            current.add(Instruction('MOVE', temp, [value], comment=('assignment result' + (f' (type={expr.type})' if getattr(expr, 'type', None) is not None else ''))))
            if self.last_assignments is not None:
                self.last_assignments[expr.target.name] = temp
            return temp, current
        if isinstance(expr, CallExprNode):
            arg_values = []
            for arg in expr.arguments:
                val, current = self._generate_expression(arg, current, function_ir)
                arg_values.append(val)
            for idx, val in enumerate(arg_values):
                current.add(Instruction('PARAM', None, [str(idx), val], comment=f'param {idx}'))
            result = self._new_temp()
            type_comment = f"type={expr.type}" if getattr(expr, 'type', None) is not None else None
            current.add(Instruction('CALL', result, [expr.callee] + arg_values, comment=('function call' + (f' ({type_comment})' if type_comment else ''))))
            return result, current
        temp = self._new_temp()
        current.add(Instruction('MOVE', temp, ['0'], comment=f'unsupported expr {type(expr).__name__}'))
        return temp, current

    def _generate_logical_expression(self, expr: BinaryExprNode, current: BasicBlock, function_ir: FunctionIR) -> tuple[str, BasicBlock]:
        left_temp, current = self._generate_expression(expr.left, current, function_ir)
        rhs_label = self._new_label('rhs')
        true_label = self._new_label('logical_true')
        false_label = self._new_label('logical_false')
        end_label = self._new_label('logical_end')
        result = self._new_temp()

        if expr.operator == '&&':
            current.add(Instruction('JUMP_IF_NOT', None, [left_temp, false_label], comment='and lhs false'))
            current.add(Instruction('JUMP', None, [rhs_label]))
        else:
            current.add(Instruction('JUMP_IF', None, [left_temp, true_label], comment='or lhs true'))
            current.add(Instruction('JUMP', None, [rhs_label]))

        rhs_block = BasicBlock(rhs_label)
        function_ir.add_block(rhs_block)
        right_temp, rhs_block = self._generate_expression(expr.right, rhs_block, function_ir)
        if expr.operator == '&&':
            rhs_block.add(Instruction('JUMP_IF_NOT', None, [right_temp, false_label], comment='and rhs false'))
            rhs_block.add(Instruction('JUMP', None, [true_label]))
        else:
            rhs_block.add(Instruction('JUMP_IF', None, [right_temp, true_label], comment='or rhs true'))
            rhs_block.add(Instruction('JUMP', None, [false_label]))

        true_block = BasicBlock(true_label)
        function_ir.add_block(true_block)
        true_block.add(Instruction('MOVE', result, ['1'], comment=f'{expr.operator} result true'))
        true_block.add(Instruction('JUMP', None, [end_label]))

        false_block = BasicBlock(false_label)
        function_ir.add_block(false_block)
        false_block.add(Instruction('MOVE', result, ['0'], comment=f'{expr.operator} result false'))
        false_block.add(Instruction('JUMP', None, [end_label]))

        end_block = BasicBlock(end_label)
        function_ir.add_block(end_block)
        return result, end_block

    def _enter_scope(self) -> None:
        self.variable_stack.append({})

    def _push_assignments(self) -> None:
        self._assignments_stack.append(self.last_assignments)
        self.last_assignments = {}

    def _pop_assignments(self) -> Dict[str, str]:
        assigns = self.last_assignments
        if self._assignments_stack:
            self.last_assignments = self._assignments_stack.pop()
        else:
            self.last_assignments = {}
        return assigns

    def _exit_scope(self) -> None:
        if self.variable_stack:
            self.variable_stack.pop()

    def _declare_variable(self, name: str) -> str:
        unique_name = f'{name}_{len(self.variable_stack) - 1 if self.variable_stack else 0}'
        self.variable_stack[-1][name] = unique_name
        if self.current_function is not None:
            self.current_function.variable_map[name] = unique_name
        return unique_name

    def _lookup_variable(self, name: str) -> Optional[str]:
        for scope in reversed(self.variable_stack):
            if name in scope:
                return scope[name]
        return None

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f't{self.temp_counter}'

    def _new_label(self, prefix: str) -> str:
        self.label_counter += 1
        return f'L_{prefix}_{self.label_counter}'

    def _add_comment(self, current: BasicBlock, text: str) -> None:
        current.add(Instruction('MOVE', None, [], comment=text))
