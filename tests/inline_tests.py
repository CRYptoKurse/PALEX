import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
ROOT = Path(__file__).parent.parent
VALID_DIR = ROOT / "tests" / "parser" / "valid"
INVALID_DIR = ROOT / "tests" / "parser" / "invalid"



def test_valid_file(path: Path) -> bool:
    """Для корректных программ проверяем, что парсер не падает и (опционально) AST совпадает с золотым."""
    result = subprocess.run(
        ["python", str(ROOT / "src" / "main.py"), "--input", str(path), "--ast-format", "text"],
        capture_output=True, text=True
    )
    # Если есть golden-файл .ast.txt, сверяем вывод
    expected_file = path.with_suffix(".ast")
    if expected_file.exists():
        expected = expected_file.read_text()
        if result.stdout.strip() != expected.strip():
            print(f"FAIL: {path} (AST mismatch)")
            return False
    else:
        # Нет golden – просто проверяем, что программа не завершилась с ошибкой
        if result.returncode != 0:
            print(f"CRASH: {path}\n{result.stderr}")
            return False
    print(f"PASS: {path}")
    return True

def test_invalid_file(path: Path) -> bool:
    """Для некорректных программ ожидаем, что парсер сообщит об ошибке."""
    result = subprocess.run(
        ["python", str(ROOT / "src" / "main.py"), "--input", str(path), "--ast-format", "text"],
        capture_output=True, text=True
    )
    # Проверяем, что либо код возврата ненулевой, либо в stderr есть слово "error"
    has_error = (result.returncode != 0) or ("error" in result.stderr.lower())
    if has_error:
        print(f"PASS (error detected): {path}")
        return True
    else:
        print(f"FAIL (expected error but got success): {path}")
        return False

def main():
    all_passed = True

    # Прогон валидных тестов
    if VALID_DIR.exists():
        for src in VALID_DIR.rglob("*.src"):
            if not test_valid_file(src):
                all_passed = False
    else:
        print("Warning: valid tests directory not found", file=sys.stderr)

    # Прогон невалидных тестов
    if INVALID_DIR.exists():
        for src in INVALID_DIR.rglob("*.src"):
            if not test_invalid_file(src):
                all_passed = False
    else:
        print("Warning: invalid tests directory not found", file=sys.stderr)

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()