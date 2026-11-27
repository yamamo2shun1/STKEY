"""Select both sides of track-width changes in the KiCad PCB Editor.

Run this file from the PCB Editor's scripting console:
    exec(open("path/to/select_width_changes.py", encoding="utf-8").read())

Run select_width_changes() again after editing to refresh the selection.
"""

from collections import defaultdict

import pcbnew


def select_width_changes(first_width=0.15, second_width=0.20):
    """Select adjoining tracks of the two widths, specified in millimeters."""
    board = pcbnew.GetBoard()
    if board is None:
        raise RuntimeError("KiCad PCB エディターのスクリプトコンソールで実行してください。")

    widths = {pcbnew.FromMM(first_width), pcbnew.FromMM(second_width)}
    if len(widths) != 2 or min(widths) <= 0:
        raise ValueError("異なる正の線幅を2つ指定してください。")

    junctions = defaultdict(list)
    vias = defaultdict(list)
    pads = defaultdict(list)
    for track in board.GetTracks():
        net = track.GetNetCode()
        if isinstance(track, pcbnew.PCB_VIA):
            point = track.GetPosition()
            vias[net, point.x, point.y].append(track)
        elif track.GetWidth() in widths:
            for point in (track.GetStart(), track.GetEnd()):
                junctions[net, track.GetLayer(), point.x, point.y].append(track)

    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            pads[pad.GetNetCode()].append(pad)

    selected = {}
    junction_count = 0
    for (net, layer, x, y), tracks in junctions.items():
        if {track.GetWidth() for track in tracks} != widths:
            continue
        if any(via.IsOnLayer(layer) for via in vias.get((net, x, y), ())):
            continue
        point = pcbnew.VECTOR2I(x, y)
        if any(pad.IsOnLayer(layer) and pad.HitTest(point) for pad in pads.get(net, ())):
            continue
        junction_count += 1
        for track in tracks:
            selected[track.m_Uuid.AsString()] = track

    for item in pcbnew.GetCurrentSelection():
        item.ClearSelected()
    for track in selected.values():
        track.SetSelected()
    pcbnew.Refresh()

    actual = {item.m_Uuid.AsString() for item in pcbnew.GetCurrentSelection()}
    if actual != selected.keys():
        raise RuntimeError("KiCad の選択状態と検出した線分が一致しませんでした。")
    print(f"切り替え: {junction_count}箇所、選択: {len(actual)}線分")


if __name__ == "__main__":
    select_width_changes()
