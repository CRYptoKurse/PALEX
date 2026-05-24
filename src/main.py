import sys
import argparse
from pathlib import Path

# Add project root to sys.path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.parser.ast_visitors import PrettyPrinter, DotVisitor, JsonVisitor
from src.semantic.analyzer import SemanticAnalyzer



def main():
    parser = argparse.ArgumentParser(description="MiniCompiler - Sprint 3")
    parser.add_argument("--input", "-i", type=str, help="Input source file")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")
    parser.add_argument("--ast-format", choices=["text", "dot", "json"], default="text",
                        help="AST output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show extra information")
    parser.add_argument("--semantic", action="store_true", help="Run semantic analysis")
    parser.add_argument("--dump-symbols", action="store_true", help="Print symbol table after semantic analysis")
    parser.add_argument("--no-preprocessor", action="store_true", help="Disable preprocessor")
    args = parser.parse_args()

    # Read source
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    else:
        source = sys.stdin.read()

    # Lexical analysis
    scanner = Scanner(source, use_preprocessor=not args.no_preprocessor)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if args.verbose and tok.type.name != "END_OF_FILE":
            print(f"[LEX] {tok}", file=sys.stderr)
    tokens.append(scanner.next_token())  # final EOF

    # Report preprocessor/lexer errors
    errors = scanner.preprocessor_errors + scanner.errors
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        if args.verbose:
            print("Aborting due to lexical errors.", file=sys.stderr)
        sys.exit(1)

    # Parsing
    parser_obj = Parser(tokens)
    try:
        ast = parser_obj.parse()
    except Exception as e:
        print(f"Parser fatal error: {e}", file=sys.stderr)
        sys.exit(1)

    if parser_obj.errors:
        for err in parser_obj.errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    analyzer = None
    if args.semantic:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        semantic_errors = analyzer.get_errors()
        if semantic_errors:
            for err in semantic_errors:
                print(err, file=sys.stderr)
            sys.exit(1)

    # Generate output
    if args.ast_format == "text":
        visitor = PrettyPrinter()
        ast.accept(visitor)
        output = visitor.get_text()
    elif args.ast_format == "dot":
        visitor = DotVisitor()
        ast.accept(visitor)
        output = visitor.get_dot()
    elif args.ast_format == "json":
        visitor = JsonVisitor()
        ast.accept(visitor)
        output = visitor.get_json()
    else:
        output = ""

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if args.dump_symbols and analyzer is not None:
                f.write(output + "\n\n" + analyzer.get_symbol_table().dump())
            else:
                f.write(output)
    else:
        print(output)
        if args.dump_symbols and analyzer is not None:
            print("\n\n" + analyzer.get_symbol_table().dump())

    sys.exit(0)

if __name__ == "__main__":
    main()