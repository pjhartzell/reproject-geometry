import json

from reproject_geometry.reproject import reproject_geometry


def test_sinusoidal_to_wgs84_densify() -> None:
    src_crs = 'PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid",6371007.181,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Sinusoidal"],PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'  # noqa
    dst_crs = "EPSG:4326"
    geojson_file = (
        "tests/data-files/VNP09A1.A2022145.h11v05.001.2022154194417_sinusoidal.json"
    )
    dst_tolerance = 0.01
    check_coords = [
        [-91.3785, 40.0],
        [-89.8853, 38.8519],
        [-88.4164, 37.6546],
        [-86.977, 36.4081],
        [-85.6841, 35.219],
        [-84.416, 33.9807],
        [-83.1544, 32.6686],
        [-81.958, 31.34],
        [-80.8317, 30.0033],
        [-69.2831, 30.0016],
        [-70.2484, 31.3383],
        [-71.2738, 32.6668],
        [-72.3481, 33.9707],
        [-73.4271, 35.2008],
        [-74.5973, 36.4555],
        [-75.7837, 37.6528],
        [-77.0604, 38.8666],
        [-78.3224, 39.9983],
        [-91.3785, 40.0],
    ]

    with open(geojson_file, "r") as infile:
        geojson = json.load(infile)
    reprojected_geojson = reproject_geometry(
        geojson, src_crs, dst_crs, dst_tolerance, precision=4
    )

    _type = reprojected_geojson["type"]
    assert _type == "Polygon"
    coords = reprojected_geojson["coordinates"][0]
    for (xc, yc), (xt, yt) in zip(coords, check_coords):
        assert xc == xt
        assert yc == yt


def test_utm_to_wgs84_simplify() -> None:
    src_crs = "EPSG:32619"
    dst_crs = "EPSG:4326"
    geojson_file = (
        "tests/data-files/HLS.S30.T19LDD.2022166T144741.v2.0.B09_epsg_32619.json"
    )
    dst_tolerance = 0.001

    with open(geojson_file, "r") as infile:
        geojson = json.load(infile)
    reprojected_geojson = reproject_geometry(
        geojson, src_crs, dst_crs, dst_tolerance, precision=4
    )

    _type = reprojected_geojson["type"]
    coords = reprojected_geojson["coordinates"]
    assert _type == "Polygon"
    assert len(coords[0]) == 5


def test_multipolygon() -> None:
    pass
