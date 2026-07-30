"""Standard SEALS run: standard task tree driven by standard_scenarios.csv."""
import os

import hazelbean as hb

from seals import seals_initialize_project


def build_task_tree(p):
    # This project's task tree: delegates unchanged to the shared library builder.
    # Compose additional library subtrees or project-specific tasks here if the
    # project's pipeline ever diverges; only tree construction belongs in this function.
    seals_initialize_project.build_standard_task_tree(p)


def run_project(scenario_definitions_filename='standard_scenarios.csv',
                project_name='standard',
                run_mode='check',
                tasks_to_skip=None):
    """Build and execute the standard SEALS pipeline against a given scenarios CSV.

    run_mode='full' gives each run its own fresh project dir; the default
    'check' reuses a stable project_name dir so repeated runs resume in place,
    skipping tasks whose outputs already exist. tasks_to_skip pares the tree for
    variant runs. Returns p.
    """

    # Create a ProjectFlow Object to organize directories and enable parallel processing.
    # The ProjectFlow constructor validates run_mode and infers the project_dir
    # from the repo layout (see _resolve_project_dir for the semantics and inference).
    p = hb.ProjectFlow(project_name=project_name, run_mode=run_mode)

    p.run_in_parallel = 1 # Must be set before building the task tree if the task tree has parralel iterator tasks.

    # Build the task tree via a building function and assign it to p. IF YOU WANT TO LOOK AT THE MODEL LOGIC, INSPECT THIS FUNCTION
    build_task_tree(p)
    p.skip_tasks(tasks_to_skip)

    # Set the base data dir. The model will check here to see if it has everything it needs to run.
    # If anything is missing, it will download it. You can use the same base_data dir across multiple projects.
    p.base_data_dir = os.path.join(p.user_dir, 'Files/base_data')

    # ProjectFlow downloads all files automatically via the p.get_path() function. If you want it to download from a different
    # bucket than default, provide the name and credentials here. Otherwise uses default public data 'gtap_invest_seals_2023_04_21'.
    p.data_credentials_path = None
    p.input_bucket_name = None

    ## Set defaults and generate the scenario_definitions.csv if it doesn't exist.
    # SEALS will run based on the scenarios defined in a scenario_definitions.csv
    # If you have not run SEALS before, SEALS will generate it in your project's input_dir.
    p.scenario_definitions_filename = scenario_definitions_filename
    p.scenario_definitions_path = os.path.join(p.input_dir, p.scenario_definitions_filename)
    seals_initialize_project.initialize_scenario_definitions(p)

    # Set processing resolution: determines how large of a chunk should be processed at a time. 4 deg is about max for 64gb memory systems
    p.processing_resolution = 1.0 # In degrees. Must be in pyramid_compatible_resolutions

    seals_initialize_project.set_advanced_options(p)

    p.L = hb.get_logger('test_run_seals')
    hb.log('Created ProjectFlow object at ' + p.project_dir + '\n    from script ' + p.calling_script + '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    run_project()
