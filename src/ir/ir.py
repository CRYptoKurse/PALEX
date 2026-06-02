from __future__ import annotations
import json
from typing import List, Optional, Dict, Any

class Instruction:
    def __init__(self, op: str, dest: Optional[str] = None, args: Optional[List[str]] = None, comment: str = ''):
        self.op = op
        self.dest = dest
        self.args = args or []
        self.comment = comment

    def __str__(self) -> str:
        parts = []
        if self.dest:
            parts.append(self.dest)
            parts.append('=')
        parts.append(self.op)
        if self.args:
            if self.op == 'PHI' and len(self.args) % 2 == 0:
                phi_parts = []
                for i in range(0, len(self.args), 2):
                    phi_parts.append(f"({self.args[i]}, {self.args[i + 1]})")
                parts.append(' ' + ', '.join(phi_parts))
            else:
                parts.append(' ' + ', '.join(self.args))
        text = ' '.join(parts)
        if self.comment:
            text = f"{text}  # {self.comment}"
        return text

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'op': self.op,
            'dest': self.dest,
            'args': self.args,
            'comment': self.comment,
        }
        if self.op == 'PHI' and len(self.args) % 2 == 0:
            result['phi_pairs'] = [
                {'value': self.args[i], 'label': self.args[i + 1]}
                for i in range(0, len(self.args), 2)
            ]
        return result

class BasicBlock:
    def __init__(self, label: str):
        self.label = label
        self.instructions: List[Instruction] = []

    def add(self, instr: Instruction) -> None:
        self.instructions.append(instr)

    def terminator(self) -> Optional[Instruction]:
        if self.instructions:
            last = self.instructions[-1]
            if last.op in {'JUMP', 'JUMP_IF', 'JUMP_IF_NOT', 'RETURN'}:
                return last
        return None

    def to_text(self) -> str:
        lines = [f"  {self.label}:"]
        for instr in self.instructions:
            lines.append(f"    {instr}")
        return '\n'.join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'label': self.label,
            'instructions': [instr.to_dict() for instr in self.instructions],
        }

class FunctionIR:
    def __init__(self, name: str, return_type: str, params: List[str], param_types: Optional[List[str]] = None):
        self.name = name
        self.return_type = return_type
        self.params = params
        self.param_types = param_types or ['int' for _ in params]
        self.blocks: List[BasicBlock] = []
        self.local_allocations: List[str] = []
        self.variable_map: Dict[str, str] = {}

    def add_block(self, block: BasicBlock) -> None:
        self.blocks.append(block)

    def get_block(self, label: str) -> Optional[BasicBlock]:
        for block in self.blocks:
            if block.label == label:
                return block
        return None

    def to_text(self) -> str:
        params = ', '.join(
            f"{ptype} {pname}" for ptype, pname in zip(self.param_types, self.params)
        )
        lines = [f"function {self.name}: {self.return_type} ({params})"]
        for block in self.blocks:
            lines.append(block.to_text())
        return '\n'.join(lines)

    def to_dot(self) -> str:
        lines = ['digraph CFG {', '  node [shape=box];']
        for block in self.blocks:
            label = '\n'.join(str(instr).replace('"', '\\"') for instr in block.instructions)
            style = 'filled' if block.label == 'entry' else 'solid'
            color = 'lightgreen' if block.label == 'entry' else ('lightcoral' if block.terminator() and block.terminator().op == 'RETURN' else 'lightgrey')
            lines.append(
                f'  {block.label} [label="{block.label}:\\n{label}", style="{style}", fillcolor="{color}"];'
            )
        for index, block in enumerate(self.blocks):
            term = block.terminator()
            if term:
                if term.op == 'JUMP' and term.args:
                    lines.append(f'  {block.label} -> {term.args[0]};')
                elif term.op == 'JUMP_IF' and term.args:
                    lines.append(f'  {block.label} -> {term.args[1]} [label="true"];')
                    next_label = self.blocks[index + 1].label if index + 1 < len(self.blocks) else None
                    if next_label:
                        lines.append(f'  {block.label} -> {next_label} [label="false"];')
                elif term.op == 'JUMP_IF_NOT' and term.args:
                    lines.append(f'  {block.label} -> {term.args[1]} [label="false"];')
                    next_label = self.blocks[index + 1].label if index + 1 < len(self.blocks) else None
                    if next_label:
                        lines.append(f'  {block.label} -> {next_label} [label="true"];')
            else:
                next_label = self.blocks[index + 1].label if index + 1 < len(self.blocks) else None
                if next_label:
                    lines.append(f'  {block.label} -> {next_label};')
        lines.append('}')
        return '\n'.join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'return_type': self.return_type,
            'params': self.params,
            'param_types': self.param_types,
            'blocks': [block.to_dict() for block in self.blocks],
            'locals': self.local_allocations,
        }

class IRProgram:
    def __init__(self):
        self.functions: List[FunctionIR] = []
        self.globals: List[str] = []

    def add_function(self, function: FunctionIR) -> None:
        self.functions.append(function)

    def add_global(self, declaration: str) -> None:
        self.globals.append(declaration)

    def get_function(self, name: str) -> Optional[FunctionIR]:
        for function in self.functions:
            if function.name == name:
                return function
        return None

    def to_text(self) -> str:
        lines = []
        for global_decl in self.globals:
            lines.append(global_decl)
        if self.globals:
            lines.append('')
        for function in self.functions:
            lines.append(function.to_text())
            lines.append('')
        return '\n'.join(lines).strip()

    def to_dot(self) -> str:
        sections = []
        for function in self.functions:
            sections.append(function.to_dot())
        return '\n\n'.join(sections)

    def to_json(self) -> str:
        return json.dumps({'functions': [func.to_dict() for func in self.functions]}, indent=2)

    def get_stats(self) -> Dict[str, int]:
        instr_count = 0
        block_count = 0
        temp_set = set()
        for func in self.functions:
            block_count += len(func.blocks)
            for block in func.blocks:
                instr_count += len(block.instructions)
                for instr in block.instructions:
                    if instr.dest and instr.dest.startswith('t'):
                        temp_set.add(instr.dest)
                    for a in instr.args:
                        if isinstance(a, str) and a.startswith('t'):
                            temp_set.add(a)
        return {
            'functions': len(self.functions),
            'basic_blocks': block_count,
            'instructions': instr_count,
            'temporaries': len(temp_set),
        }
