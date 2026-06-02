import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / 'tests' / 'codegen' / 'valid' / 'arithmetic_ops' / 'simple_add.src'


def compile_source(source_path: Path, output_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / 'src' / 'main.py'), '--input', str(source_path), '--compile', '--target', 'x86_64', '--output', str(output_path)],
        capture_output=True,
        text=True,
    )


def test_generate_assembly() -> bool:
    output_path = ROOT / 'build' / 'simple_add.asm'
    output_path.parent.mkdir(exist_ok=True, parents=True)
    result = compile_source(SRC, output_path)
    if result.returncode != 0:
        print('FAIL: assembly generation failed')
        print(result.stderr)
        return False
    asm = output_path.read_text(encoding='utf-8')
    if 'global add' not in asm or 'global main' not in asm:
        print('FAIL: missing expected symbols in generated assembly')
        return False
    print('PASS: assembly generation')
    return True


def test_assemble_and_run() -> bool:
    if not shutil.which('nasm') or not shutil.which('ld'):
        print('SKIP: nasm or ld not installed')
        return True

    workdir = ROOT / 'build'
    workdir.mkdir(exist_ok=True, parents=True)
    asm_file = workdir / 'simple_add.asm'
    obj_file = workdir / 'simple_add.o'
    runtime_obj = workdir / 'runtime.o'
    binary = workdir / 'simple_add_exec'

    result = compile_source(SRC, asm_file)
    if result.returncode != 0:
        print('FAIL: assembly generation failed')
        print(result.stderr)
        return False

    result = subprocess.run(['nasm', '-f', 'elf64', '-o', str(obj_file), str(asm_file)], capture_output=True, text=True)
    if result.returncode != 0:
        print('FAIL: nasm assembly failed')
        print(result.stderr)
        return False

    result = subprocess.run(['nasm', '-f', 'elf64', '-o', str(runtime_obj), str(ROOT / 'src' / 'runtime' / 'runtime.asm')], capture_output=True, text=True)
    if result.returncode != 0:
        print('FAIL: nasm runtime assembly failed')
        print(result.stderr)
        return False

    result = subprocess.run(['ld', '-o', str(binary), str(runtime_obj), str(obj_file)], capture_output=True, text=True)
    if result.returncode != 0:
        print('FAIL: linking failed')
        print(result.stderr)
        return False

    result = subprocess.run([str(binary)], capture_output=True, text=True)
    if result.returncode != 5:
        print(f'FAIL: expected return code 5, got {result.returncode}')
        return False

    print('PASS: assembly build and execution')
    return True


if __name__ == '__main__':
    total = 0
    passed = 0
    for test_fn in [test_generate_assembly, test_assemble_and_run]:
        total += 1
        if test_fn():
            passed += 1
    print(f'\nSummary: {passed}/{total} passed')
    sys.exit(0 if passed == total else 1)
