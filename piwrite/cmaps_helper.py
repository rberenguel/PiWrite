import re

def has_arrow(line):
    return "->" in line

def has_url(line):
    return "URL=" in line

# TODO: accept also url, or just having http or https

subgraph_cluster = re.compile(r"^\s*subgraph cluster_(\w+).*{.*$")
replacement = re.compile(r"^\s*(\$\S+)\s*=\s*(\S+)\s*$")
comment = re.compile(r"\s*\/\/.*")
open_brace = re.compile(r"\s*{\s*$")
close_brace = re.compile(r"\s*}\s*$")
attr = re.compile(r"^\s*\w+=.*\s*$")
attrs_of_arrow = re.compile(r"^\s*\S+\s*->\s*\S+\s+(.*)$")
attrs_of_node = re.compile(r"^\s*\S+\s+(.*)$")
lone_cluster = re.compile(r"^\s*cluster\s+(\S+).*{.*$")
rgba_hex = re.compile(r"^#[0-9a-f]{8}$/.")

def has_subgraph(line):
    print(subgraph_cluster.match(line))
    return subgraph_cluster.match(line) is not None

def has_cluster(line):
    return lone_cluster.match(line) is not None

def has_replacement(line):
    return replacement.match(line) is not None

def get_replacement(line):
    matches = replacement.match(line) 
    name = matches.group(1)
    value = matches.group(2)
    return name, value

def is_comment(line):
    return comment.match(line) is not None

def is_only_brace(line):
    return (open_brace.match(line) is not None) or (close_brace.match(line) is not None)

def is_attr(line):
    return attr.match(line) is not None

def is_rgba_hex(line):
    return rgba_hex.match(line) is not None

def get_attrs_of_arrow(line):
    matches = attrs_of_arrow.match(line)
    attrs = matches.group(1)
    return attrs

def get_attrs_of_node(line):
    matches = attrs_of_node.match(line)
    attrs = matches.group(1)
    return attrs

def get_subgraph_cluster_name(line):
    matches = subgraph_cluster.match(line)
    name = matches.group(1)
    return name

def get_cluster_name(line):
    matches = lone_cluster.match(line)
    name = matches.group(1)
    return name

def label_breaker(label):
    left_align = "\\l"
    if len(label) > 30 and not ("\\n" in label):
        words = label.split(" ")
        lines = []
        curr_line = []
        for word in words:
            curr_line.append(word)
            joined = " ".join(curr_line)
            if len(joined) > 30:
                lines.append(joined)
                curr_line = []
        lines.append(" ".join(curr_line))
        return left_align.join(lines)
    else:
        return label

def converter(lines):
    result = []
    replacements = {}
    tab = "  "
    ttab = tab + tab
    clusters = []
    result.append(tab + f"""label="\\n{lines[0].replace("# ", "")}"\\n\\n""")
    for line of lines[1:]:
        if is_only_brace(line) or is_attr(line) or is_comment(line):
            result.append(tab + line)
            continue
        if has_replacement(line):
            key, value = get_replacement(line)
            replacements[key] = value
            continue
        for key, value in replacements.items():
            line = line.replace(key, value)
        
        if has_subgraph(line) or has_cluster(line):
            name = None
            if has_subgraph(line):
                name = get_subgraph_cluster_name(line)
            else:
                name = get_cluster_name(line)
            clusters.append(name)
            fill = None
            for word in line.split(" "):
                if is_rgba_hex(word):
                    fill = f"""{ttab}fillcolor="{word.strip()}" """
                    line = line.replace(word.trim(), "")
            result.append(f"""{tab}subgraph cluster_{name} {""")
            result.append(f"""{ttab}style="filled, rounded, dotted" """)
            if fill is not None:
                result.append(fill)
            # Append the invisible node for linking
            result.append(f"""{ttab} label="{name}" """)
            result.append(f"""{ttab} {name} [style=invis,width=0,label="",fixedsize=true]""")
            continue

#     let attrs, src, dst
#     if(hasArrow(line)){
#       attrs = getAttrsArrow(line);
#       const match = /^\s*(\w+)\s*->\s*(\w+).*$/.exec(line)
#       src = match[1]
#       dst = match[2]
#       src = src.trim()
#       dst = dst.trim()
#     } else {
#       attrs = getAttrsNode(line)
#     }
#     let addendum = ""
#     if(src && clusters.includes(src)){
#       addendum = ` ltail="cluster_${src}"`
#     }
#     if(dst && clusters.includes(dst)){
#       addendum = ` lhead="cluster_${dst}"`
#     }
#     if(!attrs || attrs.length == 1){
#       const compoundEdge = addendum != "" ? ` [${addendum}]` : ""
#       result.push(tab + line + compoundEdge)
#       continue
#     }
#     const linkUTF = hasURL(attrs[1]) ? " &#128279;" : ""
#     let [label, props] = attrs[1].split(";")
#     if(hasArrow(line) && label.trim() == "!"){
#       label = ""
#       props = props ? props : "" + "style=invis"
#     }
#     const labelPropper = (label, props) => `[label="${labelBreaker(label)}${linkUTF}"${props ? " " + props : ""}${addendum}]`
#     const operation = line.replace(" " + attrs[1], " ")
#     let converted = `${operation} ${labelPropper(label, props)}`
#     if(!hasArrow(line) && label.trim() == "="){
#       converted =  `${operation} ${labelPropper(operation.trim(), props)}`
#     }
#     result.push(tab + converted)
#   }
#   let joined = result.join("<br/>")
#   return joined
# }



