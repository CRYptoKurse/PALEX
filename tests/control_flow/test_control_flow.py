import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT.parent
MAIN_SCRIPT = SRC_ROOT / "src" / "main.py"
VALID_DIR = ROOT / "control_flow" / "valid"
INVALID_DIR = ROOT / "control_flow" / "invalid"


def run_command(args):
    return subprocess.run(
        [sys.executable, str(MAIN_SCRIPT)] + args,
        capture_output=True,
        text=True,
    )


def test_valid_control_flow_compiles():
    for src_file in sorted(VALID_DIR.rglob("*.src")):
        if "short_circuit" in src_file.name:
            result = run_command(["--ir", "--ir-format", "text", "--input", str(src_file)])
            assert result.returncode == 0, f"IR compile failed:\n{result.stderr}"
            assert "JUMP_IF_NOT" in result.stdout, "Short-circuit logic should generate conditional jumps"
            assert "JUMP_IF" in result.stdout, "Short-circuit logic should use branch control flow"
        else:
            output_asm = src_file.with_suffix(".asm")
            result = run_command(["--compile", "--input", str(src_file), "--output", str(output_asm)])
            assert result.returncode == 0, f"Assembly compile failed for {src_file.name}:\n{result.stderr}"
            assert output_asm.exists(), f"Expected assembly file was not created: {output_asm}"


def test_invalid_control_flow_fails_semantic():
    for src_file in sorted(INVALID_DIR.rglob("*.src")):
        result = run_command(["--ir", "--input", str(src_file)])
        assert result.returncode != 0, f"Invalid source unexpectedly passed: {src_file.name}"
        assert result.stderr, "Expected a semantic error message"
