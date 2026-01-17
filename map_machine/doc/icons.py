"""Icon grids for documentation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from colour import Color
from roentgen import Roentgen, get_roentgen

from map_machine.pictogram.icon_collection import IconCollection

if TYPE_CHECKING:
    from collections.abc import Callable

    from roentgen.icon import IconSpecification

SKIP: bool = True
BLACK: Color = Color("black")


roentgen: Roentgen = get_roentgen()


def draw_special_grid(
    all_icons: dict[str, IconSpecification],
    function: Callable[[IconSpecification], bool],
    path: Path,
    color: Color | None = None,
) -> None:
    """Draw special icon grid to illustrate map feature."""
    icons: list[IconSpecification] = list(filter(function, all_icons.values()))
    icons.sort()

    if color:
        for icon in icons:
            icon.recolor(color)

    IconCollection(icons).draw_grid(path, 8, scale=4.0)


def draw_special_grids() -> None:
    """Draw special icon grids."""
    all_icons: dict[str, IconSpecification] = {
        icon.icon_id: icon
        for icon in roentgen.icon_specifications.icon_specifications
    }

    draw_special_grid(
        all_icons,
        lambda icon: icon.icon_id.startswith("power_tower")
        or icon.icon_id.startswith("power_pole"),
        Path("doc/icons_power.svg"),
    )
    if SKIP:
        draw_special_grid(
            all_icons,
            lambda icon: icon.group == "root_space",
            Path("doc/icons_space.svg"),
        )
    draw_special_grid(
        all_icons,
        lambda icon: icon.group == "root_street_playground",
        Path("doc/icons_playground.svg"),
    )
    draw_special_grid(
        all_icons,
        lambda icon: "emergency" in icon.categories,
        Path("doc/icons_emergency.svg"),
        color=Color("#DD2222"),
    )
    draw_special_grid(
        all_icons,
        lambda icon: icon.icon_id.startswith("japan"),
        Path("doc/icons_japanese.svg"),
    )


if __name__ == "__main__":
    draw_special_grids()
