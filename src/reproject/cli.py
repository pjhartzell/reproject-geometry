import json
import os
from typing import Optional

import click

from reproject.reproject import DEFAULT_PRECISION, reproject_geometry


@click.command()
@click.argument("INFILE")
@click.argument("SRC_CRS")
@click.argument("DST_CRS")
@click.option(
    "-t", "--tolerance", help="Destination geometry error tolerance", type=float
)
@click.option(
    "-p",
    "--precision",
    help="Number of decimal places in output coords",
    type=int,
    default=DEFAULT_PRECISION,
)
@click.option("-o", "--outfile", help="File path for reprojected geojson")
def cli(
    infile: str,
    src_crs: str,
    dst_crs: str,
    tolerance: Optional[float] = None,
    precision: int = DEFAULT_PRECISION,
    outfile: Optional[str] = None,
) -> None:
    """Reprojects a Polygon in a GeoJSON file.

    \b
    Args:
        infile (str): Path to file containing a GeoJSON Polygon
        src_crs (str): Source CRS string, e.g., an EPSG code or WKT
        dst_crs (str): Destination CRS string
        dst_tolerance (float, optional): Maximum acceptable "error" of the
            reprojected geometry in the destination CRS linear unit. If not
            specified, the source geometry will be reprojected without any
            densification.
        precision (int, optional): The number of decimal places to include in
            the coordinates for the reprojected geometry. Defaults to 3 decimal
            places.
        outfile (str, optional): GeoJSON file path for the reprojected geometry.
            If not specified, the file will be saved alongside the INFILE.
    """
    with open(infile, "r") as filein:
        geometry = json.load(filein)

    reprojected_geometry = reproject_geometry(
        geometry,
        src_crs=src_crs,
        dst_crs=dst_crs,
        dst_tolerance=tolerance,
        precision=precision,
    )

    if not outfile:
        outfile = f"{os.path.splitext(infile)[0]}-reprojected.json"
    with open(outfile, "w") as fileout:
        json.dump(reprojected_geometry, fileout)
