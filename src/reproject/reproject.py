from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from rasterio import warp
from rasterio.crs import CRS
from shapely.geometry import MultiPolygon, Polygon, mapping, shape

DEFAULT_PRECISION = 3


def reproject_geometry(
    geojson: Dict[str, Any],
    src_crs: str,
    dst_crs: str,
    dst_tolerance: Optional[float],
    precision: int = DEFAULT_PRECISION,
) -> Dict[str, Any]:
    """Reprojects a GeoJSON-like geometry from a source to destination CRS with
    the option to limit reprojection error to approximately dst_tolerance.

    If dst_tolerance is specified, additional vertices are inserted into the
    geometry polygon(s) prior to reprojection to capture projection distortion.
    The projected geometries are then simplified by removing vertices until the
    simplificaton imparts an error that exceeds dst_tolerance. The supplied
    dst_tolerance must be in the linear unit (e.g., meters, feet, degrees) of
    the destination CRS.

    Args:
        geojson (Dict[str, Any]): A GeoJSON-like dictionary containing a
            polygon or multipolygon to be reprojected.
        src_crs (str): Source CRS string, e.g., an EPSG code or WKT2.
        dst_crs (str): Destination CRS string.
        dst_tolerance (float, optional): Maximum acceptable "error" of the
            reprojected Polygon(s) in the destination CRS. Must be in the linear
            unit of the destination CRS.
        precision (int, optional): The number of decimal places to include in
            the coordinates for the reprojected geometry. Defaults to 3 decimal
            places.

    Returns:
         Dict[str, Any]: A GeoJSON-like dictionary containg the reprojected
            Polygon(s)
    """
    geometry = shape(geojson)
    if isinstance(geometry, Polygon):
        multipolygon = False
    elif isinstance(geometry, MultiPolygon):
        multipolygon = True
    else:
        raise ValueError(
            f"Can only reproject Polygons or MultiPolygons, geometry={geometry}"
        )

    if multipolygon:
        reprojected_geometry = reproject_multipolygon(
            geometry, src_crs, dst_crs, dst_tolerance, precision
        )
    else:
        reprojected_geometry = reproject_polygon(
            geometry, src_crs, dst_crs, dst_tolerance, precision
        )

    result: Dict[str, Any] = mapping(reprojected_geometry)
    return result


def reproject_multipolygon(
    multipolygon: MultiPolygon,
    src_crs: str,
    dst_crs: str,
    dst_tolerance: Optional[float],
    precision: int = DEFAULT_PRECISION,
) -> MultiPolygon:
    """Reprojects each polygon in a multipolygon from a source to destination
    CRS with the option to limit reprojection error to approximately
    dst_tolerance.

    If dst_tolerance is specified, additional vertices are inserted into the
    geometry polygon(s) prior to reprojection to capture projection distortion.
    The projected geometries are then simplified by removing vertices until the
    simplificaton imparts an error that exceeds dst_tolerance. The supplied
    dst_tolerance must be in the linear unit (e.g., meters, feet, degrees) of
    the destination CRS.

    Args:
        multipolygon (MultiPolygon): The multipolygon to be reprojected.
        src_crs (str): Source CRS string, e.g., an EPSG code or WKT2.
        dst_crs (str): Destination CRS string.
        dst_tolerance (float, optional): Maximum acceptable "error" of the
            reprojected Polygon(s) in the destination CRS. Must be in the linear
            unit of the destination CRS.
        precision (int, optional): The number of decimal places to include in
            the coordinates for the reprojected geometry. Defaults to 3 decimal
            places.

    Returns:
        MultiPolygon: The reprojected multipolygon
    """
    polygons = []
    for polygon in multipolygon.geoms:
        polygons.extend(
            reproject_polygon(polygon, src_crs, dst_crs, dst_tolerance, precision)
        )
    return MultiPolygon(polygons)


def reproject_polygon(
    polygon: Polygon,
    src_crs: str,
    dst_crs: str,
    dst_tolerance: Optional[float],
    precision: int = DEFAULT_PRECISION,
) -> Polygon:
    """Reprojects a polygon from a source to destination CRS with the option to
    limit reprojection error to approximately dst_tolerance.

    If dst_tolerance is specified, additional vertices are inserted into the
    geometry polygon(s) prior to reprojection to capture projection distortion.
    The projected geometries are then simplified by removing vertices until the
    simplificaton imparts an error that exceeds dst_tolerance. The supplied
    dst_tolerance must be in the linear unit (e.g., meters, feet, degrees) of
    the destination CRS.

    Args:
        polygon (Polygon): The polygon to be reprojected.
        src_crs (str): Source CRS string, e.g., an EPSG code or WKT2.
        dst_crs (str): Destination CRS string.
        dst_tolerance (float, optional): Maximum acceptable "error" of the
            reprojected Polygon(s) in the destination CRS. Must be in the linear
            unit of the destination CRS.
        precision (int, optional): The number of decimal places to include in
            the coordinates for the reprojected geometry. Defaults to 3 decimal
            places.

    Returns:
        Polygon: The reprojected polygon
    """

    if dst_tolerance is not None:
        src_bbox = polygon.bounds
        src_tolerance = _src_tol(src_crs, src_bbox, dst_crs, dst_tolerance)
        polygon = Polygon(_densify_by_distance(polygon.exterior.coords, src_tolerance))

    polygon = shape(warp.transform_geom(src_crs, dst_crs, polygon, precision=precision))

    if dst_tolerance is not None:
        return polygon.simplify(dst_tolerance).simplify(0)
    else:
        return polygon.simplify(0)


def _src_tol(
    src_crs: str, src_bbox: List[float], dst_crs: str, dst_tol: float
) -> float:
    """Converts a tolerance (a distance) from a source CRS linear unit to a
    destination CRS linear unit.

    Longitudinal ground distances vary with latitude, which means the conversion
    of the tolerance (distance) between destination and source units also varies
    with latitude. A mid-latitude value of the bounding box is therefore used to
    'average' this discrepancy when converting between geographic and projected
    units. Since this is not an exact computation, a spherical approximation is
    used for the shape of the Earth for simplicity.

    Args:
        src_crs (str): CRS of the source geometry.
        src_bbox (List[float]): Bounding box of the geometry in the source CRS.
        dst_crs (str): CRS of the destination geometry.
        dst_tolerance (float, optional): Maximum acceptable "error" of the
            reprojected Polygon(s) in the destination CRS. Must be in the linear
            unit of the destination CRS.

    Returns:
        float: The destination tolerance (distance) in the source CRS linear
            units.
    """
    d_crs = CRS.from_string(dst_crs)
    s_crs = CRS.from_string(src_crs)

    src_tol: float
    if s_crs.is_geographic and d_crs.is_geographic:
        src_tol = dst_tol
    elif s_crs.is_projected and d_crs.is_projected:
        src_tol = (
            d_crs.linear_units_factor[1] / s_crs.linear_units_factor[1]
        ) * dst_tol
    elif s_crs.is_projected and d_crs.is_geographic:
        dst_bbox = warp.transform_bounds(src_crs, dst_crs, *src_bbox)
        mid_latitude = (dst_bbox[1] + dst_bbox[3]) / 2
        meters_per_degree = 111320 * np.cos(np.deg2rad(mid_latitude))
        meters_per_src_unit = s_crs.linear_units_factor[1]
        src_units_per_degree = meters_per_degree / meters_per_src_unit
        tol_src_units = src_units_per_degree * dst_tol
        src_tol = tol_src_units
    elif s_crs.is_geographic and d_crs.is_projected:
        mid_latitude = (src_bbox[1] + src_bbox[3]) / 2
        meters_per_degree = 111320 * np.cos(np.deg2rad(mid_latitude))
        meters_per_dst_unit = d_crs.linear_units_factor[1]
        tol_meters = meters_per_dst_unit * dst_tol
        tol_degree = tol_meters / meters_per_degree
        src_tol = tol_degree
    return src_tol


def _densify_by_distance(
    point_list: List[Tuple[float, float]], densification_length: float
) -> List[Tuple[float, float]]:
    """Densifies the number of points in a list of points by inserting points
    at densification_length intervals along the polygon formed by the points.

    Args:
        point_list (List[Tuple[float, float]]): The list of points to be
            densified.
        densification_length (int): The interval at which to insert additional
            points.

    Returns:
        List[Tuple[float, float]]: The list of densified points.
    """
    points: Any = np.asarray(point_list)

    dxdy = points[1:, :] - points[:-1, :]
    segment_lengths = np.sqrt(np.sum(np.square(dxdy), axis=1))
    total_length = np.sum(segment_lengths)

    cum_segment_lengths = np.cumsum(segment_lengths)
    cum_segment_lengths = np.insert(cum_segment_lengths, 0, [0])
    cum_interp_lengths = np.arange(0, total_length, densification_length)
    cum_interp_lengths = np.append(cum_interp_lengths, [total_length])

    interp_x = np.interp(cum_interp_lengths, cum_segment_lengths, points[:, 0])
    interp_y = np.interp(cum_interp_lengths, cum_segment_lengths, points[:, 1])

    return [(x, y) for x, y in zip(interp_x, interp_y)]
