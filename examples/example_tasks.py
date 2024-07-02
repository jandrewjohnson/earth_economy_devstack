import os, sys
import hazelbean as hb
import seals.seals_utils as seals_utils
import pandas as pd
import global_invest
import numpy as np
from global_invest import ecosystem_services_functions
import dask
import example_functions
import natcap.invest
# from seals import seals_utils

def ecosystem_services(p):
    pass # Just to generate a folder

def water_yield(p):
    description = """Calculate water yield LULC maps."""
    print(description)
    

    import logging
    import sys

    import natcap.invest.annual_water_yield
    import natcap.invest.utils

    LOGGER = logging.getLogger(__name__)
    root_logger = logging.getLogger()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt=natcap.invest.utils.LOG_FMT,
        datefmt='%m/%d/%Y %H:%M:%S ')
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[handler])
        
        
        
    args = {
        'biophysical_table_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\biophysical_table_gura.csv',
        'demand_table_path': '',
        'depth_to_root_rest_layer_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\depth_to_root_restricting_layer_gura.tif',
        'eto_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\reference_ET_gura.tif',
        'lulc_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\land_use_gura.tif',
        'n_workers': '-1',
        'pawc_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\plant_available_water_fraction_gura.tif',
        'precipitation_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\precipitation_gura.tif',
        'results_suffix': '',
        'seasonality_constant': '15',
        'sub_watersheds_path': '',
        'valuation_table_path': '',
        'watersheds_path': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield\\subwatersheds_gura.shp',
        'workspace_dir': 'C:\\Users\\jajohns\\Files\\base_data\\invest_sample_data\\Annual_Water_Yield',
    }


    natcap.invest.annual_water_yield.execute(args)    
    
    
    

def another_example(p):
    description = """It wouldn't be much of a tree if it didn't branch..."""
    print(description)
    
def post_processing(p):
    description = """Post processing of the results."""
    print(description)
    

    # Load the raster
    raster_input_path = 'data/yield.tif' 
    
    
    array = example_functions.raster_to_array(raster_input_path)

    # Set no data values equal to zero

    # Method 1 (creates new array)
    array_ndv_fix = np.where(array == -9999, 0, array)

    # Method 2 (inplace)
    array[array == -9999] = 0

    # Sum the raster
    sum = np.sum(array_ndv_fix)

    # Calculate the average value on >0 cells

    ## First create a binary map of where there is positive value
    non_zero = np.where(array_ndv_fix > 0, 1, 0) 

    ## Count those
    n_non_zero = np.sum(non_zero)

    ## Calculate the average
    mean = sum / n_non_zero

    ## Write the value to a file
    with open(output_path, rw) as f: 
        print('Write here.')

    print('Sums of layers: ' + str(mean))
