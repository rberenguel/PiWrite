from enum import Enum

import pytest
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys

import piwrite.editor as editor

LETTER_I = KeyPress("i")
ESC = Keys.Escape
DEL = Keys.ControlH
ENT = Keys.ControlM
LEFT = Keys.Left


def K(letter):
    return KeyPress(letter)


def test_insertion():
    v = editor.Editor()
    v.send(["if"])
    assert v.buffer.get()[0] == "f"


def test_save():
    v = editor.Editor()
    filename = "foo"
    text = "text"
    command = ["i", text, ESC, ":w ", filename, ENT]
    v.send(command)
    assert v.mode() == str(editor.Mode.NORMAL)
    docs = v.docs
    fil = docs / filename
    written_text = fil.read_text()
    assert written_text == text
    assert v.filename == filename
    fil.unlink()


def test_read():
    v = editor.Editor()
    filename = "foo"
    text = "text"
    command = ["i", text, ESC, ":w ", filename, ENT]
    v.send(command)
    w = editor.Editor()
    command2 = ["it", ESC, ":e ", filename, ENT]
    w.send(command)
    assert w.buffer.get()[0] == "text"
    docs = w.docs
    fil = docs / "foo"
    fil.unlink()


def test_left():
    v = editor.Editor()
    cmd = ["if"]
    v.send(cmd)
    assert v.buffer.get()[0] == "f"
    cmd = [LEFT, "g"]
    v.send(cmd)
    assert v.buffer.get()[0] == "gf"
    v.send([ESC, LEFT, "ih"])
    assert v.buffer.get()[0] == "hgf"


def test_right():
    v = editor.Editor()
    cmd = ["i2"]
    v.send(cmd)
    assert v.buffer.get()[0] == "2"
    cmd = [LEFT, "1", Keys.Right, "3"]
    v.send(cmd)
    assert v.buffer.get()[0] == "123"
    v.send([ESC, Keys.ControlA, Keys.Right, "i."])
    assert v.buffer.get()[0] == ".123"


def test_up():
    v = editor.Editor()
    cmd = ["i1"]
    v.send(cmd)
    assert v.buffer.get()[0] == "1"
    cmd = [ENT, "2"]
    v.send(cmd)
    assert v.buffer.get()[1] == "2"
    cmd = [Keys.Up, "3"]
    v.send(cmd)
    assert v.buffer.get()[0] == "13"
    cmd = [ENT, "4", ESC, Keys.Up]
    v.send(cmd)
    assert v.mode() == str(editor.Mode.NORMAL)
    cmd = ["i5"]
    v.send(cmd)
    assert (
        v.buffer.get()[0] == "513"
    )  # Remember ESC switches cursor one position back from insertion


def test_new_lines():
    v = editor.Editor()
    cmd = ["i1"]
    v.send(cmd)
    assert v.buffer.get()[0] == "1"
    cmd = [ENT, "2"]
    v.send(cmd)
    assert v.buffer.get() == ["1", "2"]


def test_line_break():
    v = editor.Editor()
    cmd = ["i12", LEFT, ENT]
    v.send(cmd)
    assert v.buffer.get() == ["1", "2"]


def test_indent_ish():
    v = editor.Editor()
    cmd = ["i  b", ENT, "a"]
    v.send(cmd)
    s = v.buffer.get()[1]
    assert v.buffer.get()[0] == "  b"
    assert s == "  a"


def test_deletion():
    v = editor.Editor()
    cmd = ["i123", DEL]
    v.send(cmd)
    assert v.buffer.get()[0] == "12"


def test_deletion_of_beginning():
    v = editor.Editor()
    cmd = ["i123", ESC, "o456", Keys.ControlA, DEL]
    v.send(cmd)
    assert v.buffer.get()[0] == "123456"
    assert len(v.buffer) == 1


def test_dd():
    v = editor.Editor()
    cmd = ["i123", ESC, "ddi1"]
    v.send(cmd)
    assert v.buffer.get()[0] == "1"

    v = editor.Editor()
    cmd = ["i123", ENT, "456", Keys.Up, ESC, "dd"]
    v.send(cmd)
    assert v.buffer.get()[0] == "456"


@pytest.mark.parametrize(
    "text,deleted,yanked",
    [
        (["a word", ESC], "a", " word"),
        (["a word ", LEFT, LEFT, ESC], "a ", "word "),
        (["a word ", LEFT, LEFT, ESC], "a ", "word "),
        (["a wo ", LEFT, LEFT, LEFT, LEFT, ESC], "wo ", "a "),
    ],
)
def test_delete_around_word(text, deleted, yanked):
    v = editor.Editor()
    cmd = ["i"] + text + ["daw"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == deleted
    assert v.yank == [yanked]


@pytest.mark.parametrize(
    "text,deleted,yanked",
    [
        (["a word", ESC], "a ", "word"),
        (["a word ", LEFT, LEFT, ESC], "a  ", "word"),
        (["a word ", LEFT, LEFT, ESC], "a  ", "word"),
        (["a wo ", LEFT, LEFT, LEFT, LEFT, ESC], " wo ", "a"),
    ],
)
def test_delete_inside_word(text, deleted, yanked):
    v = editor.Editor()
    cmd = ["i"] + text + ["diw"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == deleted
    assert v.yank == [yanked]


@pytest.mark.parametrize(
    "text,deleted",
    [
        (["da word", ESC], "dafoo"),
        (["da word ", LEFT, LEFT, LEFT, ESC], "da foo"),
        (["da word ", LEFT, LEFT, LEFT, ESC], "da foo"),
        (["da wo ", LEFT, LEFT, LEFT, LEFT, ESC], "foowo "),
    ],
)
def test_change_around_word(text, deleted):
    v = editor.Editor()
    cmd = ["i"] + text + ["cawfoo"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == deleted


@pytest.mark.parametrize(
    "text,deleted",
    [
        (["da word", ESC], "da foo"),
        (["da word ", LEFT, LEFT, LEFT, ESC], "da foo "),
        (["da word ", LEFT, LEFT, LEFT, ESC], "da foo "),
        (["da wo ", LEFT, LEFT, LEFT, LEFT, ESC], "foo wo "),
    ],
)
def test_change_inside_word(text, deleted):
    v = editor.Editor()
    cmd = ["i"] + text + ["ciwfoo"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == deleted


def test_paste_problem():
    v = editor.Editor()
    cmd = ["ihello", ESC, "dawa", ENT, ESC, "p"]
    v.send(cmd)
    assert str(v.buffer.get()[1]) == "hello"


def test_basic_undo():
    v = editor.Editor()
    cmd = ["i1 ", ESC, "A2 ", ESC, "A3 ", ESC, "uA4"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == "1 2 4"


def test_branch_undo():
    v = editor.Editor()
    cmd = ["i1 ", ESC, "A2 ", ESC, "A3 ", ESC, "uuA4 ", ESC, "A5"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == "1 4 5"


def test_redo():
    v = editor.Editor()
    cmd = ["i1 ", ESC, "A2 ", ESC, "A3 ", ESC, "uu", Keys.ControlR]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == "1 2 "


def test_redo_and_undo():
    v = editor.Editor()
    # 1 2 3
    # 1
    # 1 2
    # 1 2 4
    # 1 2
    cmd = ["i1 ", ESC, "A2 ", ESC, "A3 ", ESC, "uu", Keys.ControlR, "A4", ESC, "u"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == "1 2 "


def test_undo_depth():
    v = editor.Editor()
    v.UNDO_DEPTH = 2
    cmd = ["i1 ", ESC, "A2 ", ESC, "A3 ", ESC, "uA4"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == "1 2 4"


def test_redo_and_undo_with_depth():
    v = editor.Editor()
    v.UNDO_DEPTH = 2
    # 1 2 3
    # 1 2 (just one depth)
    # 1 2 3 (redo)
    # 1 2 3 4
    # 1 2 3 (u)
    cmd = ["i1 ", ESC, "A2 ", ESC, "A3 ", ESC, "uu", Keys.ControlR, "A4", ESC, "u"]
    v.send(cmd)
    assert str(v.buffer.get()[0]) == "1 2 3 "


def test_redo_limit():
    v = editor.Editor()
    v.send([Keys.ControlR, Keys.ControlR])


def test_undo_limit():
    v = editor.Editor()
    v.send(["uuuu"])


def test_basic_paste():
    v = editor.Editor()
    cmd = ["ia word", ESC, "diwa", ENT, ESC, "p"]
    v.send(cmd)
    assert str(v.buffer.get()[1]) == "word"
