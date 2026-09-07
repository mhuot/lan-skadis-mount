"""Redraw the joint cross-section on the docs page from the build script.

Runs locally in .venv (stdlib only):

    .venv/bin/python scripts/build_joint_diagram.py

The drawing on the Pages site is a scaled section through the screw axis, and
it is the clearest thing on the page precisely because it shows a cavity you
cannot see from outside. That makes it the easiest thing on the page to leave
quietly wrong: the nut got 0.8 mm thicker and every render, model and number
updated except a hand-drawn SVG.

So it is generated, from the same constants build_skadis_nut_bracket.py uses,
and spliced into docs/index.html between its <svg class="joint"> tags. Run it
after changing any dimension the section shows.
"""

import pathlib
import re

BUILD = pathlib.Path("scripts/build_skadis_nut_bracket.py")
PAGE = pathlib.Path("docs/index.html")
SCALE, ORIGIN_X, ORIGIN_Y = 20.0, 150.0, 250.0


def constant(name):
    """Read a float constant out of the build script."""
    match = re.search(rf"^{name} = ([0-9.]+)", BUILD.read_text(encoding="utf-8"), re.M)
    if match is None:
        raise SystemExit(f"{name} not found in {BUILD}")
    return float(match.group(1))


# pylint: disable-next=too-many-locals
def draw():
    """The section, as a list of SVG elements."""
    board = constant("BOARD_THICKNESS")
    screw_length = constant("SCREW_LENGTH")
    tip_clearance = constant("SCREW_TIP_CLEARANCE")
    wall = constant("NUT_WALL_THICKNESS")
    nut_thick = constant("NUT_THICKNESS")
    nut_flats = constant("NUT_ACROSS_FLATS")
    plate = screw_length - board + tip_clearance
    cavity_depth = nut_thick + constant("NUT_CAVITY_CLEARANCE")
    cavity_height = nut_flats + constant("NUT_CHANNEL_CLEARANCE")
    slot_height = constant("SCREW_DIAMETER") + constant("SCREW_CLEARANCE")
    head_radius = 3.5

    def x(mm):
        return round(ORIGIN_X + (mm + 6.0) * SCALE, 1)

    def y(mm):
        return round(ORIGIN_Y - mm * SCALE, 1)

    top, bottom = y(9.6), y(-9.6)
    slot_top, slot_bottom = y(slot_height / 2), y(-slot_height / 2)
    cavity_top, cavity_bottom = y(cavity_height / 2), y(-cavity_height / 2)
    cavity_front, cavity_back = x(plate - wall), x(plate - wall - cavity_depth)
    parts = [
        f'<rect class="steel" x="{x(-6)}" y="{top-26}" width="{x(0)-x(-6)}" '
        f'height="{bottom-top+52}" rx="2"/>',
        f'<path class="printed" d="M {x(0)} {top} H {x(plate)} V {slot_top} '
        f'H {cavity_front} V {cavity_top} H {cavity_back} V {slot_top} H {x(0)} Z"/>',
        f'<path class="printed" d="M {x(0)} {slot_bottom} H {cavity_back} '
        f"V {cavity_bottom} H {cavity_front} V {slot_bottom} H {x(plate)} "
        f'V {bottom} H {x(0)} Z"/>',
        f'<rect class="board" x="{x(plate)}" y="{top-26}" '
        f'width="{x(plate+board)-x(plate)}" height="{y(7.5)-top+26}"/>',
        f'<rect class="board" x="{x(plate)}" y="{y(-7.5)}" '
        f'width="{x(plate+board)-x(plate)}" height="{bottom+26-y(-7.5)}"/>',
        # Screw first, nut over it: in one tone and the other order the two
        # merge into a single unreadable grey shape.
        f'<rect class="screw" x="{x(plate+board-screw_length)}" y="{y(2.0)}" '
        f'width="{x(plate+board)-x(plate+board-screw_length)}" '
        f'height="{y(-2.0)-y(2.0)}" rx="1"/>',
        f'<rect class="screw" x="{x(plate+board)}" y="{y(head_radius)}" '
        f'width="{x(plate+board+2.4)-x(plate+board)}" '
        f'height="{y(-head_radius)-y(head_radius)}" rx="1.5"/>',
        f'<rect class="nut" x="{cavity_back}" y="{y(nut_flats/2)}" '
        f'width="{x(plate-wall-cavity_depth+nut_thick)-cavity_back}" '
        f'height="{y(-nut_flats/2)-y(nut_flats/2)}" rx="1"/>',
    ]
    leaders = {3: (cavity_back + 12, 183), 4: (cavity_back + 14, 300)}
    for number, cx, cy in (
        (1, 210, 100),
        (2, 462, 110),
        (3, 330, 140),
        (4, 330, 360),
        (5, 450, 380),
        (6, 300, 250),
        (7, 552, 70),
        (8, 600, 250),
    ):
        if number in leaders:
            parts.append(
                f'<line class="leader" x1="{cx}" y1="{cy}" '
                f'x2="{leaders[number][0]}" y2="{leaders[number][1]}"/>'
            )
        parts.append(f'<circle class="callout" cx="{cx}" cy="{cy}" r="15"/>')
        parts.append(f'<text class="callout-text" x="{cx}" y="{cy+6}">{number}</text>')
    return parts


def main():
    """Regenerate the drawing and splice it into the page."""
    body = "\n".join("      " + part for part in draw())
    svg = (
        '      <svg class="joint" viewBox="0 0 720 500" role="img" aria-label='
        "\"Cross-section through the bracket at the screw axis: the upright's face "
        "metal, the plate holding a captured square nut in an internal cavity behind "
        "a solid wall, the SKADIS board, and the M4 screw clamping the board flat to "
        'the plate.">\n' + body + "\n      </svg>"
    )
    page = PAGE.read_text(encoding="utf-8")
    start = page.index('      <svg class="joint"')
    end = page.index("</svg>", start) + len("</svg>")
    PAGE.write_text(page[:start] + svg + page[end:], encoding="utf-8")
    print(f"redrew the joint section in {PAGE} ({len(draw())} elements)")


if __name__ == "__main__":
    main()
