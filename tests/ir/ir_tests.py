import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
IR_DIR = ROOT / "tests" / "ir"
GEN_DIR = IR_DIR / "generation"
VAL_DIR = IR_DIR / "validation"


def run_ir_test(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, str(ROOT / "src" / "main.py"), "--input", str(path), "--ir", "--ir-format", "text"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"FAIL: {path} - IR generation failed")
        print(result.stderr)
        return False

    golden_path = path.with_suffix('.ir')
    if not golden_path.exists():
        print(f"FAIL: {path} - missing golden file {golden_path}")
        return False

    expected = golden_path.read_text(encoding='utf-8').strip().replace('\r\n', '\n')
    actual = result.stdout.strip().replace('\r\n', '\n')
    if expected != actual:
        print(f"FAIL: {path} - output does not match golden")
        print('--- Expected ---')
        print(expected)
        print('--- Actual ---')
        print(actual)
        return False

    print(f"PASS: {path}")
    return True


def test_valid_ir_programs() -> bool:
    all_passed = True
    for src in sorted(GEN_DIR.rglob("*.src")):
        if not run_ir_test(src):
            all_passed = False
    return all_passed


def test_invalid_ir_programs() -> bool:
    all_passed = True
    for src in sorted(VAL_DIR.rglob("*.src")):
        result = subprocess.run(
            ["python", str(ROOT / "src" / "main.py"), "--input", str(src), "--ir"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"FAIL: {src} - expected semantic or parser error")
            print(result.stdout)
            all_passed = False
        else:
            print(f"PASS (error detected): {src}")
    return all_passed


def main():
    all_passed = True
    if not test_valid_ir_programs():
        all_passed = False
    if not test_invalid_ir_programs():
        all_passed = False
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
