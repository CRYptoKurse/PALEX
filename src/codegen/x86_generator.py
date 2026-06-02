from __future__ import annotations
import re
from typing import Dict, List, Optional
from src.ir.ir import IRProgram, FunctionIR, BasicBlock, Instruction

ARG_REGS = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
CMP_SET = {
    'CMP_EQ': 'e',
    'CMP_NE': 'ne',
    'CMP_LT': 'l',
    'CMP_LE': 'le',
    'CMP_GT': 'g',
    'CMP_GE': 'ge',
}


class FrameInfo:
    def __init__(self, function: FunctionIR):
        self.function = function
        self.slot_map: Dict[str, int] = {}
        self.stack_size = 0
        self.epilogue_label = self._sanitize_label(f'{function.name}_epilogue')
        self._assign_slots()

    def _assign_slots(self) -> None:
        offset = 0
        for name in self.function.local_allocations:
            if name not in self.slot_map:
                offset += 8
                self.slot_map[name] = -offset

        temps = set()
        for block in self.function.blocks:
            for instr in block.instructions:
                if instr.dest and instr.dest.startswith('t'):
                    temps.add(instr.dest)
                for arg in instr.args:
                    if isinstance(arg, str) and arg.startswith('t'):
                        temps.add(arg)
        for temp in sorted(temps):
            if temp not in self.slot_map:
                offset += 8
                self.slot_map[temp] = -offset

        self.stack_size = max(((offset + 15) // 16) * 16, 16)

    def slot(self, name: str) -> str:
        if name in self.slot_map:
            offset = self.slot_map[name]
            return f'[rbp{offset}]'
        return f'[{name}]'

    def _sanitize_label(self, label: str) -> str:
        return '.L' + re.sub(r'[^A-Za-z0-9_]', '_', label)


class X86Generator:
    def __init__(self, program: IRProgram):
        self.program = program

    def generate(self) -> str:
        lines = ['section .text', 'global _start']
        externs = ['print_int', 'print_string', 'read_int', 'exit']
        for extern in externs:
            lines.append(f'extern {extern}')
        lines.append('')

        for function in self.program.functions:
            lines.extend(self._emit_function(function))
            lines.append('')

        return '\n'.join(lines).strip() + '\n'

    def _emit_function(self, function: FunctionIR) -> List[str]:
        frame = FrameInfo(function)
        label_map = {
            block.label: self._sanitize_label(f'{function.name}_{block.label}')
            for block in function.blocks
        }
        lines: List[str] = []
        lines.append(f'global {function.name}')
        lines.append(f'{function.name}:')
        lines.append('    push rbp')
        lines.append('    mov rbp, rsp')
        lines.append(f'    sub rsp, {frame.stack_size}')
        lines.extend(self._emit_parameter_setup(function, frame))

        for block in function.blocks:
            sanitized = label_map[block.label]
            lines.append(f'{sanitized}:')
            lines.extend(self._emit_block(block, frame, label_map))

        if not self._has_explicit_return(function):
            lines.append('    mov rax, 0')
            lines.append(f'    jmp {frame.epilogue_label}')

        lines.append(f'{frame.epilogue_label}:')
        lines.append('    mov rsp, rbp')
        lines.append('    pop rbp')
        lines.append('    ret')
        return lines

    def _emit_parameter_setup(self, function: FunctionIR, frame: FrameInfo) -> List[str]:
        lines: List[str] = []
        for index, param in enumerate(function.params):
            mem = function.variable_map.get(param, param)
            slot = frame.slot(mem)
            if index < len(ARG_REGS):
                lines.append(f'    mov qword {slot}, {ARG_REGS[index]}')
            else:
                stack_offset = 16 + 8 * (index - len(ARG_REGS))
                lines.append(f'    mov rax, qword [rbp+{stack_offset}]')
                lines.append(f'    mov qword {slot}, rax')
        return lines

    def _emit_block(self, block: BasicBlock, frame: FrameInfo, label_map: Dict[str, str]) -> List[str]:
        lines: List[str] = []
        for instr in block.instructions:
            lines.extend(self._emit_instruction(instr, frame, label_map))
        return lines

    def _emit_instruction(self, instr: Instruction, frame: FrameInfo, label_map: Dict[str, str]) -> List[str]:
        op = instr.op
        if op == 'ALLOCA':
            return []
        if op == 'PARAM':
            return [f'    ; PARAM {" ".join(instr.args)}']
        if op == 'PHI':
            return [f'    ; PHI {instr.dest}']
        if op == 'LOAD':
            if instr.dest is None or not instr.args:
                return ['    ; malformed LOAD']
            return self._emit_load(instr.dest, instr.args[0], frame)
        if op == 'STORE':
            if len(instr.args) < 2:
                return ['    ; malformed STORE']
            return self._emit_store(instr.args[0], instr.args[1], frame)
        if op in {'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'AND', 'OR', 'XOR'}:
            return self._emit_binary(instr, frame)
        if op in CMP_SET:
            return self._emit_compare(instr, frame)
        if op == 'NOT':
            return self._emit_not(instr, frame)
        if op == 'MOVE':
            return self._emit_move(instr, frame)
        if op == 'CALL':
            return self._emit_call(instr, frame)
        if op == 'RETURN':
            return self._emit_return(instr, frame)
        if op == 'JUMP':
            if instr.args:
                target = label_map.get(instr.args[0], self._sanitize_label(instr.args[0]))
                return [f'    jmp {target}']
            return ['    ; malformed JUMP']
        if op == 'JUMP_IF':
            return self._emit_conditional(instr, frame, label_map, invert=False)
        if op == 'JUMP_IF_NOT':
            return self._emit_conditional(instr, frame, label_map, invert=True)
        return [f'    ; unsupported op {op}']

    def _emit_load(self, dest: str, source: str, frame: FrameInfo) -> List[str]:
        lines: List[str] = []
        self._load_operand_to_reg(source, 'rax', frame, lines)
        lines.append(f'    mov qword {frame.slot(dest)}, rax')
        return lines

    def _emit_store(self, target: str, source: str, frame: FrameInfo) -> List[str]:
        lines: List[str] = []
        self._load_operand_to_reg(source, 'rax', frame, lines)
        if target.startswith('[') and target.endswith(']'):
            mem = self._format_memory(target, frame)
            lines.append(f'    mov qword {mem}, rax')
        else:
            lines.append(f'    mov qword {frame.slot(target)}, rax')
        return lines

    def _emit_move(self, instr: Instruction, frame: FrameInfo) -> List[str]:
        if instr.dest is None or not instr.args:
            return ['    ; malformed MOVE']
        lines: List[str] = []
        self._load_operand_to_reg(instr.args[0], 'rax', frame, lines)
        lines.append(f'    mov qword {frame.slot(instr.dest)}, rax')
        return lines

    def _emit_binary(self, instr: Instruction, frame: FrameInfo) -> List[str]:
        if instr.dest is None or len(instr.args) < 2:
            return ['    ; malformed binary']
        lines: List[str] = []
        self._load_operand_to_reg(instr.args[0], 'rax', frame, lines)
        self._load_operand_to_reg(instr.args[1], 'rbx', frame, lines)
        if instr.op == 'ADD':
            lines.append('    add rax, rbx')
        elif instr.op == 'SUB':
            lines.append('    sub rax, rbx')
        elif instr.op == 'MUL':
            lines.append('    imul rax, rbx')
        elif instr.op == 'DIV':
            lines.append('    cqo')
            lines.append('    idiv rbx')
        elif instr.op == 'MOD':
            lines.append('    cqo')
            lines.append('    idiv rbx')
            lines.append('    mov rax, rdx')
        elif instr.op == 'AND':
            lines.append('    and rax, rbx')
        elif instr.op == 'OR':
            lines.append('    or rax, rbx')
        elif instr.op == 'XOR':
            lines.append('    xor rax, rbx')
        lines.append(f'    mov qword {frame.slot(instr.dest)}, rax')
        return lines

    def _emit_compare(self, instr: Instruction, frame: FrameInfo) -> List[str]:
        if instr.dest is None or len(instr.args) < 2:
            return ['    ; malformed compare']
        lines: List[str] = []
        self._load_operand_to_reg(instr.args[0], 'rax', frame, lines)
        self._load_operand_to_reg(instr.args[1], 'rbx', frame, lines)
        lines.append('    cmp rax, rbx')
        suffix = CMP_SET[instr.op]
        lines.append(f'    set{suffix} al')
        lines.append('    movzx rax, al')
        lines.append(f'    mov qword {frame.slot(instr.dest)}, rax')
        return lines

    def _emit_not(self, instr: Instruction, frame: FrameInfo) -> List[str]:
        if instr.dest is None or not instr.args:
            return ['    ; malformed NOT']
        lines: List[str] = []
        self._load_operand_to_reg(instr.args[0], 'rax', frame, lines)
        lines.append('    cmp rax, 0')
        lines.append('    sete al')
        lines.append('    movzx rax, al')
        lines.append(f'    mov qword {frame.slot(instr.dest)}, rax')
        return lines

    def _emit_call(self, instr: Instruction, frame: FrameInfo) -> List[str]:
        lines: List[str] = []
        if instr.dest is None or not instr.args:
            return ['    ; malformed CALL']
        func_name = instr.args[0]
        call_args = instr.args[1:]
        stack_args = call_args[6:]
        if stack_args and len(stack_args) % 2 == 1:
            lines.append('    sub rsp, 8')
        for arg in reversed(stack_args):
            self._load_operand_to_reg(arg, 'rax', frame, lines)
            lines.append('    push rax')
        for index, arg in enumerate(call_args[:6]):
            self._load_operand_to_reg(arg, ARG_REGS[index], frame, lines)
        lines.append(f'    call {func_name}')
        if stack_args:
            cleanup = 8 * len(stack_args)
            if len(stack_args) % 2 == 1:
                cleanup += 8
            lines.append(f'    add rsp, {cleanup}')
        lines.append(f'    mov qword {frame.slot(instr.dest)}, rax')
        return lines

    def _emit_return(self, instr: Instruction, frame: FrameInfo) -> List[str]:
        lines: List[str] = []
        if instr.args:
            self._load_operand_to_reg(instr.args[0], 'rax', frame, lines)
        lines.append(f'    jmp {frame.epilogue_label}')
        return lines

    def _emit_conditional(self, instr: Instruction, frame: FrameInfo, label_map: Dict[str, str], invert: bool) -> List[str]:
        lines: List[str] = []
        if len(instr.args) < 2:
            return ['    ; malformed conditional']
        self._load_operand_to_reg(instr.args[0], 'rax', frame, lines)
        lines.append('    cmp rax, 0')
        target = label_map.get(instr.args[1], self._sanitize_label(instr.args[1]))
        if invert:
            lines.append(f'    je {target}')
        else:
            lines.append(f'    jne {target}')
        return lines

    def _has_explicit_return(self, function: FunctionIR) -> bool:
        for block in function.blocks:
            for instr in block.instructions:
                if instr.op == 'RETURN':
                    return True
        return False

    def _format_memory(self, operand: str, frame: FrameInfo) -> str:
        if operand.startswith('[') and operand.endswith(']'):
            inner = operand[1:-1]
            if inner in frame.slot_map:
                return f'[rbp{frame.slot_map[inner]}]'
            if inner.startswith('rbp') or inner.startswith('rsp'):
                return f'[{inner}]'
            return f'[{inner}]'
        return operand

    def _load_operand_to_reg(self, value: str, reg: str, frame: FrameInfo, lines: List[str]) -> None:
        if value == 'true':
            lines.append(f'    mov {reg}, 1')
            return
        if value == 'false':
            lines.append(f'    mov {reg}, 0')
            return
        if self._is_integer_literal(value):
            lines.append(f'    mov {reg}, {value}')
            return
        if value.startswith('[') and value.endswith(']'):
            mem = self._format_memory(value, frame)
            lines.append(f'    mov {reg}, qword {mem}')
            return
        if value in frame.slot_map:
            lines.append(f'    mov {reg}, qword {frame.slot(value)}')
            return
        lines.append(f'    mov {reg}, qword [{value}]')

    def _is_integer_literal(self, value: str) -> bool:
        if value.startswith('-'):
            return value[1:].isdigit()
        return value.isdigit()

    def _sanitize_label(self, label: str) -> str:
        return '.L' + re.sub(r'[^A-Za-z0-9_]', '_', label)
