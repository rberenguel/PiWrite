import pytest

from piwrite.markdownify import markdownify


@pytest.mark.parametrize(
    "text,converted",
    [
        ("# foo", "<h1># foo</h1>"),
        ("## foo", "<h2>## foo</h2>"),
        ("### foo", "<h3>### foo</h3>"),
        ("#### foo", "<h4>#### foo</h4>"),
    ],
)
def test_headers(text, converted):
    assert markdownify([text])[0] == converted


@pytest.mark.parametrize(
    "text,converted",
    [
        ("**foo**", "<b>**foo**</b><br/>"),
        (" **foo**", " <b>**foo**</b><br/>"),
        (" **foo** ", " <b>**foo**</b> <br/>"),
        ("**foo** ", "<b>**foo**</b> <br/>"),
        ("**foo**: ", "<b>**foo**</b>: <br/>"),
        (" **foo bar** ", " <b>**foo bar**</b> <br/>"),
    ],
)
def test_bold(text, converted):
    assert markdownify([text])[0] == converted


@pytest.mark.parametrize(
    "text,converted",
    [
        ("_foo_", "<i>_foo_</i><br/>"),
        (" _foo_", " <i>_foo_</i><br/>"),
        (" _foo_ ", " <i>_foo_</i> <br/>"),
        ("_foo_ ", "<i>_foo_</i> <br/>"),
        ("_foo_: ", "<i>_foo_</i>: <br/>"),
        (" _foo bar_ ", " <i>_foo bar_</i> <br/>"),
    ],
)
def test_italics(text, converted):
    assert markdownify([text])[0] == converted


@pytest.mark.parametrize(
    "text,converted",
    [
        ("`foo`", "<tt>`foo`</tt><br/>"),
        (" `foo`", " <tt>`foo`</tt><br/>"),
        (" `foo` ", " <tt>`foo`</tt> <br/>"),
        ("`foo` ", "<tt>`foo`</tt> <br/>"),
        ("`foo`: ", "<tt>`foo`</tt>: <br/>"),
        (" `foo bar` ", " <tt>`foo bar`</tt> <br/>"),
    ],
)
def test_tt(text, converted):
    assert markdownify([text])[0] == converted


@pytest.mark.parametrize(
    "text,converted",
    [
        ("_f_oo_", "<i>_f_oo_</i><br/>"),
        (" _f_oo_", " <i>_f_oo_</i><br/>"),
        (" _f_oo_ ", " <i>_f_oo_</i> <br/>"),
        ("_f_oo_ ", "<i>_f_oo_</i> <br/>"),
        (" _f_oo bar_ ", " <i>_f_oo bar_</i> <br/>"),
    ],
)
def test_escaped_underscore(text, converted):
    assert markdownify([text])[0] == converted
