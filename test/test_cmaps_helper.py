import pytest

import piwrite.cmaps_helper as ch

@pytest.mark.parametrize(
    "line,expected",
    [
        ("a -> b", True),
        ("arstartsarst", False),
        ("a-> b", True),
        ("a ->b", True),
        ("a->b", True),
    ],
)
def test_has_arrow(line, expected):
    assert ch.has_arrow(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("subgraph cluster_foo{", True),
        ("aarstarst", False),
    ],
)
def test_has_subgraph(line, expected):
    assert ch.has_subgraph(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("cluster foo{", True),
        ("aarstarst", False),
    ],
)
def test_has_cluster(line, expected):
    assert ch.has_cluster(line) == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        ("$foo = bar", True),
        ("$foo=bar", True),
        ("$foo =bar", True),
        ("$foo= bar", True),
        ("foo=bar", False),
        ("$foo bar", False),
    ],
)
def test_has_replacement(line, expected):
    assert ch.has_replacement(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("$foo = bar", ("$foo", "bar")),
        ("$foo=bar", ("$foo", "bar")),
        ("$foo =bar", ("$foo", "bar")),
        ("$foo= bar", ("$foo", "bar")),
    ],
)
def test_get_replacement(line, expected):
    assert ch.get_replacement(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("// foo", True),
        ("/// foo", True),
        ("//foo", True),
        ("/ foo", False),
    ],
)
def test_is_comment(line, expected):
    assert ch.is_comment(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("{", True),
        ("    {  ", True),
        ("}", True),
        ("  } ", True),
        ("  }}", False),
        ("  {{ ", False),
        (" }a", False),
        ("  b{ ", False),
    ],
)
def test_is_only_brace(line, expected):
    assert ch.is_only_brace(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("foo=bar", True),
        ("foo = bar", False),
        (" = bar", False),
    ],
)
def test_is_attr(line, expected):
    assert ch.is_attr(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("zzz -> arstd label thingy;color=red", "label thingy;color=red"),
        ("zzz ->arstd label thingy; color=red", "label thingy; color=red"),
        ("zzz-> arstd label thingy; color=red  ", "label thingy; color=red  "),
        ("zzz -> arstd ;color=red", ";color=red"),
        ("zzz -> arstd ", ""),
    ],
)
def test_get_attrs_of_arrow(line, expected):
    assert ch.get_attrs_of_arrow(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("zzzz The zs; foo", "The zs; foo"),
        ("zzzz The zs; ", "The zs; "),
        ("zzzz The zs", "The zs"),
    ],
)
def test_get_attrs_of_node(line, expected):
    assert ch.get_attrs_of_node(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("subgraph cluster_foo {", "foo"),
        ("subgraph cluster_foo  {  arstarstarst", "foo"),
        ("subgraph cluster_foo{", "foo"),
    ],
)
def test_get_subgraph_cluster_name(line, expected):
    assert ch.get_subgraph_cluster_name(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("cluster foo {", "foo"),
        (" cluster foo  {  arstarstarst", "foo"),
        ("cluster foo{", "foo"),
    ],
)
def test_get_cluster_name(line, expected):
    assert ch.get_cluster_name(line) == expected

@pytest.mark.parametrize(
    "line,expected",
    [
        ("a very very long long long label label label", "a very very long long long label\\llabel label"),
        ("short one", "short one")
    ],
)
def test_label_breaker(line, expected):
    assert ch.label_breaker(line) == expected




