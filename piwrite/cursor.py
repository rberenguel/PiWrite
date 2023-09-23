from dataclasses import dataclass


@dataclass
class Cursor:
    line: int = 0
    column: int = 0

    def to(self, line=0, column=0):
        self.line = line
        self.column = column
        # The hidden column is used for clipping: when moving up
        # shorter/longer lines we should try to keep the longest
        self._column = column

    def __ixor__(self, inc: int):
        """Change column, because ^ looks like moving up/down"""
        self.line += inc
        return self

    def __iadd__(self, inc: int):
        """Change position, because += seems natural for columns"""
        self.column += inc
        return self

    def __isub__(self, inc: int):
        self.column -= inc
        return self
