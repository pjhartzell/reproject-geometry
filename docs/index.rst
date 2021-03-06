.. Reproject Geometry documentation master file, created by
   sphinx-quickstart on Fri Jul 29 05:24:40 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Reproject Geometry Docs
==============================================

Reproject Geometry is a utility for transforming GeoJSON Polygon and MultiPolygon 
geometries from one Coordinate Reference System (CRS) to another. The intended use
case is transforming a geometry from projected CRS coordinates (northing, easting)
to geographic WGS84 coordinates (latitude, longitude). However, reprojection is
possible between any source and destination CRS supported by rasterio's `crs 
module <https://rasterio.readthedocs.io/en/latest/api/rasterio.crs.html>`_.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Contents:

   api.rst

API Reference
-------------

:doc:`api`

Installation
------------

.. code-block:: shell

   $ pip install git+https://github.com/pjhartzell/reproject-geometry

Command Line
------------

.. code-block:: shell

   $ reproject --help
   Usage: reproject [OPTIONS] INFILE SRC_CRS DST_CRS

   Reprojects a Polygon in a GeoJSON file.

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

   Options:
   -t, --tolerance FLOAT    Destination geometry error tolerance
   -p, --precision INTEGER  Number of decimal places in output coords
   -o, --outfile TEXT       File path for reprojected geojson
   --help                   Show this message and exit.
