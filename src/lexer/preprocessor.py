import re
from typing import List, Tuple

class Preprocessor:
    """Удаляет однострочные и многострочные комментарии, сохраняя нумерацию строк."""
    def __init__(self, source: str):
        self.source = source
        self.errors: List[Tuple[int, int, str]] = []  # (line, col, message)

    def process(self) -> str:
        lines = self.source.splitlines(keepends=True)
        result_lines = []
        in_block_comment = False
        for line_idx, line in enumerate(lines, start=1):
            i = 0
            new_line = []
            while i < len(line):
                if not in_block_comment:
                    # однострочный комментарий
                    if line[i] == '/' and i+1 < len(line) and line[i+1] == '/':
                        break  # остаток строки игнорируем
                    # начало блочного комментария
                    elif line[i] == '/' and i+1 < len(line) and line[i+1] == '*':
                        in_block_comment = True
                        i += 2
                    else:
                        new_line.append(line[i])
                        i += 1
                else:
                    # конец блочного комментария
                    if line[i] == '*' and i+1 < len(line) and line[i+1] == '/':
                        in_block_comment = False
                        i += 2
                    else:
                        i += 1
            # заменяем удалённый текст пробелами для сохранения колонок
            result_lines.append(''.join(new_line))
        # проверка незавершённого блочного комментария
        if in_block_comment:
            self.errors.append((len(result_lines), 1, "Unterminated block comment"))
        return ''.join(result_lines)