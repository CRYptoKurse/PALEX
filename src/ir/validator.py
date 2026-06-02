from typing import List
from .ir import IRProgram, FunctionIR, BasicBlock, Instruction


def validate_ir(program: IRProgram) -> List[str]:
    errors: List[str] = []
    for func in program.functions:
        labels = {block.label for block in func.blocks}
        # check blocks terminators
        for idx, block in enumerate(func.blocks):
            term = block.terminator()
            if term is None and idx != len(func.blocks) - 1:
                errors.append(f"Function '{func.name}': block '{block.label}' missing terminator")
        # check jump targets
        for block in func.blocks:
            for instr in block.instructions:
                if instr.op == 'JUMP':
                    if not instr.args:
                        errors.append(f"Function '{func.name}': JUMP in '{block.label}' missing target")
                    else:
                        target = instr.args[0]
                        if target not in labels:
                            errors.append(f"Function '{func.name}': JUMP target '{target}' from '{block.label}' not found")
                if instr.op in {'JUMP_IF', 'JUMP_IF_NOT'}:
                    if len(instr.args) < 2:
                        errors.append(f"Function '{func.name}': {instr.op} in '{block.label}' missing target")
                    else:
                        target = instr.args[1]
                        if target not in labels:
                            errors.append(f"Function '{func.name}': {instr.op} target '{target}' from '{block.label}' not found")
                if instr.op == 'PHI':
                    # ensure phi args are value,label pairs
                    if len(instr.args) % 2 != 0:
                        errors.append(f"Function '{func.name}': PHI in '{block.label}' has invalid arg count")
                    else:
                        for i in range(0, len(instr.args), 2):
                            val = instr.args[i]
                            label = instr.args[i + 1]
                            if label not in labels:
                                errors.append(f"Function '{func.name}': PHI in '{block.label}' references unknown label '{label}'")
                            if isinstance(val, str) and val.startswith('t'):
                                continue
                            if val in {'true', 'false'}:
                                continue
                            try:
                                float(val)
                                continue
                            except Exception:
                                errors.append(f"Function '{func.name}': PHI in '{block.label}' has unknown value '{val}'")
    return errors
