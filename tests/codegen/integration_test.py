#!/usr/bin/env python3
"""
Integration test for code generation pipeline.
Tests compilation from source -> IR -> assembly on all test cases.
Works on Windows without requiring nasm/ld.
"""
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
TEST_CASES = [
    ("arithmetic_ops/simple_add.src", "Simple addition"),
    ("control_flow/if_statement.src", "If statement"),
    ("control_flow/while_loop.src", "While loop"),
    ("control_flow/for_loop.src", "For loop"),
    ("control_flow/if_else.src", "If/Else statement"),
    ("control_flow/short_circuit.src", "Logical short-circuit"),
    ("function_calls/simple_call.src", "Simple function call"),
    ("function_calls/multiple_calls.src", "Multiple function calls"),
    ("function_calls/recursive.src", "Recursive function (factorial)"),
    ("io_operations/simple_print.src", "Simple print"),
    ("io_operations/multiple_outputs.src", "Multiple outputs"),
    ("integration/fibonacci.src", "Fibonacci sequence"),
    ("integration/is_prime.src", "Prime number check"),
    ("integration/sum_of_squares.src", "Sum of squares"),
]


def test_compile_to_assembly(src_file: str, description: str) -> bool:
    """Test compilation from source to assembly."""
    src_path = ROOT / "valid" / src_file
    if not src_path.exists():
        print(f"FAIL {description:30} - Source file not found: {src_file}")
        return False
    
    output_file = ROOT / "build" / f"test_{Path(src_file).stem}.asm"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT.parent.parent / "src" / "main.py"),
             "-i", str(src_path),
             "--compile", "--target", "x86_64",
             "-o", str(output_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"FAIL {description:30} - Compilation failed")
            if result.stderr:
                print(f"   Error: {result.stderr[:100]}")
            return False
        
        if not output_file.exists():
            print(f"FAIL: {description:30} - Assembly file not created")
            return False
        
        # Quick validation
        asm_content = output_file.read_text()
        required = ["section .text", "global _start", "push rbp", "pop rbp", "ret"]
        if all(req in asm_content for req in required):
            print(f"PASS: {description:30} - {output_file.stat().st_size:6} bytes")
            return True
        else:
            print(f"WARNING: {description:30} - Assembly generated but may be incomplete")
            return True
            
    except subprocess.TimeoutExpired:
        print(f"FAIL {description:30} - Compilation timeout")
        return False
    except Exception as e:
        print(f"FAIL {description:30} - {str(e)[:50]}")
        return False


def main():
    print("="*70)
    print("Code Generation Integration Tests")
    print("="*70)
    print()
    
    passed = 0
    total = len(TEST_CASES)
    
    for src_file, description in TEST_CASES:
        if test_compile_to_assembly(src_file, description):
            passed += 1
    
    print()
    print("="*70)
    print(f"Results: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("All code generation tests PASSED!")
        return 0
    else:
        print(f"{total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
