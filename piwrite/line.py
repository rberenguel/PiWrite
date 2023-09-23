class Line:
    def __init__(self, contents=None):
        if contents:
            self.contents = contents
        else:
            self.contents = ""
        self.cursor = None

    def copy(self):
        return Line(self.contents)

    def __getitem__(self, key):
        return self.contents[key]

    def __len__(self):
        return len(self.contents)

    def __repr__(self):
        return self.contents

    def __eq__(self, other):
        if isinstance(other, Line):
            return self.contents == other.contents
        if isinstance(other, str):
            return self.contents == other

    def __iadd__(self, other):
        self.contents += other.contents
        return self

    def delete(self, column):
        s = self.contents
        self.contents = s[0 : column - 1] + s[column:]

    def insert(self, column, letter):
        s = self.contents
        if len(self.contents) == column:
            self.contents = s + letter
        else:
            # TODO: keep the breakage point and keep inserting until a change of cursor
            # Probably needs to keep track of cursor, which I haven't used yet.
            self.contents = (
                s[0:column] + letter + s[column:]
            )  # Wasteful, but ok for a PoC

    def _iw(self):
        """Handle, kind of, the inside word text object. Returns the new cursor position"""
        # This is uglily hardcoded like this
        # Note that daw is diw + deleting a space
        col = self.cursor.column
        # For now will ignore any other separators (vim handles . and others)
        lin = self.contents
        end = lin.find(" ", col)
        start = lin.rfind(" ", 0, col)
        if end == -1 and start == -1:
            return Line(""), "", 0
        if end == -1:
            return Line(lin[0 : start + 1]), lin[start + 1 :], start + 1
        if start == -1:
            return Line(lin[end:]), lin[0:end], 0
        return Line(lin[0 : start + 1] + lin[end:]), lin[start + 1 : end], start + 1

    def _aw(self):
        """Handle, kind of, the around word text object. Returns the new cursor position"""
        # This is uglily hardcoded like this
        # Note that daw is diw + deleting a space
        col = self.cursor.column
        # For now will ignore any other separators (vim handles . and others)
        lin = self.contents
        end = lin.find(" ", col)
        start = lin.rfind(" ", 0, col)
        if end == -1 and start == -1:
            print("Deletion has been empty-ish")
            return Line(""), lin, 0
        if end == -1:
            return Line(lin[0:start]), lin[start:], start + 1
        if start == -1:
            return Line(lin[end + 1 :]), lin[0 : end + 1], 0
        return Line(lin[0:start] + lin[end:]), lin[start + 1 : end + 1], start + 1
