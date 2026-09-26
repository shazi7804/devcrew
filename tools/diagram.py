#!/usr/bin/env python3
"""Keep the ASCII diagrams in this repo aligned.

    tools/diagram.py check FILE...        report misaligned boxes + long lines
    tools/diagram.py fix   FILE...        pad each box to its own widest line
    tools/diagram.py fix -u FILE...       all boxes in one fence share a width
                                          (for stacked L3/L2/L1 layer diagrams)
    tools/diagram.py fix -w 80 -u FILE    force an exact width — this one can
                                          SHRINK a box, not only grow it

Alignment cannot be eyeballed reliably, because the diagrams mix characters of
different DISPLAY width: 🔴 and ①②③④ occupy two terminal columns, not one. A box
whose source lines are the same length can still render ragged. `check` measures
columns, so it sees what the reader sees. It found six already-broken boxes the
repo had shipped.

WHAT COUNTS AS A BOX — a true rectangle: an opener whose first non-space char is
┌ and which ends in ┐, then members of the form │…│ or ├…┤, closed by └…┘. The
first line that does not fit abandons the candidate. Everything else is left
alone on purpose: branch connectors (┌──┴──┐), arrow spines and cycle art use
the same characters as corners without being rectangles, so there is no width to
check and a checker that guessed would only produce false failures. Those are
eyeball-only by nature — which is a reason to prefer a real box when you can.

LINE WIDTH — a diagram line past 80 columns wraps in a default terminal, and a
wrapped box is worse than no box. `check` reports those too; the fix is to
shorten the text, never to widen the box. Only fences that actually contain box
art are measured: a YAML or shell block is prose the reader scrolls, not a
drawing that has to hold its shape, and flagging those would just train everyone
to ignore the output.
"""
import pathlib
import sys
import unicodedata

MAX_WIDTH = 80
BOX_ART = "┌┐└┘├┤┬┴┼─│▶◀▲▼"


def width(s):
    """Display width: East-Asian Wide/Fullwidth (incl. emoji) count as 2."""
    n = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return n


def fences(lines):
    """Map 0-based line index -> fence number, for lines inside a code fence."""
    out, idx, infence = {}, -1, False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            if not infence:
                idx += 1
            infence = not infence
            continue
        if infence:
            out[i] = idx
    return out


def boxes(lines):
    """Yield lists of 0-based indices, one list per true rectangle in a fence."""
    infence = False
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].rstrip()
        if s.lstrip().startswith("```"):
            infence = not infence
            i += 1
            continue
        if not infence:
            i += 1
            continue
        if s.lstrip().startswith("┌") and s.endswith("┐"):
            members, j, closed = [i], i + 1, False
            while j < n:
                u = lines[j].rstrip()
                v = u.lstrip()
                if v.startswith("```"):
                    break
                if (v.startswith("│") and u.endswith("│")) or (
                    v.startswith("├") and u.endswith("┤")
                ):
                    members.append(j)
                    j += 1
                    continue
                if v.startswith("└") and u.endswith("┘"):
                    members.append(j)
                    closed = True
                break
            if closed:
                yield members
                i = j + 1
                continue
        i += 1


def check(paths):
    bad = 0
    for path in paths:
        lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")
        for box in boxes(lines):
            seen = {}
            for j in box:
                seen.setdefault(width(lines[j].rstrip()), []).append(j + 1)
            if len(seen) > 1:
                print(f"{path}: box at line {box[0] + 1} has mismatched widths:")
                for k in sorted(seen):
                    print(f"    width {k}: lines {seen[k]}")
                bad += 1
        infence = fences(lines)
        drawn = {f for i, f in infence.items()
                 if any(ch in lines[i] for ch in BOX_ART)}
        for i, line in enumerate(lines):
            if infence.get(i, -1) in drawn and width(line.rstrip()) > MAX_WIDTH:
                print(f"{path}:{i + 1}: {width(line.rstrip())} columns "
                      f"(> {MAX_WIDTH}, wraps in a default terminal)")
                bad += 1
    print("ALIGNED" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


def fix(paths, uniform, target_width=None):
    def repad(s, target):
        """Grow or shrink a box line to `target` columns by changing only the
        filler that sits just inside the closing border. Shrinking stops at the
        content — a line with nothing left to give is returned unchanged, and
        `check` will then report it so a human shortens the words."""
        gap = target - width(s)
        if gap == 0:
            return s
        fill = "─" if s[-1] in "┐┘┤" else " "
        if gap > 0:
            return s[:-1] + fill * gap + s[-1]
        body = s[:-1]
        slack = len(body) - len(body.rstrip(" ─"))
        cut = min(slack, -gap)
        return body[:len(body) - cut] + s[-1]

    for path in paths:
        p = pathlib.Path(path)
        lines = p.read_text(encoding="utf-8").split("\n")
        out = list(lines)
        infence = fences(lines)

        groups = {}
        for box in boxes(lines):
            key = infence.get(box[0], -1) if uniform else box[0]
            groups.setdefault(key, []).append(box)

        for boxlist in groups.values():
            target = target_width or max(width(lines[j].rstrip())
                                         for box in boxlist for j in box)
            for box in boxlist:
                for j in box:
                    out[j] = repad(lines[j].rstrip(), target)

        p.write_text("\n".join(out), encoding="utf-8")
        print(f"normalised {path}{' (fence-uniform)' if uniform else ''}")
    return 0


def main(argv):
    if not argv or argv[0] not in ("check", "fix"):
        print(__doc__.split("\n\n")[1].strip(), file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    uniform, target = False, None
    while rest and rest[0].startswith("-"):
        if rest[0] in ("-u", "--fence-uniform"):
            uniform, rest = True, rest[1:]
        elif rest[0] in ("-w", "--width"):
            target, rest = int(rest[1]), rest[2:]
        else:
            print(f"unknown option {rest[0]}", file=sys.stderr)
            return 2
    if not rest:
        print("no files given", file=sys.stderr)
        return 2
    return check(rest) if cmd == "check" else fix(rest, uniform, target)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
