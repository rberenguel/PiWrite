import logging
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from prompt_toolkit.keys import Keys
from proselint import config as proselint_config
from proselint import tools as proselint_tools
from readability import Readability

from piwrite.buffer import Buffer
from piwrite.cursor import Cursor
from piwrite.line import Line
from piwrite.markdownify import markdownify
from piwrite.mode import Mode

logger = logging.getLogger("piwrite")


class Dispatcher:
    def __init__(self, editor=None):
        self.editor = editor
        self.editor._history = [Buffer()]
        self.editor.buffer = Buffer(lines=None)
        self.editor.cursor = Cursor(0, 0)

    def dispatch_command(self, command):
        # TODO: A Trie for this would work sooo much better than doing it by hand
        logger.info("Dispatching %s", str(command))
        if command == ["i"]:
            self.editor.clear_command()
            self.editor._mode = Mode.INSERT
            self.editor.updating_fields["mode"] = True
            self.editor.cursor -= 1  # Seems to be giving problems!?
            self.editor.buffer.clip(self.editor.cursor)
            return
        if command[-1] == Keys.Escape:
            # TODO: this has no test
            self.editor.clear_command()
            return
        if command == ["v"]:
            lines = [str(lin) for lin in self.editor.buffer.get()]
            self.editor.visual = markdownify(lines, visible=False)
            self.editor.updating_fields["visual"] = True
            return
        if command[-1] == Keys.ControlH:
            self.editor._command = self.editor._command[0:-2]
            self.editor.completions = None
            self.editor.completions_markdownified = (
                None  # TODO: wrap these two in a function
            )
            self.editor.updating_fields["command"] = True
            self.editor.updating_fields["completions"] = True
            return
        if command[-1] in self.editor.GENERIC_MOVEMENT:
            self.editor.status = (
                "I didn't bother implementing arrows or C-a/C-e here, sorry"
            )
            self.editor.updating_fields["status"] = True
            self.editor._command.pop()
            self.editor.updating_fields["command"] = True
            return
        if command == ["d"] or command == ["d", "a"] or command == ["d", "i"]:
            return
        if command == ["c"] or command == ["c", "a"] or command == ["c", "i"]:
            return
        # TODO: the commands below need tests
        if command == ["a"]:
            self.editor.clear_command()
            self.editor._mode = Mode.INSERT
            self.editor.updating_fields["mode"] = True
            return
        if command == ["I"]:
            self.editor.clear_command()
            self.editor._mode = Mode.INSERT
            self.editor.updating_fields["mode"] = True
            self.editor.cursor.to(column=0, line=self.editor.cursor.line)
            return
        if command == ["A"]:
            self.editor.clear_command()
            self.editor._mode = Mode.INSERT
            self.editor.updating_fields["mode"] = True
            lin = self.editor.cursor.line
            end = len(self.editor.buffer[lin])
            self.editor.cursor.to(column=end, line=lin)
            return

        if command == ["o"]:
            self.editor.clear_command()
            self.editor._mode = Mode.INSERT
            self.editor.updating_fields["mode"] = True
            lin = self.editor.cursor.line
            self.editor.buffer.lines.insert(lin + 1, Line())
            self.editor.cursor.to(column=0, line=lin + 1)
            return

        if command == ["u"]:
            # Undo-ish
            self.editor.clear_command()
            self.editor._history_pointer -= 1
            if self.editor._history_pointer < 0:
                logger.info("No further undo")
                self.editor.status = "No further undo information"
                self.editor.updating_fields["status"] = True
                self.editor._history_pointer = 0
            logger.debug("Undoing at %s", self.editor._history_pointer)
            self.editor.buffer = self.editor._history[
                self.editor._history_pointer
            ].copy()
            logger.debug("Buffer now: %s", self.editor.buffer)
            self.editor.buffer.clip(self.editor.cursor)
            return
        if command == [Keys.ControlS]:
            self.editor.clear_command()
            words, pars, _ = self.editor.buffer.counts()
            self.editor.status = f"{words} words, {pars} paragraphs"
            self.editor.updating_fields["status"] = True
            return

        if command == [Keys.ControlR]:
            # Redo-ish
            self.editor.clear_command()
            self.editor._history_pointer += (
                1  # We need to jump "pressed escape" and "current"
            )
            if self.editor._history_pointer >= len(self.editor._history):
                self.editor.status = "No further redo information"
                self.editor._history_pointer = len(self.editor._history) - 1
            self.editor.buffer = self.editor._history[
                self.editor._history_pointer
            ].copy()
            self.editor.buffer.clip(self.editor.cursor)
            return

        if command == ["g"]:
            return

        if command == ["g", "g"]:
            self.editor.clear_command()
            self.editor.cursor.to(0, 0)
            return

        if command == ["G"]:
            self.editor.clear_command()
            self.editor.cursor.to(len(self.editor.buffer.lines) - 1, 0)
            return

        if command == ["p"]:
            self.editor.clear_command()
            paste = ["a"] + self.editor.yank + [Keys.Escape]
            self.editor.send(paste)
            return

        if command == ["P"]:
            self.editor.clear_command()
            paste = ["i"] + self.editor.yank + [Keys.Escape]
            self.editor.send(paste)
            return

        if command == ["c", "a", "w"]:
            self.editor.clear_command()
            self.editor.send(["dawa"])
        if command == ["c", "i", "w"]:
            self.editor.clear_command()
            self.editor.send(["diwa"])
        if command == ["d", "d"]:
            self.editor.clear_command()
            lin = self.editor.cursor.line
            self.editor.yank = [self.editor.buffer.lines[lin], Keys.ControlM]
            del self.editor.buffer.lines[lin]
            if len(self.editor.buffer) == 0:
                self.editor.buffer = Buffer()
            self.editor.buffer.clip(self.editor.cursor)
            return
        # TODO: clear repetition between daw and diw
        if command == ["d", "a", "w"]:
            self.editor.clear_command()
            row = self.editor.cursor.line
            line = self.editor.buffer[row]
            line.cursor = self.editor.cursor  # This is somewhat ugly
            new_line, word, col = line._aw()
            self.editor.yank = [word]
            self.editor.buffer[self.editor.cursor.line] = new_line
            self.editor.cursor.column = col
            self.editor.buffer.clip(self.editor.cursor)
            return

        if command == ["d", "i", "w"]:
            self.editor.clear_command()
            row = self.editor.cursor.line
            line = self.editor.buffer[row]
            line.cursor = self.editor.cursor  # This is somewhat ugly
            new_line, word, col = line._iw()
            self.editor.yank = [word]
            self.editor.buffer[self.editor.cursor.line] = new_line
            self.editor.cursor.column = col
            self.editor.buffer.clip(self.editor.cursor)
            return
        if command == ["d", "$"]:
            self.editor.clear_command()
            row = self.editor.cursor.line
            col = self.editor.cursor.column
            line = self.editor.buffer[row]
            line.cursor = self.editor.cursor
            cut = line[col:]
            self.editor.buffer[row] = Line(line[:col])
            self.editor.yank = [cut]
            self.editor.buffer.clip(self.editor.cursor)
            return
        if command == ["c", "$"]:
            self.editor.clear_command()
            self.editor.send("d$a")
            return
        if command[0] == "q" and self.editor.previous_file is not None:
            cmd = [":E ", self.editor.previous_file[0], Keys.ControlM]
            self.editor.clear_command()
            self.editor.send(cmd)
            self.editor.dot = "nope"
            self.editor.updating_fields["dot"] = True
            self.editor.filename = self.editor.previous_file[1]
            self.editor.updating_fields["filename"] = True
            Path(self.editor.previous_file[0]).unlink()
            self.editor.previous_file = None

        if command[0] == ":" and (
            command[-1] != Keys.ControlM and command[-1] != Keys.ControlI
        ):
            logger.debug("Ignoring because no tab, no return")
            self.editor.completions = None
            self.editor.completions_markdownified = (
                None  # TODO: wrap these two in a function
            )
            return
        if command == [":", "k", "e", "y", "s", Keys.ControlM]:
            self.editor.clear_command()
            self.editor.log_keys = True
            self.editor.status = "Logging keys to buffer"
            self.editor.updating_fields["status"] = True
            return
        if command == [":", "s", "t", "a", "t", "s", Keys.ControlM]:
            self.editor.clear_command()
            words, pars, content = self.editor.buffer.counts()
            r = Readability(content)
            fc_line = ""
            f_line = ""
            w_line = f"<b>Stats and readability</b><br/>&nbsp; word count: {words}<br/>&nbsp; paragraphs: {pars}"
            try:
                fc = r.flesch_kincaid()
                f = r.flesch()
                fc_line = f"<b>Flesch-Kincaid</b><br/>&nbsp; score: {fc.score:.2f}<br/>&nbsp; grade: {fc.grade_level} (1-18)"
                f_line = f"<b>Flesch ease</b><br/>&nbsp; ease: {f.ease} ({f.score:.2f})"
            except Exception as e:
                f_line = f"Readability failure: {e}"
            finally:
                modal = "<br/>".join([w_line, fc_line, f_line])
                self.editor.modal = modal
                self.editor.updating_fields["modal"] = True
            return

        if command == [":", "l", "i", "n", "t", Keys.ControlM]:
            self.editor.clear_command()
            _, tmpname = tempfile.mkstemp()
            resolved = Path(tmpname).resolve()
            previous_file = self.editor.filename
            previous_save_status = self.editor.saved
            cmd = [":W ", str(resolved), Keys.ControlM]
            self.editor.send(cmd)
            text = resolved.read_text()
            text = (
                text.replace("*", " ")
                .replace("_", " ")
                .replace("#", " ")
                .replace(":", " ")
            )
            p_suggestions = proselint_tools.lint(text, config=proselint_config.default)
            suggestions = [f"At {sug[2]}:{sug[3]}: {sug[1]}" for sug in p_suggestions]
            if len(suggestions) == 0:
                self.editor.modal = "No suggestions: As good as <i>The Great Gatsby</i>"
            else:
                self.editor.modal = "<br>".join(suggestions)
            self.editor.filename = previous_file
            self.editor.saved = previous_save_status
            self.editor.updating_fields["modal"] = True
            self.editor.updating_fields["filename"] = True
            self.editor.updating_fields["saved"] = True
            return

        if command == [":", "q", Keys.ControlM]:
            self.editor.clear_command()
            if self.editor.saved:
                subprocess.call(
                    [
                        self.editor._display,
                        "/home/ruben/display.py",
                        "-f",
                        self.editor.font,
                        "-s",
                        "off",
                    ]
                )
                subprocess.call(["shutdown", "-h", "now"])
            else:
                self.editor.status = "You have unsaved changes"
        if command == [":", "q", "!", Keys.ControlM]:
            self.editor.clear_command()
            self.editor.saved = True
            self.editor.send([":q", Keys.ControlM])
            return
        if command == [":", "h", Keys.ControlM]:
            self.editor.clear_command()
            _, tmpname = tempfile.mkstemp()
            resolved = str(Path(tmpname).resolve())
            self.editor.previous_file = (
                resolved,
                self.editor.filename,
            )  # Keep track of the previous "real" file (if any)
            cmd = [":W ", resolved, Keys.ControlM]
            self.editor.send(cmd)
            this_path = Path(__file__).resolve()
            root_dir = this_path.parent
            help = root_dir / "help"
            cmd = [":E ", str(help), Keys.ControlM]
            self.editor.send(cmd)
            return

        if command == [":", "d", "o", "t", Keys.ControlM]:
            # Render graphviz
            self.editor.clear_command()
            _, tmpname = tempfile.mkstemp()
            resolved = Path(tmpname).resolve()
            self.editor.previous_file = (
                str(resolved),
                self.editor.filename,
            )  # Keep track of the previous "real" file (if any)
            cmd = [":W ", str(resolved), Keys.ControlM]
            self.editor.send(cmd)
            img_resolved = (
                str((self.editor.docs / Path("imgs") / Path("graph")).resolve())
                + ".png"
            )
            template = (self.editor.docs / Path("dot_template.dot")).read_text()
            content = resolved.read_text()
            adapted = resolved.with_suffix(".dot")
            with adapted.open("a") as f:
                f.write(template)
                f.write(content)
                f.write("}")
            subprocess.call(["dot", "-Tpng", str(adapted), "-o", img_resolved])
            self.editor.status = img_resolved
            self.editor.updating_fields["status"] = True
            self.editor.dot = "/docs/imgs/graph.png"
            self.editor.updating_fields["dot"] = True
            return

        if command[0:2] == [":", "w"] and command[-1] == Keys.ControlM:
            # Write file
            filename = "".join(command[3:-1])
            self.editor.clear_command()
            if filename.strip() == "":
                filename = self.editor.filename
                self.editor.updating_fields["filename"] = True
            try:
                (self.editor.docs / filename).write_text(
                    "\n".join([str(lin) for lin in self.editor.buffer.get()])
                )
                self.editor.filename = filename
                self.editor.updating_fields["filename"] = True
                self.editor.saved = True
                self.editor.updating_fields["saved"] = True
                self.editor.status = f"Saved as {filename}"
                self.editor.updating_fields["status"] = True
            except Exception as e:
                self.editor.err = str(e)
                self.editor.updating_fields["err"] = True
            return
        if command[0:2] == [":", "W"] and command[-1] == Keys.ControlM:
            # This should be protected like E
            filename = "".join(command[3:-1])
            self.editor.clear_command()
            try:
                Path(filename).write_text(
                    "\n".join([str(lin) for lin in self.editor.buffer.get()])
                )
                self.editor.filename = filename
                self.editor.saved = True
                self.editor.status = f"Special saved as {filename}"
                self.editor.updating_fields["filename"] = True
                self.editor.updating_fields["saved"] = True
                self.editor.updating_fields["status"] = True
            except Exception as e:
                self.editor.err = str(e)
                self.editor.updating_fields["err"] = True
            return
        if "".join(command[0:4]) == ":rot" and command[-1] == Keys.ControlM:
            self.editor.clear_command()
            if self.editor.rot == "0":
                self.editor.rot = "90"
            else:
                self.editor.rot = "0"
            self.editor.updating_fields["rot"] = True
            return
        if "".join(command[0:5]) == ":mono" and command[-1] == Keys.ControlM:
            self.editor.clear_command()
            self.editor.font = "mono"
            self.editor.updating_fields["font"] = True
            return
        if "".join(command[0:5]) == ":gyre" and command[-1] == Keys.ControlM:
            self.editor.clear_command()
            self.editor.font = "gyre"
            self.editor.updating_fields["font"] = True
            return
        if "".join(command[0:5]) == ":sans" and command[-1] == Keys.ControlM:
            self.editor.clear_command()
            self.editor.font = "sans"
            self.editor.updating_fields["font"] = True
            return
        if "".join(command[0:6]) == ":serif" and command[-1] == Keys.ControlM:
            self.editor.clear_command()
            self.editor.font = "serif"
            self.editor.updating_fields["font"] = True
            return
        if "".join(command[0:6]) == ":latex" and command[-1] == Keys.ControlM:
            self.editor.clear_command()
            self.editor.font = "latex"
            self.editor.updating_fields["font"] = True
            return
        if "".join(command[0:9]) == ":fontsize" and command[-1] == Keys.ControlM:
            fs = command[10:-1]
            self.editor.clear_command()
            try:
                self.editor.fontsize = int("".join(fs).strip())
                self.editor.updating_fields["fontsize"] = True
                self.editor.status = f"Set font size to {self.editor.fontsize}"
                self.editor.updating_fields["status"] = True
            except Exception as e:
                self.editor.err = str(e)
                self.editor.updating_fields["err"] = True
            return
        if "".join(command[0:3]) == ":fs" and command[-1] == Keys.ControlM:
            fs = command[4:-1]
            self.editor.clear_command()
            try:
                self.editor.fontsize = int("".join(fs).strip())
                self.editor.updating_fields["fontsize"] = True
                self.editor.status = f"Set font size to {self.editor.fontsize}"
                self.editor.updating_fields["status"] = True
            except Exception as e:
                self.editor.err = str(e)
                self.editor.updating_fields["err"] = True
            return
        if (command[0:2] == [":", "e"] or command[0:3] == [":", "e", "!"]) and command[
            -1
        ] == Keys.ControlI:
            command.pop()  # Drop the tab
            if self.editor.completions is None:
                filename = "".join(command).replace(":e!", "").replace(":e", "").strip()
                logger.debug("Globbing on %s", filename)
                files = [str(f.name) for f in self.editor.docs.glob(filename + "*")]
                if len(files) == 0:
                    self.editor.completions = None
                else:
                    self.editor.completions = {"files": files, "idx": -1}
                self.editor.updating_fields["completions"] = True
            else:
                self.editor.completions["idx"] = (
                    self.editor.completions["idx"] + 1
                ) % len(self.editor.completions["files"])
                # TODO: In addition to this, deleting or writing will need to clear completions, reset index…
                md = []
                for i, completion in enumerate(self.editor.completions["files"]):
                    if i == self.editor.completions["idx"]:
                        md.append(f"::{completion}::")
                    else:
                        md.append(completion)
                self.editor.completions_markdownified = markdownify(
                    [" ".join(md)], visible=False
                )
                self.editor.updating_fields["completions"] = True
            return
        if command[0:4] == [":", "v", "i", "z"] and command[-1] == Keys.ControlM:
            try:
                viz_val = "".join(command[4:-1]).strip()
                self.editor.clear_command()
                if len(viz_val) == 0:
                    self.editor.status = "Clearing custom viz"
                    self.editor.viz = None
                else:
                    viz, shift = viz_val.split(":")
                    viz = int(viz)
                    shift = int(shift)
                    self.editor.viz = (viz, shift)
            except Exception as e:
                self.editor.clear_command()
                self.editor.status = f"viz has to be of the form int:int or empty ({e})"
                self.editor.updating_fields["status"] = True
            self.editor.status = f"Setting shift to {self.editor.viz}"
            self.editor.updating_fields["status"] = True
            return
        if command[0:3] == [":", "e", "!"] and command[-1] == Keys.ControlM:
            if self.editor.completions is None:
                filename = "".join(command[4:-1])
            else:
                filename = self.editor.completions["files"][
                    self.editor.completions["idx"]
                ]
            self.editor.clear_command()
            self.editor.status = ""
            self.editor.saved = True
            self.editor.updating_fields["saved"] = True
            self.editor.updating_fields["status"] = True
            self.editor.send([":e ", filename, Keys.ControlM])
            return
        if command[0:2] == [":", "e"] and command[-1] == Keys.ControlM:
            if not self.editor.saved:
                self.editor.status = "You have unsaved changes"
                self.editor.updating_fields["saved"] = True
                return
            if self.editor.completions is None:
                filename = "".join(command[3:-1])
            else:
                filename = self.editor.completions["files"][
                    self.editor.completions["idx"]
                ]
            self.editor.clear_command()
            try:
                text = (self.editor.docs / filename).read_text()
                lines = text.split("\n")
                new_buffer = Buffer(lines=[Line(line) for line in lines])
                self.editor.buffer = new_buffer
                self.editor.filename = filename
                self.editor.saved = True
                self.editor.status = f"Loaded {self.editor.filename}"
                self.editor.updating_fields["status"] = True
                self.editor.updating_fields["saved"] = True
                self.editor.updating_fields["filename"] = True
            except Exception as e:
                self.editor.err = str(e)
                self.editor.updating_fields["err"] = True
            self.editor.cursor.to(0, 0)
            if self.editor.filename.endswith(".dot"):
                self.editor.send([":mono", Keys.ControlM])
            return
        if command[0:2] == [":", "E"] and command[-1] == Keys.ControlM:
            if self.editor.completions is None:
                filename = "".join(command[3:-1])
            else:
                filename = self.editor.completions["files"][
                    self.editor.completions["idx"]
                ]
            self.editor.clear_command()
            try:
                logger.debug("Opening %s", filename)
                text = Path(filename).read_text()
                lines = text.split("\n")
                self.editor.buffer = Buffer([Line(line) for line in lines])
                self.editor.filename = Path(filename).name
                self.editor.saved = True
                self.editor.status = f"Loaded {self.editor.filename}"
                self.editor.updating_fields["status"] = True
                self.editor.updating_fields["saved"] = True
                self.editor.updating_fields["filename"] = True
            except Exception as e:
                self.editor.err = str(e)
                self.editor.updating_fields["err"] = True
            self.editor.cursor.to(0, 0)
            return
        self.editor.clear_command()
