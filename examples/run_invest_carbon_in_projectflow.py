"""Example: run the global_invest InVEST carbon task tree in a ProjectFlow."""
import os
import hazelbean as hb

from global_invest import ecosystem_services_tasks
from global_invest import ecosystem_services_functions


def build_task_tree(p):
    p.project_aoi_task = p.add_task(ecosystem_services_tasks.project_aoi) # Clips the global_regions_vector to the aoi selected
    p.aoi_inputs_task = p.add_task(ecosystem_services_tasks.aoi_inputs) # Clips global inputs based on the aoi
    p.ecosystem_services_task = p.add_task(ecosystem_services_tasks.ecosystem_services) # Empty task just to contain all the other ES tasks (by being set as their parent task)
    p.carbon_storage_biophysical_invest_task = p.add_task(ecosystem_services_tasks.carbon_storage_biophysical_invest, parent=p.ecosystem_services_task) # Actually implements the model logic


def run_project(project_name='test_global_invest', append_timestamp=False,
                tasks_to_skip=None, execute=True):
    """Build and execute the example InVEST carbon task tree.

    append_timestamp=True gives each run a fresh project dir (the spec preference is a
    stable, resumable dir with append_timestamp=False). Returns p.
    """
    p = hb.ProjectFlow()

    # Set project-directories
    p.user_dir = os.path.expanduser('~') # EE Devstack is defined relative to the user's directory, but could be overwritten if running not for the Devstack.
    p.extra_dirs = ['Files', 'global_invest', 'projects'] # Extra directories used inside the user_dir
    p.project_name = project_name # Name of the project, which will be used to create the project_dir
    if append_timestamp:
        p.project_name = p.project_name + '_' + hb.pretty_time()
    p.project_dir = os.path.join(p.user_dir, os.sep.join(p.extra_dirs), p.project_name) # Combines above to set the user_dir.
    p.set_project_dir(p.project_dir) # Based on the project_dir, create all other relevant dirs, like input, intermediate, and output.

    # Set base_data_dir. Will download required files here.
    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data') # Could be anywhere, including external storage. But, should not be cloud-controlled (like Google Drive).

    # Set model-paths and details
    p.aoi = 'RWA'
    p.base_year_lulc_path = p.get_path('lulc/esa/lulc_esa_2017.tif') # Defines the fine_resolution
    p.region_ids_coarse_path = p.get_path('cartographic/ee/id_rasters/eemarine_r566_ids_900sec.tif') # Defines the coarse_resolution
    p.global_regions_vector_path = p.get_path('cartographic/ee/eemarine_r566_correspondence.gpkg') # Will be used to create the aoi vector

    build_task_tree(p)
    p.skip_tasks(tasks_to_skip)

    p.L = hb.get_logger('invest_carbon_in_projectflow')
    hb.log('Created ProjectFlow object at ' + p.project_dir)

    if execute:
        p.execute()

    return p


if __name__ == '__main__':
    run_project(append_timestamp=True)
