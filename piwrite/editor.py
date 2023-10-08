import logging
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys

from piwrite.dispatcher import Dispatcher
from piwrite.markdownify import markdownify
from piwrite.mode import Mode

logger = logging.getLogger("piwrite")


class Editor:
    UNDO_DEPTH = 10

    def __init__(self):
        # TODO: Some could be properties
        # TODO: Some should be saved and restored on quit
        self.refresh = False
        self._history_pointer = 0
        self._mode = Mode.NORMAL
        self._command = []
        self.yank = [""]
        self.viz = None
        self.setup_movement()
        self.rot = "0"
        self.dot = "nope"
        self.filename = "unnamed"
        self.previous_file = None
        self.saved = False
        self.status = None
        self.completions = None
        self.completions_markdownified = None
        self.font = "serif"
        self.fontsize = 50
        self.err = None
        home = Path.home()
        self.docs = home / "piwrite-docs/"
        self.docs.mkdir(exist_ok=True)
        (self.docs / Path("imgs")).mkdir(exist_ok=True)
        self.dispatcher = Dispatcher(editor=self)

    def send(self, arr):
        """Send an array containing strings and keys to be parsed"""
        logger.info(f"Command being sent: {arr}")
        for thing in arr:
            if isinstance(thing, Enum):
                self.dispatch(KeyPress(thing))
            else:
                for let in thing:
                    self.dispatch(KeyPress(let))

    def mode(self):
        return str(self._mode)

    def get(self):
        # TODO: needs a test
        lines = [str(lin) for lin in self.buffer.get()]  # "cheap" copy
        if self.cursor.line + 1 > len(lines):
            lin = ""
            lines.append(lin)
        lin = lines[self.cursor.line]
        col = self.cursor.column
        # if col == 0:
        #    col = 1
        if len(lin) > col:
            end = lin[col:]
        else:
            end = ""
        if col <= 0:
            letter = " "
        else:
            letter = lin[col - 1]
        if self._mode == Mode.INSERT:
            if False:  # col == 1:
                lines[self.cursor.line] = (
                    """<span id="ins0">""" + letter + """</span>""" + end
                )
            else:
                if col - 1 < 0:
                    start = ""
                else:
                    start = lin[0 : col - 1]
                lines[self.cursor.line] = (
                    start
                    + """<span id="caret" class="ins">"""
                    + letter
                    + """</span>"""
                    + end
                )
        if self._mode == Mode.NORMAL:
            if col - 1 < 0:
                start = ""
            else:
                start = lin[0 : col - 1]
            lines[self.cursor.line] = (
                start
                + """<span id="caret" class="normal">"""
                + letter
                + """</span>"""
                + end
            )
        if self.viz:
            viz = self.viz[0]
            shift = self.viz[1]
        else:
            viz = int(1100 / (2 * self.fontsize)) + 2  # _very_ rough approx
            shift = int(viz / 2)
            if self.rot == "90":  # TODO: Convert these to an Enum
                viz = int(int(self.fontsize) / 9)
                shift = 2
        row = self.cursor.line
        if row < viz:
            return markdownify(lines, row)
        else:
            return markdownify(lines[row - shift :], shift)

    def setup_movement(self):
        def up():
            self.cursor ^= -1
            self.buffer.clip(self.cursor)
            return

        def down():
            self.cursor ^= +1
            self.buffer.clip(self.cursor)
            return

        def right():
            self.cursor += 1
            self.buffer.clip(self.cursor)
            return

        def left():
            self.cursor -= 1
            self.buffer.clip(self.cursor)
            return

        self.GENERIC_MOVEMENT = {
            Keys.ControlA: lambda: self.cursor.to(line=self.cursor.line, column=0),
            Keys.ControlE: lambda: self.cursor.to(
                line=self.cursor.line, column=len(self.buffer.get()[self.cursor.line])
            ),
            Keys.Up: up,
            Keys.Down: down,
            Keys.Left: left,
            Keys.Right: right,
        }

    def dispatch(self, _key):
        if _key is None:
            return
        key = _key.key
        if key == Keys.ControlC:
            sys.exit(0)

        if key in self.GENERIC_MOVEMENT:
            self.GENERIC_MOVEMENT[key]()
            return

        if key == Keys.ControlQ:
            self.refresh = True
            return

        if self._mode == Mode.INSERT:
            if key == Keys.Escape:
                self._mode = Mode.NORMAL
                self.cursor -= 1  # This seems to be the vim behaviour
                self.buffer.clip(self.cursor)
                logger.debug(
                    f"History before: {self._history}, {self._history_pointer}"
                )
                # TODO: All this needs better testing, and it may get tricky
                if self._history_pointer + 1 >= len(self._history):
                    logger.debug("Adding at the end")
                    self._history.append(self.buffer.copy())
                else:
                    self._history[self._history_pointer + 1] = self.buffer.copy()
                self._history_pointer += 1
                self._history_pointer = min(self._history_pointer, self.UNDO_DEPTH - 1)
                logger.debug(f"Clipping pointer at {self._history_pointer}")
                if len(self._history) > self.UNDO_DEPTH:
                    self._history = self._history[-self.UNDO_DEPTH :]
                    assert len(self._history) == self.UNDO_DEPTH
                logger.debug(f"History after: {self._history}, {self._history_pointer}")
                return
            self.saved = False
            if key == Keys.Delete or key == Keys.ControlH:
                self.buffer.delete(self.cursor)
                return
            self.buffer.insert(key, self.cursor)

        if self._mode == Mode.NORMAL:
            self._command.append(key)
            self.dispatch_command(self._command)
        return

    def clear_command(self):
        self.completions = None
        self.completions_markdownified = None
        self.status = "&nbsp;"
        self._command = []

    def command(self):
        filt = [str(l) for l in self._command if len(str(l)) == 1]
        return "".join(filt)

    def dispatch_command(self, command):
        self.dispatcher.dispatch_command(command)
