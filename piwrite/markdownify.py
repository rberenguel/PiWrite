import re


def start_highlighter(ent, clip=0):
    def focuser(line, idx, current):
        if idx == current:
            return f"""<{ent} class="focus">{line[clip:]}</{ent}>"""
        else:
            return f"""<{ent}>{line[clip:]}</{ent}>"""

    return focuser


STARTS = {
    "# ": start_highlighter("h1"),  # lambda t: f"<h1>{t}</h1>",
    "## ": start_highlighter("h2"),  # lambda t: f"<h2>{t}</h2>",
    "### ": start_highlighter("h3"),  # lambda t: f"<h3>{t}</h3>",
    "#### ": start_highlighter("h4"),  # lambda t: f"<h4>{t}</h4>",
    "- ": start_highlighter("li", clip=2),  # lambda t: f"<li>{t[2:]}</li>",
}


def bolding(line):
    beg_of_word = re.compile(r"(^|\s)(\*\*\S)")
    end_of_word = re.compile(r"(\S\*\*)($|\s|:)")
    new_line = re.sub(beg_of_word, "\\1<b>\\2", line)
    new_line = re.sub(end_of_word, "\\1</b>\\2", new_line)
    return new_line


def highlighting(line):
    # TODO: needs tests
    beg_of_word = re.compile(r"(^|\s)(::\S)")
    end_of_word = re.compile(r"(\S::)($|\s)")
    new_line = re.sub(beg_of_word, "\\1<span class='highlight'>\\2", line)
    new_line = re.sub(end_of_word, "\\1</span>\\2", new_line)
    return new_line


def italicising(line):
    beg_of_word = re.compile(r"(^|\s)(_\S)")
    end_of_word = re.compile(r"(\S_)($|\s|:)")
    new_line = re.sub(beg_of_word, "\\1<i>\\2", line)
    new_line = re.sub(end_of_word, "\\1</i>\\2", new_line)
    return new_line


def teletyping(line):
    beg_of_word = re.compile(r"(^|\s)(`\S)")
    end_of_word = re.compile(r"(\S`)($|\s|:)")
    new_line = re.sub(beg_of_word, "\\1<tt>\\2", line)
    new_line = re.sub(end_of_word, "\\1</tt>\\2", new_line)
    return new_line


def focus(line, idx, current):
    if idx == current:
        return f"""<span class="focus">{line}</span>"""
    return line


def markdownify(original_lines, current_line=-1):
    """Convert simple Markdown to reasonable HTML (with mostly visible Markdown markers), with highlighting of the current line"""
    new_lines = []
    skip = False
    for idx, line in enumerate(original_lines):
        newline = line
        if line == "---":
            new_lines.append(focus("<hr/>", idx, current_line))
            continue
        if newline == "":
            new_lines.append(
                focus("""<span class="small">&nbsp;</span>""", idx, current_line)
            )
            continue
            # escape = True
        # if escape:
        # escape = False
        # continue

        newline = bolding(newline)
        newline = italicising(newline)
        newline = teletyping(newline)
        newline = highlighting(newline)
        for key, transform in STARTS.items():
            if line.startswith(key):
                skip = True
                if key == "- ":
                    # newline = key + focus(newline[2:], idx, current_line)
                    newline = transform(newline, idx, current_line)
                else:
                    newline = transform(newline, idx, current_line)
                    # newline = focus(newline, idx, current_line)
        else:
            if not skip:
                newline = focus(newline, idx, current_line)
                newline = newline + "<br/>"
            else:
                skip = False
        new_lines.append(newline)
    return new_lines
