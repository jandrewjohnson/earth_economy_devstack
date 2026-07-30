# Copyright (c) 2025, Yanxu Long
# This file is part of the Global GEP project: carbon storage and sequestration

import os, sys
import hazelbean as hb
import pandas as pd

from global_invest.carbon import carbon_tasks

# Create the project flow object
p = hb.ProjectFlow()

# Set project-directories
p.user_dir = os.path.expanduser('~')
p.extra_dirs = ['Files', 'global_invest', 'projects']
p.project_name = p.project_name + '_' + hb.pretty_time() # Comment this line out if you want it to use an existing project. Will skip recreation of files that already exist.
p.project_dir = os.path.join(p.user_dir, os.sep.join(p.extra_dirs), p.project_name)
p.set_project_dir(p.project_dir)

# Set basa_data_dir. Will download required files here.
p.base_data_dir = "/Users/long/Library/CloudStorage/GoogleDrive-yxlong@umn.edu/Shared drives/NatCapTEEMs/Files/base_data/submissions/carbon/spawn_2020"
# p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data') # Uncomment this line if you want to use the default base_data_dir

# Set model-paths
p.aoi = 'global' #p.aoi = 'RWA'
p.base_year_lulc_path = p.get_path(os.path.join(p.base_data_dir,'lulc/esa/lulc_esa_2019.tif')) # Defines the fine_resolution
p.all_lulcs_path = p.get_path(os.path.join(p.base_data_dir, 'lulc/esa')) # Defines the all_lulcs
p.carbon_zones_path = p.get_path(os.path.join(p.base_data_dir,'carbon_zones_rasterized.tif')) # Defines the carbon zones
p.region_boundary_path = p.get_path(os.path.join(p.base_data_dir,'ee_r264_correspondence.gpkg'))

def build_task_tree(p):
    p.task_print_hello = p.add_task(carbon_tasks.task_print_hello)
    p.task_convert_carbon_density_maps_dtype = p.add_task(carbon_tasks.task_convert_carbon_density_maps_dtype)
    p.task_combine_two_carbon_density_maps = p.add_task(carbon_tasks.task_combine_two_carbon_density_maps)
    p.task_reproject_total_carbon_density = p.add_task(carbon_tasks.task_reproject_total_carbon_density)
    p.task_compute_carbon_density_table = p.add_task(carbon_tasks.task_compute_carbon_density_table)
    p.task_generate_carbon_density_raster_base_year = p.add_task(carbon_tasks.task_generate_carbon_density_raster_base_year)
    p.task_summarize_carbon_density_by_region = p.add_task(carbon_tasks.task_summarize_carbon_density_by_region)

# Build the task tree and excute it!
build_task_tree(p)
p.fail_fast = True
p.verbosity = 2
p.debug = True
p.execute()











