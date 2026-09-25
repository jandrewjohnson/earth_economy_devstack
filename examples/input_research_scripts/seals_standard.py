"""Standard SEALS run: the standard task tree, driven by standard_scenarios.csv.

A reference implementation -- the conventions at full scale on a real model. The
code below is identical to run_templates/run_template_seals_example.py, which is
the copy to start a new project from, and to seals/seals/run_seals.py,
the run file SEALS itself ships. If you change the anatomy in one, change it in
all three.

Read this one; copy from run_templates/.
"""
import os

import hazelbean as hb

from seals import seals_initialize_project


def build_task_tree(p):
    # This project's task tree: delegates unchanged to the shared library builder.
    # Compose additional library subtrees or project-specific tasks here if the
    # project's pipeline ever diverges; only tree construction belongs in this function.
    seals_initialize_project.build_standard_task_tree(p)


def run_project(p):
    """Execute the standard SEALS pipeline against the ProjectFlow the caller configured.

    Reads p.scenario_definitions_filename, and optionally p.tasks_to_skip. Returns p.
    """
    # Must be set BEFORE the tree is built: the standard tree contains parallel
    # iterator tasks, which read this at construction time.
    p.run_in_parallel = 1

    # IF YOU WANT TO LOOK AT THE MODEL LOGIC, INSPECT THIS FUNCTION.
    build_task_tree(p)
    p.skip_tasks(p.tasks_to_skip)

    # Project constants: no variant changes these, so they are set here rather
    # than by the caller. The model checks base_data_dir for everything it needs
    # and downloads anything missing; one base_data serves every project.
    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data')

    # ProjectFlow downloads via p.get_path(). To pull from a non-default bucket,
    # provide the name and credentials here. Otherwise the default public data is used.
    p.data_credentials_path = None
    p.input_bucket_name = None

    # How large a chunk to process at a time. 4 deg is about the max for 64gb systems.
    p.processing_resolution = 1.0 # In degrees. Must be in pyramid_compatible_resolutions

    # Scenarios: the rows of work. The caller chose which CSV, because that is
    # exactly what a variant run varies. SEALS generates a default in the
    # project's input_dir if this is your first run.
    p.scenario_definitions_path = os.path.join(p.input_dir, p.scenario_definitions_filename)
    seals_initialize_project.initialize_scenario_definitions(p)

    seals_initialize_project.set_advanced_options(p)

    p.L = hb.get_logger(p.project_name)
    hb.log('Created ProjectFlow object at ' + p.project_dir +
           '\n    from script ' + p.calling_script +
           '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    # run_mode: 'check' resumes in place | 'fresh_intermediate' rebuilds all
    # computation but keeps input/ (test projects only) | 'full' timestamps a new dir.
    p = hb.ProjectFlow(project_name='seals', run_mode='check')
    p.scenario_definitions_filename = 'standard_scenarios.csv'
    # p.tasks_to_skip = ['stitched_lulc_simplified_scenarios']

    run_project(p)
