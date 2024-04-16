import os
import hazelbean as hb
from osgeo import gdal
import numpy as np


def execute_water_yield(args):
    description = """Actual execution of the invest water yield model"""

def raster_to_array(raster_input_path):
    ds = gdal.Open(raster_input_path)
    print("Reading " + raster_input_path +'. This might take a while!')
    array = ds.ReadAsArray()
    return array

