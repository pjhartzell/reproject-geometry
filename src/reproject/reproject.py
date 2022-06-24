from typing import Any, Dict, List

import numpy as np
import shapely.geometry
from rasterio import features, warp
from rasterio.crs import CRS


def nearest_multiple(number: float, multiple: float) -> float:
    """Rounds a number to the nearest multiple.

    Args:
        number (float): Number to be rounded
        multiple (float): Multiple to which the number will be rounded

    Returns:
        float: Rounded number
    """
    return multiple * round(number / multiple)


def src_tol(src_crs: str, src_bbox: List[float], dst_crs: str, dst_tol: float) -> float:
    """Converts a tolerance from destination to source units.

    Noting that longitudinal ground distances vary with latitude, we use
    the mid-latitude value of the bounding box to convert between geographic
    and projected distances. We also use a spherical approximation for the shape
    of the Earth.

    Args:
        src_crs (str): CRS of the source geometry
        src_bbox (List[float]): Bounding box of the geometry in the source CRS
        dst_crs (str): CRS of the destination geometry
        dst_tol (float): Desired maximum error (dst_tolerance) of the geometry
            after reprojection to the destination CRS

    Returns:
        float: Maximum error (dst_tolerance) in the source CRS linear units
    """
    d_crs = CRS.from_string(dst_crs)
    s_crs = CRS.from_string(src_crs)

    s_tol: float
    if s_crs.is_geographic and d_crs.is_geographic:
        s_tol = dst_tol
    elif s_crs.is_projected and d_crs.is_projected:
        s_tol = (d_crs.linear_units_factor[1] / s_crs.linear_units_factor[1]) * dst_tol
    elif s_crs.is_projected and d_crs.is_geographic:
        dst_bbox = warp.transform_bounds(src_crs, dst_crs, *src_bbox)
        mid_latitude = (dst_bbox[1] + dst_bbox[3]) / 2
        meters_per_degree = 111320 * np.cos(np.deg2rad(mid_latitude))
        meters_per_src_unit = s_crs.linear_units_factor[1]
        src_units_per_degree = meters_per_degree / meters_per_src_unit
        tol_src_units = src_units_per_degree * dst_tol
        s_tol = tol_src_units
    elif s_crs.is_geographic and d_crs.is_projected:
        mid_latitude = (src_bbox[1] + src_bbox[3]) / 2
        meters_per_degree = 111320 * np.cos(np.deg2rad(mid_latitude))
        meters_per_dst_unit = d_crs.linear_units_factor[1]
        tol_meters = meters_per_dst_unit * dst_tol
        tol_degree = tol_meters / meters_per_degree
        s_tol = tol_degree
    return s_tol


def reproject_geometry(
    geojson: Dict[str, Any], src_crs: str, dst_crs: str, dst_tolerance: float
) -> Dict[str, Any]:
    """Reprojects a shapely Polygon from a source to destination CRS.

    The reprojected geometry contains additional vertices to bound reprojection
    distortion errors to within the specified tolerance. The supplied tolerance
    must be in the linear unit (e.g., meters, feet, degrees) of the destination
    CRS.

    TODO:
        1. Handle MultiPolygons.
        2. Merge exactly reprojected original vertices with the approximated
            additional vertices for cleaner results.

    Args:
        geometry (Dict[str, Any]): A geojson-like dictionary containing a
            Polygon to be reprojected
        src_crs (str): Source CRS string, e.g., an EPSG code or WKT
        dst_crs (str): Destination CRS string
        dst_tolerance (float): Maximum acceptable "error" of the reprojected
            Polygon in the destination CRS linear unit.

    Returns:
        Dict[str, Any]: _description_
    """
    geometry = shapely.geometry.shape(geojson)
    if not isinstance(geometry, shapely.geometry.Polygon):
        raise ValueError(f"Can only reproject Polygons, geometry={geometry}")

    bbox = geometry.bounds
    src_tolerance = src_tol(src_crs, bbox, dst_crs, dst_tolerance)

    cell_size = src_tolerance / 2
    xmin = nearest_multiple(bbox[0] - (2 * src_tolerance), cell_size)
    ymin = nearest_multiple(bbox[1] - (2 * src_tolerance), cell_size)
    xmax = nearest_multiple(bbox[2] + (2 * src_tolerance), cell_size)
    ymax = nearest_multiple(bbox[3] + (2 * src_tolerance), cell_size)

    num_rows = int((ymax - ymin) / cell_size)
    num_cols = int((xmax - xmin) / cell_size)
    src_transform = [cell_size, 0.0, xmin, 0.0, -cell_size, ymax]
    # maybe raise an error if the array size will be very large (before creating)
    src_raster: Any = np.zeros((num_rows, num_cols), dtype=np.uint8)

    features.rasterize(
        [(geometry)], out=src_raster, transform=src_transform, default_value=255
    )

    dst_transform, dst_width, dst_height = warp.calculate_default_transform(
        src_crs,
        dst_crs,
        width=num_cols,
        height=num_rows,
        left=xmin,
        bottom=ymin,
        right=xmax,
        top=ymax,
    )
    dst_raster: Any = np.zeros((dst_height, dst_width), dtype=np.uint8)
    warp.reproject(
        src_raster,
        dst_raster,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=warp.Resampling.nearest,
    )

    shapes = features.shapes(dst_raster, transform=dst_transform)
    for poly, val in shapes:
        if val == 255:
            shape = shapely.geometry.shape(poly).simplify(dst_tolerance)

    reprojected_geometry: Dict[str, Any] = shapely.geometry.mapping(shape)
    return reprojected_geometry


# import json
# if __name__ == "__main__":
#     src_crs = "PROJCS[\"unnamed\",GEOGCS[\"Unknown datum based upon the custom spheroid\",DATUM[\"Not specified (based on custom spheroid)\",SPHEROID[\"Custom spheroid\",6371007.181,0]],PRIMEM[\"Greenwich\",0],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]]],PROJECTION[\"Sinusoidal\"],PARAMETER[\"longitude_of_center\",0],PARAMETER[\"false_easting\",0],PARAMETER[\"false_northing\",0],UNIT[\"Meter\",1],AXIS[\"Easting\",EAST],AXIS[\"Northing\",NORTH]]"  # noqa
#     dst_crs = "EPSG:4326"
#     geojson_file = "tests/data-file/viirs_h11v05_sinusoidal.json"
#     dst_tolerance = 0.01

#     with open(geojson_file, "r") as infile:
#         geojson = json.load(infile)

#     reprojected_geojson = reproject_geometry(geojson, src_crs, dst_crs, dst_tolerance)

#     with open("reprojected.json", "w") as outfile:
#         json.dump(reprojected_geojson, outfile)
