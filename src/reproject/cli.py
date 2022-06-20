import json
import os
from typing import Optional

import click

from reproject.reproject import reproject_geometry


@click.command()
@click.argument("INFILE")
@click.argument("SRC_CRS")
@click.argument("DST_CRS")
@click.argument("TOLERANCE")
@click.option("-o", "--outfile", help="File path for reprojected geojson")
def cli(
    infile: str,
    src_crs: str,
    dst_crs: str,
    tolerance: float,
    outfile: Optional[str] = None,
) -> None:
    """Reprojects a Polygon in a GeoJSON file.

    \b
    Args:
        infile (str): Path to file containing the GeoJSON Polygon
        src_crs (str): Source CRS string, e.g., an EPSG code or WKT
        dst_crs (str): Destination CRS string
        dst_tolerance (float): Maximum acceptable "error" of the reprojected
            Polygon in the destination CRS linear unit.
        outfile (str, optional): File path for the reprojected GeoJSON Polygon.
            If not specified, the file will be saved alongside the INFILE.
    """
    with open(infile, "r") as filein:
        geometry = json.load(filein)

    reprojected_geometry = reproject_geometry(
        geometry, src_crs=src_crs, dst_crs=dst_crs, dst_tolerance=float(tolerance)
    )

    if not outfile:
        outfile = f"{os.path.splitext(infile)[0]}-reprojected.json"
    with open(outfile, "w") as fileout:
        json.dump(reprojected_geometry, fileout)
