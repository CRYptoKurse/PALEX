import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
VALID_DIR = ROOT / "tests" / "semantic" / "valid"
INVALID_DIR = ROOT / "tests" / "semantic" / "invalid"


def test_valid_file(path: Path) -> bool:
    result = subprocess.run(
        ["python", str(ROOT / "src" / "main.py"), "--input", str(path), "--semantic"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"FAIL: {path} - expected semantic success")
        print(result.stderr)
        return False
    print(f"PASS: {path}")
    return True


def test_invalid_file(path: Path) -> bool:
    result = subprocess.run(
        ["python", str(ROOT / "src" / "main.py"), "--input", str(path), "--semantic"],
        capture_output=True, text=True
    )
    has_error = result.returncode != 0 or "semantic error" in result.stderr.lower()
    if has_error:
        print(f"PASS (error detected): {path}")
        return True
    print(f"FAIL: {path} - expected semantic error")
    print(result.stderr)
    return False


def main():
    all_passed = True

    if VALID_DIR.exists():
        for src in sorted(VALID_DIR.rglob("*.src")):
            if not test_valid_file(src):
                all_passed = False
    else:
        print("Warning: semantic valid tests directory not found", file=sys.stderr)

    if INVALID_DIR.exists():
        for src in sorted(INVALID_DIR.rglob("*.src")):
            if not test_invalid_file(src):
                all_passed = False
    else:
        print("Warning: semantic invalid tests directory not found", file=sys.stderr)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
