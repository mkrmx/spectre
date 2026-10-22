"""Minimal s-expression parser/writer for KiCad files, plus symbol-library helpers."""
import re

SYMDIR = "/usr/share/kicad/symbols"


def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c; i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == "\\":
                    buf.append(s[j:j + 2]); j += 2
                else:
                    buf.append(s[j]); j += 1
            yield ('"', "".join(buf)); i = j + 1
        else:
            j = i
            while j < n and s[j] not in " \t\r\n()":
                j += 1
            yield s[i:j]; i = j


def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(x):
    if isinstance(x, tuple):
        return '"' + x[1] + '"'
    if isinstance(x, str):
        return x
    return "(" + " ".join(dump(e) for e in x) + ")"


def q(s):
    return ('"', s)


_libs = {}


def lib_symbol(lib, name):
    """Return the symbol s-expr; resolves 'extends' by returning (parent_flattened)."""
    if lib not in _libs:
        _libs[lib] = parse(open(f"{SYMDIR}/{lib}.kicad_sym").read())
    syms = {e[1][1]: e for e in _libs[lib] if isinstance(e, list) and e and e[0] == "symbol"}
    sym = syms[name]
    ext = [e for e in sym if isinstance(e, list) and e and e[0] == "extends"]
    if ext:
        parent = syms[ext[0][1][1]]
        # flatten: take parent body, rename sub-units, keep child's properties
        flat = ["symbol", q(name)]
        for e in parent[2:]:
            if isinstance(e, list) and e and e[0] == "property":
                continue
            if isinstance(e, list) and e and e[0] == "symbol":
                sub = list(e); sub[1] = q(sub[1][1].replace(parent[1][1], name, 1)); flat.append(sub)
            else:
                flat.append(e)
        for e in sym[2:]:
            if isinstance(e, list) and e and e[0] in ("property",):
                flat.insert(2, e)
        return flat
    return sym


def sym_pins(sym):
    """{number: [(x, y, angle, length, unit, name)]} in library coords (y up)."""
    out = {}
    base = sym[1][1]
    for sub in sym:
        if isinstance(sub, list) and sub and sub[0] == "symbol":
            m = re.match(r".*_(\d+)_(\d+)$", sub[1][1]); unit = int(m.group(1))
            for p in sub:
                if isinstance(p, list) and p and p[0] == "pin":
                    at = next(e for e in p if isinstance(e, list) and e[0] == "at")
                    ln = next(e for e in p if isinstance(e, list) and e[0] == "length")
                    num = next(e for e in p if isinstance(e, list) and e[0] == "number")[1][1]
                    nm = next(e for e in p if isinstance(e, list) and e[0] == "name")[1][1]
                    out.setdefault(num, []).append((float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                                                    float(ln[1]), unit, nm))
    return out


def props(sym):
    return {e[1][1]: e for e in sym if isinstance(e, list) and e and e[0] == "property"}
