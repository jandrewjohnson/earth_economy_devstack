import os
import pandas as pd
import hazelbean as hb

from global_invest.terrestrial_carbon import terrestrial_carbon_initialization

if __name__ == '__main__':

    # ProjectFlow object
    p = hb.ProjectFlow() # Create a ProjectFlow Object to organize directories and enable parallel processing.
    p.project_name = 'gep_terrestrial_carbon'  # Determines the folder created to store intermediate and final results.
    p.project_dir = os.path.join(os.path.expanduser('~'), 'Files', 'global_invest', 'projects', p.project_name) # Put it in the right location relative to the user's home directory.
    p.base_data_dir = "/Users/long/Library/CloudStorage/GoogleDrive-yxlong@umn.edu/Shared drives/NatCapTEEMs/Files/base_data/submissions" # Set where data outside the project will be stored. CAUTION: For GEP we are using the shared Google Drive, but best practice is to use a local directory that you can control (also it's faster)
    p.set_project_dir(p.project_dir) # Set the project directory in the ProjectFlow object. Also defines p.input_dir, p.intermediate_dir, and p.output_dir based on the project_dir.

    # Task tree
    terrestrial_carbon_initialization.build_gep_service_task_tree(p) # Defines the actual logic of the model. Navigate into here to see what the model does.

    # Project level attributes
    p.df_countries_csv_path = p.get_path('cartographic', 'ee', 'ee_r264_correspondence.csv') # ProjectFlow downloads all files automatically via the p.get_path() function.
    p.gdf_countries_vector_path = p.get_path('cartographic', 'ee', 'ee_r264_correspondence.gpkg')
    p.gdf_countries_vector_simplified_path = p.get_path('cartographic', 'ee', 'ee_r264_simplified300sec.gpkg')
    p.carbon_zones_path =os.path.join(p.base_data_dir,'carbon', 'johnson_2019', 'decision_tree_combined_carbon', 'carbon_zones_rasterized.tif')
    p.projected_carbon_density_2019_per_cell_path = os.path.join(p.project_dir, 'projected_carbon_density_maps_per_cell/projected_carbon_density_2019_per_cell.tif')
    p.lulc_folder_path = os.path.join(p.base_data_dir, 'lulc/esa')
    p.base_year_lulc_path = os.path.join(p.base_data_dir, 'lulc/esa/lulc_esa_2019.tif')
    p.carbon_prices_path = os.path.join(p.base_data_dir, 'terrestrial_carbon', 'carbon_prices.xlsx')
    p.carbon_price = "rental scc r2%"
    p.results = {}  # All results will be stored here by each child task.
    terrestrial_carbon_initialization.initialize_paths(p)

    # Run the model
    hb.log('Created ProjectFlow object at ' + p.project_dir + '\n    from script ' + p.calling_script + '\n    with base_data set at ' + p.base_data_dir)
    p.execute()

    result = 'Done!'
