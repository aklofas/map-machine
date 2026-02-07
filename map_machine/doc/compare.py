"""Compare maps with Carto."""

import argparse
import logging
import sys
from pathlib import Path
from random import random as random_random
from xml.etree.ElementTree import Element, ElementTree

import numpy as np
from svgwrite import Drawing

from map_machine.constructor import Constructor
from map_machine.geometry.bounding_box import BoundingBox
from map_machine.geometry.flinger import MercatorFlinger
from map_machine.map_configuration import (
    BuildingMode,
    MapConfiguration,
    RoadMode,
)
from map_machine.mapper import Map
from map_machine.osm.osm_getter import get_osm
from map_machine.osm.osm_reader import OSMData
from map_machine.scheme import Scheme
from map_machine.slippy.tile import Tile, Tiles
from map_machine.workspace import Workspace

workspace: Workspace = Workspace(Path("temp"))

logger: logging.Logger = logging.getLogger(__name__)

CACHE_PATH: Path = Path("work", "coordinates")


def draw(
    boundary_box: BoundingBox,
    configuration: MapConfiguration,
    output_path: Path,
) -> None:
    """Draw map."""
    cache_file_path = Path("cache") / (boundary_box.get_format() + ".osm")
    get_osm(boundary_box, cache_file_path)
    osm_data = OSMData()
    osm_data.parse_osm_file(cache_file_path)
    flinger: MercatorFlinger = MercatorFlinger(
        boundary_box, 18, osm_data.equator_length
    )

    svg: Drawing = Drawing(output_path.name, flinger.size)

    constructor: Constructor = Constructor(osm_data, flinger, configuration)
    constructor.construct()

    map_: Map = Map(flinger, svg, configuration)
    map_.draw(constructor)
    with output_path.open("w") as output_file:
        svg.write(output_file)


def _random() -> float:
    return random_random()  # noqa: S311


def _parse_coordinates(string: str) -> np.ndarray:
    if "," in string:
        pair = string.split(",")
    elif "/" in string:
        pair = string.split("/")
    else:
        raise ValueError

    return np.array(list(map(float, pair)))


def main(arguments: argparse.Namespace) -> None:
    """Draw random place."""
    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.INFO)

    point: np.ndarray | None = None

    if arguments.coordinates:
        point = _parse_coordinates(arguments.coordinates)
    elif not arguments.update:
        with CACHE_PATH.open() as input_file:
            point = _parse_coordinates(input_file.read())
    else:
        boxes: dict[str, BoundingBox] = {
            "Amsterdam": BoundingBox(4.73, 52.32, 4.94, 52.42),
            "Berlin": BoundingBox(13.29, 52.41, 13.48, 52.60),
            "Buenos Aires": BoundingBox(-58.61, -34.69, -58.35, -34.56),
            "Kinshasa": BoundingBox(15.24, -4.39, 15.33, -4.30),
            "Lubumbashi": BoundingBox(27.44, -11.70, 27.51, -11.61),
            "Los Angeles": BoundingBox(-118.41, 33.75, -117.94, 34.11),
            "Mexico": BoundingBox(-99.26, 19.28, -99.04, 19.52),
            "Moscow center": BoundingBox(37.49, 55.69, 37.73, 55.81),
            "New Delhi": BoundingBox(77.01, 28.53, 77.39, 28.74),
            "Oslo": BoundingBox(10.70, 59.90, 10.83, 59.95),
            "Praha": BoundingBox(14.32, 50.02, 14.57, 50.11),
            "Tokyo": BoundingBox(139.36, 35.67, 139.93, 36.30),
        }
        area: float = 0.0

        for box in boxes.values():
            area += (box.right - box.left) * (box.top - box.bottom)

        area_point: float = area * _random()
        current_area: float = 0.0

        for city, box in boxes.items():
            current_area += (box.right - box.left) * (box.top - box.bottom)
            if area_point < current_area:
                point = np.array(
                    (
                        box.bottom + (box.top - box.bottom) * _random(),
                        box.left + (box.right - box.left) * _random(),
                    )
                )
                logger.info(city)
                logger.info("%s,%s", str(point[0]), str(point[1]))
                break

        if point is not None:
            with CACHE_PATH.open("w") as output_file:
                output_file.write(f"{point[0]},{point[1]}")

    assert point is not None

    tile_1: Tile = Tile.from_coordinates(point, 18)
    x, y = tile_1.x, tile_1.y
    tile_2: Tile = Tile(x + 2, y + 1, 18)

    tile_3: Tile = Tile(x + 3, y + 2, 18)
    p1 = tile_1.get_coordinates()
    p2 = tile_3.get_coordinates()
    p = (p1 + p2) / 2
    logger.info(p)
    logger.info("https://www.openstreetmap.org/edit#map=18/%s/%s", p[0], p[1])
    logger.info(
        "map-machine render -o out/random.html --scheme carto "
        "-s 768,512 -c %s/%s --tooltips",
        p[0],
        p[1],
    )

    boundary_box: BoundingBox = tile_1.get_bounding_box()
    boundary_box.combine(tile_2.get_bounding_box())

    tile_list: list[Tile] = [
        Tile(i, j, 18) for j in (y, y + 1) for i in (x, x + 1, x + 2)
    ]

    tiles: Tiles = Tiles(tile_list, tile_1, tile_2, 18, boundary_box)
    osm_data: OSMData = tiles.load_osm_data(Path("cache"))

    for scheme_id in ("default", "carto"):
        scheme: Scheme = Scheme.from_file(
            workspace.SCHEME_PATH / f"{scheme_id}.yml"
        )
        configuration: MapConfiguration = MapConfiguration(
            scheme,
            show_tooltips=True,
            ignore_level_matching=True,
            level="all",
            show_overlapped=True,
            road_mode=RoadMode.SIMPLE,
            building_mode=BuildingMode.ISOMETRIC,
        )
        tiles.draw(
            Path("out/tiles"),
            Path("cache"),
            configuration,
            osm_data,
            redraw=True,
        )

        def write_page(*, is_osm: bool, output_path: Path) -> None:
            """Write HTML page with the map."""
            root: Element = Element("html")
            table: Element = Element("table")
            table.set("style", "border-collapse: collapse;")
            root.append(table)

            for j in y, y + 1:
                table_row: Element = Element("tr")
                table.append(table_row)
                for i in x, x + 1, x + 2:
                    tile: Tile = Tile(i, j, 18)
                    table_cell: Element = Element("td")
                    table_cell.set("style", "padding: 0; margin: 0;")
                    table_row.append(table_cell)

                    img: Element = Element("img")
                    address: str
                    if is_osm:
                        address = tile.get_carto_address()
                    else:
                        address = "../" + str(
                            tile.get_file_name(Path("out/tiles")).with_suffix(
                                ".png"
                            )
                        )
                    img.set("src", address)
                    table_cell.append(img)

            with output_path.open("wb+") as output_file:
                ElementTree(root).write(output_file)

        draw(
            tiles.bounding_box,
            configuration,
            Path(f"out/random_{scheme_id}.html"),
        )
        write_page(is_osm=True, output_path=Path("out/random_osm.html"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--coordinates")
    parser.add_argument("-u", "--update", action=argparse.BooleanOptionalAction)
    main(parser.parse_args(sys.argv[1:]))
