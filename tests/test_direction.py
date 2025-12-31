"""Test direction processing."""

import numpy as np

from map_machine.feature.direction import DirectionSet, Sector, parse_vector

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


def test_compass_points_1() -> None:
    """Test north direction."""
    vector: np.ndarray | None = parse_vector("N")
    assert vector is not None
    assert np.allclose(vector, np.array([0, -1]))


def test_compass_points_2() -> None:
    """Test north-west direction."""
    root: np.float64 = -np.sqrt(2) / 2
    vector: np.ndarray | None = parse_vector("NW")
    assert vector is not None
    assert np.allclose(vector, np.array([root, root]))


def test_compass_points_3() -> None:
    """Test south-south-west direction."""
    vector: np.ndarray | None = parse_vector("SSW")
    assert vector is not None
    assert np.allclose(vector, np.array([-0.38268343, 0.92387953]))


def test_invalid() -> None:
    """Test invalid direction representation string."""
    assert not parse_vector("O")


def test_degree() -> None:
    """Test east direction."""
    vector: np.ndarray | None = parse_vector("90")
    assert vector is not None
    assert np.allclose(vector, np.array([1, 0]))


def test_main_direction() -> None:
    """Test main direction computing."""
    assert DirectionSet("0").is_right() is None
    assert DirectionSet("70").is_right() is True
    assert DirectionSet("270").is_right() is False
    assert DirectionSet("180").is_right() is None


def test_sector_parsing() -> None:
    """Test constructing sector from the string representation."""
    Sector("0", angle=0)
    Sector("90", angle=0)
    Sector("-90", angle=0)

    sector: Sector = Sector("0-180")
    assert sector.start is not None
    assert sector.end is not None
    assert np.allclose(sector.start, [0, -1])
    assert np.allclose(sector.end, [0, 1])
