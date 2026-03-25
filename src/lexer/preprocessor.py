from typing import List, Tuple, Dict, Set

class Preprocessor:
    """Удаляет комментарии и обрабатывает директивы препроцессора:
       #define, #undef, #ifdef, #ifndef, #endif.
       Сохраняет нумерацию строк для сообщений об ошибках.
    """
    def __init__(self, source: str):
        self.source = source
        self.errors: List[Tuple[int, int, str]] = []  # (line, col, message)
        self._macros: Dict[str, str] = {}             # внешние макросы (задаются через define)

    def define(self, name: str, value: str = "") -> None:
        """Добавляет или переопределяет макрос."""
        self._macros[name] = value

    def undefine(self, name: str) -> None:
        """Удаляет макрос, если он существует."""
        self._macros.pop(name, None)

    def process(self) -> str:
        # Шаг 1: удаление комментариев (существующая логика)
        no_comments = self._remove_comments()

        # Шаг 2: обработка директив препроцессора и условной компиляции
        # Результат этого шага: текст без директив, таблица макросов (копия внешних + определённые в коде)
        macros = self._macros.copy()          # копируем внешние макросы
        lines = no_comments.splitlines(True)  # сохраняем переводы строк
        processed_lines = []
        cond_stack: List[bool] = []           # стек состояний: True если условие на этом уровне истинно
        line_number = 1

        i = 0
        while i < len(lines):
            raw_line = lines[i]
            line = raw_line.rstrip('\n\r')    # убираем концевые переводы для анализа
            eol = raw_line[len(line):]        # сохраняем символ(ы) конца строки

            # Определяем, активна ли текущая строка (не в пропущенном блоке)
            active = all(cond_stack) if cond_stack else True

            # Проверяем, является ли строка директивой препроцессора (после обрезания пробелов начинается с '#')
            stripped = line.lstrip()
            if stripped.startswith('#'):
                # разбираем директиву
                directive_line = stripped[1:].lstrip()  # убираем '#' и пробелы после него
                # извлекаем первую лексему (имя директивы)
                parts = directive_line.split(None, 1)
                if not parts:
                    self._add_error(line_number, 1, "Empty preprocessor directive")
                    # заменяем всю строку пробелами
                    processed_lines.append(' ' * len(line) + eol)
                else:
                    cmd = parts[0]
                    rest = parts[1] if len(parts) > 1 else ""

                    # Обрабатываем директиву в зависимости от активности
                    if cmd == 'define':
                        if active:
                            # разбираем "имя значение"
                            subparts = rest.split(None, 1)
                            if not subparts:
                                self._add_error(line_number, 1, "#define missing macro name")
                            else:
                                name = subparts[0]
                                value = subparts[1] if len(subparts) > 1 else ""
                                macros[name] = value
                        # заменяем строку пробелами
                        processed_lines.append(' ' * len(line) + eol)

                    elif cmd == 'undef':
                        if active:
                            name = rest.split(None, 1)[0] if rest else ""
                            if not name:
                                self._add_error(line_number, 1, "#undef missing macro name")
                            else:
                                macros.pop(name, None)
                        processed_lines.append(' ' * len(line) + eol)

                    elif cmd == 'ifdef':
                        name = rest.split(None, 1)[0] if rest else ""
                        if not name:
                            self._add_error(line_number, 1, "#ifdef missing macro name")
                        if active:
                            cond = name in macros
                        else:
                            cond = False
                        cond_stack.append(cond)
                        processed_lines.append(' ' * len(line) + eol)

                    elif cmd == 'ifndef':
                        name = rest.split(None, 1)[0] if rest else ""
                        if not name:
                            self._add_error(line_number, 1, "#ifndef missing macro name")
                        if active:
                            cond = name not in macros
                        else:
                            cond = False
                        cond_stack.append(cond)
                        processed_lines.append(' ' * len(line) + eol)

                    elif cmd == 'endif':
                        if not cond_stack:
                            self._add_error(line_number, 1, "Unmatched #endif")
                        else:
                            cond_stack.pop()
                        processed_lines.append(' ' * len(line) + eol)

                    else:
                        self._add_error(line_number, 1, f"Unknown preprocessor directive '{cmd}'")
                        processed_lines.append(' ' * len(line) + eol)
            else:
                # Не директива: если активны, оставляем строку как есть, иначе заменяем пробелами
                if active:
                    processed_lines.append(raw_line)
                else:
                    processed_lines.append(' ' * len(line) + eol)

            line_number += 1
            i += 1

        # Проверка незакрытых условных блоков
        if cond_stack:
            self._add_error(line_number-1, 1, "Unclosed #ifdef/#ifndef block(s)")

        # Склеиваем результат после обработки директив
        after_directives = ''.join(processed_lines)

        # Шаг 3: подстановка макросов (с сохранением строковых литералов)
        expanded = self._expand_macros(after_directives, macros)

        return expanded

    # ------------------------------------------------------------------
    # Внутренние вспомогательные методы
    # ------------------------------------------------------------------

    def _add_error(self, line: int, col: int, msg: str) -> None:
        self.errors.append((line, col, msg))

    def _remove_comments(self) -> str:
        """Удаляет комментарии, заменяя их пробелами (существующая логика с небольшими правками)."""
        result = []
        i = 0
        length = len(self.source)
        line = 1
        col = 1
        in_string = False
        in_line_comment = False
        in_block_comment = False

        while i < length:
            ch = self.source[i]

            if in_string:
                result.append(ch)
                if ch == '"' and (i == 0 or self.source[i-1] != '\\'):
                    in_string = False
                i += 1
                col += 1
            elif in_block_comment:
                if ch == '*' and i+1 < length and self.source[i+1] == '/':
                    result.append(' ')
                    result.append(' ')
                    i += 2
                    col += 2
                    in_block_comment = False
                else:
                    if ch == '\n':
                        result.append(ch)
                        line += 1
                        col = 1
                    elif ch == '\r':
                        result.append(ch)
                        line += 1
                        col = 1
                        if i+1 < length and self.source[i+1] == '\n':
                            i += 1
                            result.append(self.source[i])
                    else:
                        result.append(' ')
                        col += 1
                    i += 1
            elif in_line_comment:
                if ch == '\n':
                    result.append(ch)
                    line += 1
                    col = 1
                    in_line_comment = False
                elif ch == '\r':
                    result.append(ch)
                    line += 1
                    col = 1
                    if i+1 < length and self.source[i+1] == '\n':
                        i += 1
                        result.append(self.source[i])
                    in_line_comment = False
                else:
                    result.append(' ')
                    col += 1
                i += 1
            else:
                if ch == '"':
                    in_string = True
                    result.append(ch)
                    i += 1
                    col += 1
                elif ch == '/' and i+1 < length and self.source[i+1] == '/':
                    result.append(' ')
                    result.append(' ')
                    i += 2
                    col += 2
                    in_line_comment = True
                elif ch == '/' and i+1 < length and self.source[i+1] == '*':
                    result.append(' ')
                    result.append(' ')
                    i += 2
                    col += 2
                    in_block_comment = True
                else:
                    result.append(ch)
                    if ch == '\n':
                        line += 1
                        col = 1
                    elif ch == '\r':
                        line += 1
                        col = 1
                        if i+1 < length and self.source[i+1] == '\n':
                            i += 1
                            result.append(self.source[i])
                    else:
                        col += 1
                    i += 1

        if in_string:
            self._add_error(line, col, "Unterminated string")
        if in_block_comment:
            self._add_error(line, col, "Unterminated block comment")

        return ''.join(result)

    def _expand_macros(self, text: str, macros: Dict[str, str]) -> str:
        """Заменяет идентификаторы-макросы на их значения, избегая рекурсии.
           Учитывает строковые литералы (внутри них замена не производится).
        """
        result = []
        i = 0
        length = len(text)
        in_string = False

        while i < length:
            ch = text[i]

            if in_string:
                result.append(ch)
                if ch == '"' and (i == 0 or text[i-1] != '\\'):
                    in_string = False
                i += 1
            else:
                if ch == '"':
                    in_string = True
                    result.append(ch)
                    i += 1
                elif ch.isalpha() or ch == '_':
                    # начало идентификатора
                    start = i
                    while i < length and (text[i].isalnum() or text[i] == '_'):
                        i += 1
                    ident = text[start:i]
                    # проверяем, является ли идентификатор макросом
                    if ident in macros:
                        # рекурсивно раскрываем значение, защищаясь от циклов
                        expanded = self._expand_once(ident, macros, set())
                        result.append(expanded)
                    else:
                        result.append(ident)
                else:
                    result.append(ch)
                    i += 1

        return ''.join(result)

    def _expand_once(self, name: str, macros: Dict[str, str], expanding: Set[str]) -> str:
        """Раскрывает макрос name, предотвращая рекурсию."""
        if name in expanding:
            # рекурсия – оставляем как есть (можно добавить ошибку при желании)
            return name
        value = macros.get(name, "")
        if not value:
            return ""
        # раскрываем значение рекурсивно
        new_expanding = expanding | {name}
        return self._expand_macros_in_value(value, macros, new_expanding)

    def _expand_macros_in_value(self, text: str, macros: Dict[str, str], expanding: Set[str]) -> str:
        """Вспомогательная функция для раскрытия макросов внутри значения."""
        result = []
        i = 0
        length = len(text)
        while i < length:
            ch = text[i]
            if ch.isalpha() or ch == '_':
                start = i
                while i < length and (text[i].isalnum() or text[i] == '_'):
                    i += 1
                ident = text[start:i]
                if ident in macros and ident not in expanding:
                    expanded = self._expand_once(ident, macros, expanding)
                    result.append(expanded)
                else:
                    result.append(ident)
            else:
                result.append(ch)
                i += 1
        return ''.join(result)