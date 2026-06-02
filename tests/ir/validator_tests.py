import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.validator import validate_ir


def parse_file(path):
    sample_path = Path(path)
    if not sample_path.is_absolute():
        sample_path = Path(__file__).resolve().parent / sample_path
    with open(sample_path, 'r', encoding='utf-8') as f:
        src = f.read()
    scanner = Scanner(src)
    tokens = []
    while not scanner.is_at_end():
        tokens.append(scanner.next_token())
    tokens.append(scanner.next_token())
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    gen = IRGenerator(analyzer.get_symbol_table())
    ir = gen.generate(ast)
    return ir


def test_validator_on_valid_if_else():
    ir = parse_file('generation/control_flow/if_else.src')
    errors = validate_ir(ir)
    assert not errors, f"Expected no validation errors, got: {errors}"


def test_validator_detects_missing_terminator():
    ir = parse_file('generation/control_flow/if_else.src')
    func = ir.functions[0]
    for block in func.blocks:
        while block.terminator() is not None and block.instructions:
            block.instructions.pop()
        if block.terminator() is None:
            break
    errors = validate_ir(ir)
    assert errors and any('missing terminator' in e for e in errors), "Expected validation errors for missing terminator"


if __name__ == '__main__':
    test_validator_on_valid_if_else()
    test_validator_detects_missing_terminator()
    print('validator tests passed')
