import pytest

from reproject.reproject import src_tol


def test_geographic_to_geographic() -> None:
    src_crs = "EPSG:4326"  # WGS84
    src_bbox = [-72.0, 43.0, -71.0, 44.0]
    dst_crs = "EPSG:4269"  # NAD83
    dst_tol = 1.0
    src_tolerance = src_tol(src_crs, src_bbox, dst_crs, dst_tol)
    assert src_tolerance == dst_tol


def test_projected_to_projected() -> None:
    src_crs = "EPSG:6525"  # New Hampshire State Plane, USFT
    src_bbox = [895078.8, 182401.2, 1159673.0, 547429.8]
    dst_crs = "EPSG:32619"  # UTM, meter
    dst_tol = 1.0
    src_tolerance = src_tol(src_crs, src_bbox, dst_crs, dst_tol)
    assert src_tolerance == pytest.approx(3.280833333333333)


def test_projected_to_geographic() -> None:
    src_crs = "EPSG:32619"  # UTM, meter
    src_bbox = [255466.9, 4765182.9, 339650.5, 4873817.3]
    dst_crs = "EPSG:4326"  # WGS84
    dst_tol = 1.0
    src_tolerance = src_tol(src_crs, src_bbox, dst_crs, dst_tol)
    assert src_tolerance == pytest.approx(80748.67540991119)


def test_geographic_to_projected() -> None:
    src_crs = "EPSG:4326"  # WGS84
    src_bbox = [-72.0, 43.0, -71.0, 44.0]
    dst_crs = "EPSG:32619"  # UTM, meter
    dst_tol = 100000.0
    src_tolerance = src_tol(src_crs, src_bbox, dst_crs, dst_tol)
    assert src_tolerance == pytest.approx(1.2384104138355332)
