from typing import Dict
from .ir import IRProgram, FunctionIR, BasicBlock, Instruction


def optimize_ir(program: IRProgram) -> None:
    # Simple block-local constant propagation and folding
    for func in program.functions:
        for block in func.blocks:
            consts: Dict[str, str] = {}
            new_instrs = []
            for instr in block.instructions:
                # track simple moves of constants into temps
                if instr.op == 'MOVE' and instr.dest and instr.args:
                    src = instr.args[0]
                    # detect numeric constants
                    if isinstance(src, str):
                        try:
                            float(src)
                            consts[instr.dest] = src
                        except Exception:
                            # if src is a known constant temp, propagate
                            if src in consts:
                                consts[instr.dest] = consts[src]
                    new_instrs.append(instr)
                    continue

                # fold binary ops when operands are constants
                if instr.op in {'ADD', 'SUB', 'MUL', 'DIV', 'MOD'} and instr.dest and len(instr.args) >= 2:
                    a0, a1 = instr.args[0], instr.args[1]
                    v0 = consts.get(a0, a0)
                    v1 = consts.get(a1, a1)
                    try:
                        n0 = float(v0)
                        n1 = float(v1)
                        if instr.op == 'ADD':
                            res = n0 + n1
                        elif instr.op == 'SUB':
                            res = n0 - n1
                        elif instr.op == 'MUL':
                            res = n0 * n1
                        elif instr.op == 'DIV':
                            res = n0 / n1 if n1 != 0 else None
                        elif instr.op == 'MOD':
                            res = n0 % n1 if n1 != 0 else None
                        else:
                            res = None
                        if res is not None:
                            # replace with MOVE dest, [const]
                            const_str = str(int(res)) if res.is_integer() else str(res)
                            new_instrs.append(Instruction('MOVE', instr.dest, [const_str], comment=f'folded {instr.op}'))
                            consts[instr.dest] = const_str
                            continue
                    except Exception:
                        pass

                # propagate known const operands for other ops
                new_args = [consts.get(a, a) for a in instr.args]
                instr.args = new_args
                new_instrs.append(instr)

            block.instructions = new_instrs
