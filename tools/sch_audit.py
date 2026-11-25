#!/usr/bin/env python3
"""Minimal KiCad schematic net auditor.

Parses a .kicad_sch file (S-expression), builds wire connectivity, and
reports, for a chosen symbol reference, which net label(s) each pin
connects to. Also lists all labels and all placed references.

Usage:
  sch_audit.py FILE.kicad_sch [--ref U3] [--labels] [--refs]
"""
import re, sys, math
from collections import defaultdict

def tokenize(s):
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in ' \t\r\n': i += 1
        elif c in '()': toks.append(c); i += 1
        elif c == '"':
            j = i + 1; buf = []
            while j < n and s[j] != '"':
                if s[j] == '\\' and j + 1 < n: buf.append(s[j+1]); j += 2
                else: buf.append(s[j]); j += 1
            toks.append(('str', ''.join(buf))); i = j + 1
        else:
            j = i
            while j < n and s[j] not in ' \t\r\n()': j += 1
            toks.append(s[i:j]); i = j
    return toks

def parse(toks):
    pos = 0
    def rec():
        nonlocal pos
        t = toks[pos]
        if t == '(':
            pos += 1; out = []
            while toks[pos] != ')':
                out.append(rec())
            pos += 1; return out
        pos += 1
        return t[1] if isinstance(t, tuple) else t
    return rec()

def is_node(x, head):
    return isinstance(x, list) and x and x[0] == head

def find_all(node, head, out=None):
    if out is None: out = []
    if isinstance(node, list):
        if is_node(node, head): out.append(node)
        for ch in node: find_all(ch, head, out)
    return out

def get_at(node):
    for ch in node:
        if is_node(ch, 'at'):
            vals = [float(v) for v in ch[1:] if re.fullmatch(r'-?[\d.]+', str(v))]
            ang = vals[2] if len(vals) > 2 else 0.0
            return vals[0], vals[1], ang
    return None

def prop(node, name):
    for ch in node:
        if is_node(ch, 'property') and len(ch) > 2 and ch[1] == name:
            return ch[2]
    return None

def rot(x, y, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    # KiCad schematic Y axis points down; rotation in file is CCW in that frame
    return (x * c - y * s, x * s + y * c)

def main():
    path = sys.argv[1]
    ref_want = None
    if '--ref' in sys.argv: ref_want = sys.argv[sys.argv.index('--ref') + 1]
    root = parse(tokenize(open(path, encoding='utf-8').read()))

    # ---- library symbols: lib_id -> {unit_suffix -> [(num, name, x, y)]}
    libpins = defaultdict(dict)
    for lib in find_all(root, 'lib_symbols'):
        for sym in lib[1:]:
            if not is_node(sym, 'symbol'): continue
            sname = sym[1]
            pins = []
            for sub in sym[1:]:
                if is_node(sub, 'symbol'):
                    for pin in find_all(sub, 'pin'):
                        num = name = None; px = py = 0.0
                        for ch in pin:
                            if is_node(ch, 'at'):
                                px, py = float(ch[1]), float(ch[2])
                            elif is_node(ch, 'name'): name = ch[1]
                            elif is_node(ch, 'number'): num = ch[1]
                        if num is not None: pins.append((num, name, px, py))
                elif is_node(sub, 'pin'):
                    pass
            # pins directly under symbol (single-unit)
            for pin in sym[1:]:
                if is_node(pin, 'pin'):
                    num = name = None; px = py = 0.0
                    for ch in pin:
                        if is_node(ch, 'at'): px, py = float(ch[1]), float(ch[2])
                        elif is_node(ch, 'name'): name = ch[1]
                        elif is_node(ch, 'number'): num = ch[1]
                    if num is not None: pins.append((num, name, px, py))
            if pins: libpins[sname] = pins

    # ---- placed symbols
    placed = []  # (ref, lib_id, x, y, angle, mirror, [(num,name,absx,absy)])
    for sym in find_all(root, 'symbol'):
        libid = None
        for ch in sym:
            if is_node(ch, 'lib_id'): libid = ch[1]
        if not libid: continue
        ref = prop(sym, 'Reference') or '?'
        at = get_at(sym)
        if at is None: continue
        x, y, ang = at
        mirror = None
        for ch in sym:
            if is_node(ch, 'mirror'): mirror = ch[1]
        pins = []
        base = libid.split(':')[-1]
        cands = [k for k in libpins if k == base or k.split(':')[-1] == base]
        pinset = libpins[cands[0]] if cands else []
        for (num, name, px, py) in pinset:
            # KiCad symbol-library Y axis points up; schematic Y points down,
            # so placement negates the library Y (before mirror/rotation).
            mx, my = px, -py
            if mirror == 'x': my = -my
            elif mirror == 'y': mx = -mx
            rx, ry = rot(mx, my, -ang)
            pins.append((num, name, round(x + rx, 2), round(y + ry, 2)))
        placed.append((ref, libid, pins))

    if '--refs' in sys.argv:
        for ref, libid, pins in sorted(placed):
            print(f"{ref}\t{libid}\t{len(pins)} pins")
        return

    # ---- wires & connectivity (union-find over points)
    parent = {}
    def find(p):
        parent.setdefault(p, p)
        while parent[p] != p:
            parent[p] = parent[parent[p]]; p = parent[p]
        return p
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    def on_seg(p, a, b):
        (px, py), (ax, ay), (bx, by) = p, a, b
        if abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) > 0.01: return False
        return min(ax, bx) - 0.01 <= px <= max(ax, bx) + 0.01 and min(ay, by) - 0.01 <= py <= max(ay, by) + 0.01
    segs = []
    for w in find_all(root, 'wire'):
        pts = []
        for ch in w:
            if is_node(ch, 'pts'):
                for xy in ch[1:]:
                    if is_node(xy, 'xy'): pts.append((round(float(xy[1]), 2), round(float(xy[2]), 2)))
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b)); union(a, b)
    allpts = set()
    for a, b in segs: allpts.add(a); allpts.add(b)
    # points lying on segments join them
    for p in list(allpts):
        for a, b in segs:
            if p != a and p != b and on_seg(p, a, b): union(p, a)
    for j in find_all(root, 'junction'):
        at = get_at(j)
        if at:
            p = (round(at[0], 2), round(at[1], 2))
            for a, b in segs:
                if on_seg(p, a, b): union(p, a)

    # ---- labels
    labels = []  # (kind, name, x, y)
    for kind in ('label', 'global_label', 'hierarchical_label'):
        for lb in find_all(root, kind):
            at = get_at(lb)
            if at: labels.append((kind, lb[1], round(at[0], 2), round(at[1], 2)))
    if '--labels' in sys.argv:
        for kind, name, x, y in sorted(labels, key=lambda t: t[1]):
            print(f"{kind}\t{name}\t{x},{y}")
        return
    comp_labels = defaultdict(set)
    for kind, name, x, y in labels:
        p = (x, y)
        hit = None
        for a, b in segs:
            if on_seg(p, a, b): hit = a; break
        if hit is not None: comp_labels[find(hit)].add(name)
        else: comp_labels[('orphan', x, y)].add(name)

    # ---- power symbols: pin name is the net
    for ref, libid, pins in placed:
        if ref.startswith('#PWR'):
            for (num, name, px, py) in pins:
                comp_labels[find((px, py))].add(f"PWR:{name}")

    if ref_want:
        for ref, libid, pins in placed:
            if ref != ref_want: continue
            print(f"== {ref} ({libid})")
            def keyf(t):
                try: return (0, int(t[0]))
                except: return (1, t[0])
            for (num, name, px, py) in sorted(pins, key=keyf):
                nets = comp_labels.get(find((px, py)), set())
                print(f"pin {num}\t{name}\t{sorted(nets) if nets else '-'}")
        return

if __name__ == '__main__':
    main()
