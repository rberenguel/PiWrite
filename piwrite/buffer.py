from typing import List, Union

from prompt_toolkit.keys import Keys

from piwrite.cursor import Cursor
from piwrite.line import Line


class Buffer:
    # TODO: move insertion to Line
    def __init__(self, lines: Union[List[Line], None] = None):
        if lines:
            self.lines = lines
        else:
            self.lines = list()

    def copy(self):
        return Buffer([line.copy() for line in self.lines])

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, key: int):
        return self.lines[key]

    def __setitem__(self, key: int, value: Line):
        self.lines[key] = value

    def __repr__(self):
        joined = "|".join([str(l) for l in self.lines])
        return f"Buffer({joined})"

    def counts(self):
        content = " ".join([str(lin) for lin in self.get()])
        content = (
            content.replace("*", " ")
            .replace("_", " ")
            .replace("#", " ")
            .replace(":", " ")
        )
        words = len(content.split(" "))
        pars = len([1 for lin in self.get() if len(str(lin).strip()) > 0])
        return words, pars, content

    def insert(self, key, cursor: Cursor):
        col: int = cursor.column

        if key == Keys.ControlM:
            current_line: int = cursor.line
            head = self.lines[current_line][0 : cursor.column]
            tail = self.lines[current_line][cursor.column :]
            # Keep indentation
            prev = str(self.lines[current_line])
            indent = len(prev) - len(prev.lstrip())
            self.lines[current_line] = Line(head)
            if len(tail) == 0 and indent > 0:
                self.lines.insert(current_line + 1, Line(" " * indent))
                cursor.to(current_line + 1, indent)
            else:
                self.lines.insert(current_line + 1, Line(tail))
                cursor.to(current_line + 1, 0)
            return

        if cursor.line + 1 > len(self.lines):
            self.lines.append(Line())
        self.lines[cursor.line].insert(col, key)
        cursor += 1

    def clip(self, cursor: Cursor):
        """Clip the cursor to the current line and buffer"""
        if cursor.line >= len(self):
            cursor.line = len(self) - 1
        if len(self) == 0:
            le = 0
        else:
            le = len(self[cursor.line])
        if cursor.column < 0:
            cursor.column = 0
        if cursor.line < 0:
            cursor.line = 0
        if le < cursor.column:
            cursor.column = le

    def delete(self, cursor: Cursor):
        col = cursor.column
        row = cursor.line
        if col == 0:
            if row == 0:
                return
            new_column = len(self.lines[row - 1])
            self.lines[row - 1] += self.lines[row]
            self.lines = self.lines[0:row] + self.lines[row + 1 :]
            cursor.line = row - 1
            cursor.column = new_column
            self.clip(cursor)
            return
        lin = self.lines[cursor.line]
        self.lines[cursor.line].delete(col)
        cursor -= 1

    def get(self):
        return self.lines
