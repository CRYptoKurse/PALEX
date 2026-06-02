#!/usr/bin/env python3
"""
Verify that generated x86-64 assembly is valid.
This script checks the assembly without requiring nasm/ld.
Works on Windows, Linux, and macOS.
"""
import sys
import re
from pathlib import Path


def verify_assembly(asm_file: str) -> bool:
    """Verify generated assembly has correct structure."""
    content = Path(asm_file).read_text()
    
    checks = [
        ("section .text", "Assembly must have .text section"),
        ("global _start", "Must export _start entry point"),
        ("extern print_int", "Must declare runtime functions"),
        ("push rbp", "Functions must have prologue (push rbp)"),
        ("mov rbp, rsp", "Functions must set up base pointer"),
        ("sub rsp", "Functions must allocate stack space"),
        ("pop rbp", "Functions must have epilogue (pop rbp)"),
        ("ret", "Functions must have return instruction"),
    ]
    
    print(f"📋 Verifying assembly: {asm_file}\n")
    all_passed = True
    
    for pattern, description in checks:
        found = pattern in content
        status = "✅" if found else "❌"
        print(f"{status} {description}")
        if not found:
            all_passed = False
    
    # Check for function labels
    functions = re.findall(r'^global (\w+)$', content, re.MULTILINE)
    print(f"\n📍 Found {len(functions)} functions:")
    for func in functions:
        print(f"   - {func}")
    
    # Check stack alignment
    stack_allocations = re.findall(r'sub rsp, (\d+)', content)
    if stack_allocations:
        print(f"\n📊 Stack allocations (should be multiples of 16):")
        for size in stack_allocations:
            size_int = int(size)
            aligned = "✅" if size_int % 16 == 0 else "⚠️"
            print(f"   {aligned} {size} bytes")
    
    # Check parameter passing (System V ABI)
    param_regs = re.findall(r'mov (rdi|rsi|rdx|rcx|r8|r9)', content)
    if param_regs:
        print(f"\n📤 Parameter registers used (System V ABI): {set(param_regs)}")
    
    # Check for runtime calls
    runtime_calls = re.findall(r'call (\w+)', content)
    if runtime_calls:
        print(f"\n📞 Runtime function calls:")
        for call in set(runtime_calls):
            print(f"   - {call}")
    
    print(f"\n{'='*50}")
    result = "✅ VALID" if all_passed else "❌ INVALID"
    print(f"Assembly validation: {result}")
    return all_passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_assembly.py <asm_file>")
        print("\nExample:")
        print("  python verify_assembly.py program.asm")
        sys.exit(1)
    
    asm_file = sys.argv[1]
    if not Path(asm_file).exists():
        print(f"❌ Error: {asm_file} not found")
        sys.exit(1)
    
    success = verify_assembly(asm_file)
    sys.exit(0 if success else 1)
