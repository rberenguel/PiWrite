import logging
import subprocess
import sys
import time
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys

from piwrite.buffer import Buffer
from piwrite.cursor import Cursor
from piwrite.line import Line
from piwrite.markdownify import markdownify

logger = logging.getLogger("piwrite")


class Mode(Enum):
    NORMAL = "N"
    INSERT = "I"

class Editor:
    UNDO_DEPTH = 10

    def __init__(self):
        # TODO: Some could be properties
        # TODO: Some should be saved and restored on quit
        self.buffer = Buffer()
        self._history_pointer = 0
        self._history = [Buffer()]
        self._mode = Mode.NORMAL
        self.cursor = Cursor(0, 0)
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
                    start + """<span id="caret" class="ins">""" + letter + """</span>""" + end
                )
        if self._mode == Mode.NORMAL:
            if col - 1 < 0:
                start = ""
            else:
                start = lin[0 : col - 1]
            lines[self.cursor.line] = (
                start + """<span id="caret" class="normal">""" + letter + """</span>""" + end
            )
        if self.viz:
            viz = self.viz[0]
            shift = self.viz[1]
        else:
            viz = int(1100 / (2 * self.fontsize)) + 2  # _very_ rough approx
            shift = int(viz / 2)
            if self.rot == "90": # TODO: Convert these to an Enum
                viz = int(int(self.fontsize)/9)
                shift = 2
        row = self.cursor.line
        if row < viz:
            return markdownify(lines, row)
        else:
            return markdownify(lines[row - shift:], shift)

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
        # TODO: A Trie for this would work sooo much better than doing it by hand
        if command == ["i"]:
            self.clear_command()
            self._mode = Mode.INSERT
            self.cursor -= 1  # Seems to be giving problems!?
            self.buffer.clip(self.cursor)
            return
        if command[-1] == Keys.Escape:
            # TODO: this has no test
            self.clear_command()
            return
        if command[-1] == Keys.ControlH:
            self._command = self._command[0:-2]
            self.completions = None
            self.completions_markdownified = None  # TODO: wrap these two in a function
            return
        if command[-1] in self.GENERIC_MOVEMENT:
            self.status = "I didn't bother implementing arrows or C-a/C-e here, sorry"
            self._command.pop()
            return
        if command == ["d"] or command == ["d", "a"] or command == ["d", "i"]:
            return
        if command == ["c"] or command == ["c", "a"] or command == ["c", "i"]:
            return
        # TODO: the commands below need tests
        if command == ["a"]:
            self.clear_command()
            self._mode = Mode.INSERT
            return
        if command == ["I"]:
            self.clear_command()
            self._mode = Mode.INSERT
            self.cursor.to(column=0, line=self.cursor.line)
            return
        if command == ["A"]:
            self.clear_command()
            self._mode = Mode.INSERT
            lin = self.cursor.line
            end = len(self.buffer[lin])
            self.cursor.to(column=end, line=lin)
            return

        if command == ["o"]:
            self.clear_command()
            self._mode = Mode.INSERT
            lin = self.cursor.line
            self.buffer.lines.insert(lin + 1, Line())
            self.cursor.to(column=0, line=lin + 1)
            return

        if command == ["u"]:
            # Undo-ish
            self.clear_command()
            self._history_pointer -= 1
            if self._history_pointer < 0:
                logger.info("No further undo")
                self.status = "No further undo information"
                self._history_pointer = 0
            logger.debug(f"Undoing at {self._history_pointer}")
            self.buffer = self._history[self._history_pointer].copy()
            logger.debug(f"Buffer now: {self.buffer}")
            self.buffer.clip(self.cursor)
            return

        if command == [Keys.ControlR]:
            # Redo-ish
            self.clear_command()
            self._history_pointer += 1  # We need to jump "pressed escape" and "current"
            if self._history_pointer >= len(self._history):
                self.status = "No further redo information"
                self._history_pointer = len(self._history) - 1
            self.buffer = self._history[self._history_pointer].copy()
            self.buffer.clip(self.cursor)
            return

        if command == ["p"]:
            self.clear_command()
            paste = ["a"] + self.yank + [Keys.Escape]
            self.send(paste)
            return

        if command == ["P"]:
            self.clear_command()
            paste = ["i"] + self.yank + [Keys.Escape]
            self.send(paste)
            return

        if command == ["c", "a", "w"]:
            self.clear_command()
            self.send(["dawa"])
        if command == ["c", "i", "w"]:
            self.clear_command()
            self.send(["diwa"])
        if command == ["d", "d"]:
            self.clear_command()
            lin = self.cursor.line
            self.yank = [self.buffer.lines[lin], Keys.ControlM]
            del self.buffer.lines[lin]
            if len(self.buffer) == 0:
                self.buffer = Buffer()
            self.buffer.clip(self.cursor)
            return
        # TODO: clear repetition between daw and diw
        if command == ["d", "a", "w"]:
            self.clear_command()
            row = self.cursor.line
            line = self.buffer[row]
            line.cursor = self.cursor  # This is somewhat ugly
            new_line, word, col = line._aw()
            self.yank = [word]
            self.buffer[self.cursor.line] = new_line
            self.cursor.column = col
            self.buffer.clip(self.cursor)
            return

        if command == ["d", "i", "w"]:
            self.clear_command()
            row = self.cursor.line
            line = self.buffer[row]
            line.cursor = self.cursor  # This is somewhat ugly
            new_line, word, col = line._iw()
            self.yank = [word]
            self.buffer[self.cursor.line] = new_line
            self.cursor.column = col
            self.buffer.clip(self.cursor)
            return

        if command[0] == "q" and self.previous_file is not None:
            cmd = [":E ", self.previous_file[0], Keys.ControlM]
            self.clear_command()
            self.send(cmd)
            self.dot = "nope"
            self.filename = self.previous_file[1]
            Path(self.previous_file[0]).unlink()
            self.previous_file = None

        if command[0] == ":" and (
            command[-1] != Keys.ControlM and command[-1] != Keys.ControlI
        ):
            logger.debug("Ignoring because no tab, no return")
            self.completions = None
            self.completions_markdownified = None  # TODO: wrap these two in a function
            return
        if command == [":", "q", Keys.ControlM]:
            self.clear_command()
            if self.saved:
                self.status = "Shutting down"
                time.sleep(1) # I want this real blocking here
                subprocess.call(["shutdown", "-h", "now"])
            else:
                self.status = "You have unsaved changes"
        if command == [":", "q", "!", Keys.ControlM]:
            self.saved = True
            self.clear_command()
            self.send([":q", Keys.ControlM])
            return
        if command == [":", "h", Keys.ControlM]:
            self.clear_command()
            _, tmpname = tempfile.mkstemp()
            resolved = str(Path(tmpname).resolve())
            self.previous_file = (
                resolved,
                self.filename,
            )  # Keep track of the previous "real" file (if any)
            cmd = [":W ", resolved, Keys.ControlM]
            self.send(cmd)
            this_path = Path(__file__).resolve()
            root_dir = this_path.parent
            help = root_dir / "help"
            cmd = [":E ", str(help), Keys.ControlM]
            self.send(cmd)
            return

        if command == [":", "d", "o", "t", Keys.ControlM]:
            # Render graphviz
            self.clear_command()
            _, tmpname = tempfile.mkstemp()
            resolved = str(Path(tmpname).resolve())
            self.previous_file = (
                resolved,
                self.filename,
            )  # Keep track of the previous "real" file (if any)
            cmd = [":W ", resolved, Keys.ControlM]
            self.send(cmd)
            img_resolved = str((self.docs / Path("imgs") / Path("graph")).resolve()) + ".png"
            subprocess.call(["dot", "-Tpng", resolved, "-o", img_resolved])
            self.status = img_resolved
            self.dot = "/docs/imgs/graph.png"
            return

        if command[0:2] == [":", "w"] and command[-1] == Keys.ControlM:
            # Write file
            filename = "".join(command[3:-1])
            if filename.strip() == "":
                filename = self.filename
            try:
                (self.docs / filename).write_text(
                    "\n".join([str(lin) for lin in self.buffer.get()])
                )
                self.filename = filename
                self.saved = True
                self.status = f"Saved as {filename}"
            except Exception as e:
                self.err = str(e)
            self.clear_command()
            return
        if command[0:2] == [":", "W"] and command[-1] == Keys.ControlM:
            # This should be protected like E
            filename = "".join(command[3:-1])
            try:
                Path(filename).write_text(
                    "\n".join([str(lin) for lin in self.buffer.get()])
                )
                self.filename = filename
                self.saved = True
                self.status = f"Special saved as {filename}"
            except Exception as e:
                self.err = str(e)
            self.clear_command()
            return
        if "".join(command[0:4]) == ":rot" and command[-1] == Keys.ControlM:
            if self.rot == "0":
                self.rot = "90"
            else:
                self.rot = "0"
            self.clear_command()
            return
        if "".join(command[0:5]) == ":mono" and command[-1] == Keys.ControlM:
            self.font = "mono"
            self.clear_command()
            return
        if "".join(command[0:5]) == ":sans" and command[-1] == Keys.ControlM:
            self.font = "sans"
            self.clear_command()
            return
        if "".join(command[0:6]) == ":serif" and command[-1] == Keys.ControlM:
            self.font = "serif"
            self.clear_command()
            return
        if "".join(command[0:6]) == ":latex" and command[-1] == Keys.ControlM:
            self.font = "latex"
            self.clear_command()
            return
        if "".join(command[0:9]) == ":fontsize" and command[-1] == Keys.ControlM:
            self.fontsize = int("".join(command[10:-1]).strip())
            self.status = f"Set font size to {self.fontsize}"
            self.clear_command()
            return
        if "".join(command[0:3]) == ":fs" and command[-1] == Keys.ControlM:
            self.fontsize = int("".join(command[4:-1]).strip())
            self.status = f"Set font size to {self.fontsize}"
            self.clear_command()
            return
        if (command[0:2] == [":", "e"] or command[0:3] == [":", "e", "!"]) and command[
            -1
        ] == Keys.ControlI:
            command.pop()  # Drop the tab
            if self.completions is None:
                filename = "".join(command).replace(":e!", "").replace(":e", "").strip()
                logger.debug(f"Globbing on {filename}")
                files = [str(f.name) for f in self.docs.glob(filename + "*")]
                if len(files) == 0:
                    self.completions = None
                else:
                    self.completions = {"files": files, "idx": -1}
            else:
                self.completions["idx"] = (self.completions["idx"] + 1) % len(
                    self.completions["files"]
                )
                # TODO: In addition to this, deleting or writing will need to clear completions, reset index…
                md = []
                for i, completion in enumerate(self.completions["files"]):
                    if i == self.completions["idx"]:
                        md.append(f"::{completion}::")
                    else:
                        md.append(completion)
                self.completions_markdownified = markdownify([" ".join(md)])
            return
        if command[0:4] == [":", "v", "i", "z"] and command[-1] == Keys.ControlM:
            try:
                viz_val = "".join(command[4:-1]).strip()
                if len(viz_val) == 0:
                    self.status = "Clearing custom viz"
                    self.viz = None
                else:
                    viz, shift = viz_val.split(":")
                    viz = int(viz)
                    shift = int(shift)
                    self.viz = (viz, shift)
            except Exception as e:
                self.status = f"viz has to be of the form int:int or empty ({e})"
            finally:
                self.clear_command()
            self.status = f"Setting shift to {self.viz}"
            return
        if command[0:3] == [":", "e", "!"] and command[-1] == Keys.ControlM:
            self.status = ""
            self.saved = True
            if self.completions is None:
                filename = "".join(command[4:-1])
            else:
                filename = self.completions["files"][self.completions["idx"]]
            self.clear_command()
            self.send([":e ", filename, Keys.ControlM])
            return
        if command[0:2] == [":", "e"] and command[-1] == Keys.ControlM:
            if not self.saved:
                self.status = "You have unsaved changes"
                return
            if self.completions is None:
                filename = "".join(command[3:-1])
            else:
                filename = self.completions["files"][self.completions["idx"]]
            try:
                text = (self.docs / filename).read_text()
                lines = text.split("\n")
                self.buffer = Buffer([Line(line) for line in lines])
                self.filename = filename
                self.saved = True
                self.status = f"Loaded {self.filename}"
            except Exception as e:
                self.err = str(e)
            self.cursor.to(0, 0)
            self.clear_command()
            if self.filename.endswith(".dot"):
                self.send([":mono", Keys.ControlM])
            return
        if command[0:2] == [":", "E"] and command[-1] == Keys.ControlM:
            if self.completions is None:
                filename = "".join(command[3:-1])
            else:
                filename = self.completions["files"][self.completions["idx"]]
            try:
                logger.debug(f"Opening {filename}")
                text = Path(filename).read_text()
                lines = text.split("\n")
                self.buffer = Buffer([Line(line) for line in lines])
                self.filename = Path(filename).name
                self.saved = True
                self.status = f"Loaded {self.filename}"
            except Exception as e:
                self.err = str(e)
            self.clear_command()
            self.cursor.to(0, 0)
            return
        self.clear_command()
