"""Example: run the global_invest InVEST carbon task tree in a ProjectFlow.

    Configuration: level 2 of 4 -- a task tree, no CSVs; p.aoi is the variant knob
    Code layout:   library package -- tasks come from global_invest
    Ownership:     devstack developer -- global_invest is imported, and you could edit it

run_project(p) sets what no variant ever changes; the caller sets what a variant
might. See examples/run_templates_annotated/ for the fully documented form of
this convention, and examples/run_templates/ for a copy-me version.
"""
import os
import hazelbean as hb

from global_invest import ecosystem_services_tasks
from global_invest import ecosystem_services_functions


def build_task_tree(p):
    p.project_aoi_task = p.add_task(ecosystem_services_tasks.project_aoi) # Clips the global_regions_vector to the aoi selected
    p.aoi_inputs_task = p.add_task(ecosystem_services_tasks.aoi_inputs) # Clips global inputs based on the aoi
    p.ecosystem_services_task = p.add_task(ecosystem_services_tasks.ecosystem_services) # Empty task just to contain all the other ES tasks (by being set as their parent task)
    p.carbon_storage_biophysical_invest_task = p.add_task(ecosystem_services_tasks.carbon_storage_biophysical_invest, parent=p.ecosystem_services_task) # Actually implements the model logic


def run_project(p):
    """Execute the InVEST carbon pipeline against the ProjectFlow the caller configured.

    Reads p.aoi, and optionally p.tasks_to_skip. Returns p.
    """
    build_task_tree(p)
    # Build the tree in full, then pare it, so structure is identical across variants.
    p.skip_tasks(p.tasks_to_skip)

    # Project constants: no variant changes these, so they are set here rather than
    # by the caller. Set base_data_dir first -- required files are downloaded here.
    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data') # Could be anywhere, including external storage. But, should not be cloud-controlled (like Google Drive).

    # Model paths. get_path resolves each against the project input dir, then
    # base_data, then the cloud, downloading if needed.
    p.base_year_lulc_path = p.get_path('lulc/esa/lulc_esa_2017.tif') # Defines the fine_resolution
    p.region_ids_coarse_path = p.get_path('cartographic/ee/id_rasters/eemarine_r566_ids_900sec.tif') # Defines the coarse_resolution
    p.global_regions_vector_path = p.get_path('cartographic/ee/eemarine_r566_correspondence.gpkg') # Will be used to create the aoi vector

    p.L = hb.get_logger(p.project_name)
    hb.log('Created ProjectFlow object at ' + p.project_dir +
           '\n    from script ' + p.calling_script +
           '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    # run_mode: 'check' resumes in place | 'fresh_intermediate' rebuilds all
    # computation but keeps input/ (test projects only) | 'full' timestamps a new dir.
    p = hb.ProjectFlow(project_name='invest_carbon_in_projectflow', run_mode='check',
                       extra_dirs=['Files', 'global_invest', 'projects'])

    p.aoi = 'RWA' # The variant knob: an ISO3 code, or 'global'.
    # p.tasks_to_skip = ['carbon_storage_biophysical_invest']

    run_project(p)
