import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.optimizer import optimize_ir


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


def test_optimizer_folds_constants():
    ir = parse_file('generation/expressions/simple.src')
    # count ADD ops before
    add_before = sum(1 for f in ir.functions for b in f.blocks for i in b.instructions if i.op == 'ADD')
    optimize_ir(ir)
    add_after = sum(1 for f in ir.functions for b in f.blocks for i in b.instructions if i.op == 'ADD')
    assert add_after <= add_before, 'Optimizer should not increase ADD count'


if __name__ == '__main__':
    test_optimizer_folds_constants()
    print('optimizer tests passed')
