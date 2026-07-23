"""Example: run a small ProjectFlow task tree end to end on the EE devstack test data."""
import os
import hazelbean as hb
import pandas as pd

import example_tasks


def build_task_tree(p):
    p.ecosystem_services_task = p.add_task(example_tasks.ecosystem_services)
    p.water_yield_task = p.add_task(example_tasks.water_yield, parent=p.ecosystem_services_task)
    p.another_example_task = p.add_task(example_tasks.another_example, parent=p.ecosystem_services_task)


def run_project(parameter_definitions_filename='example_global_invest_parameters.csv',
                project_name='test_example', append_timestamp=False,
                tasks_to_skip=None, execute=True):
    """Build and execute the example task tree.

    ProjectFlow only calculates tasks that haven't been done yet, so a stable
    project_name (append_timestamp=False) resumes in place; append_timestamp=True gives a
    fresh directory that forces every task to re-run. Returns p.
    """
    # A ProjectFlow object is created from the Hazelbean library to organize directories
    # and enable parallel processing. Project-level variables are assigned as attributes
    # on the p object. The EE-spec locates the project dir with extra_dirs relative to the
    # user_dir.
    p = hb.ProjectFlow()

    p.user_dir = os.path.expanduser('~')
    p.extra_dirs = ['Files', 'global_invest', 'projects']
    p.project_name = project_name
    if append_timestamp:
        p.project_name = p.project_name + '_' + hb.pretty_time()

    # The project-dir is where everything will be stored (input, intermediate, output).
    # IMPORTANT: this should not be in a cloud-synced directory (dropbox, google drive,
    # etc.), which will either make the run fail or make it very slow. The recommended
    # place is somewhere in the user's home directory (as coded above).
    p.project_dir = os.path.join(p.user_dir, os.sep.join(p.extra_dirs), p.project_name)
    p.set_project_dir(p.project_dir)

    # Build the task tree via a building function.
    # IF YOU WANT TO LOOK AT THE MODEL LOGIC, INSPECT THIS FUNCTION.
    build_task_tree(p)
    p.skip_tasks(tasks_to_skip)

    # Set the base data dir. The model checks here for everything it needs and downloads
    # anything missing. The final directory has to be named base_data to match the naming
    # convention on the google cloud bucket.
    p.base_data_dir = os.path.join(p.user_dir, 'Files/base_data')

    # Best open-source base_data bucket is 'gtap_invest_seals_2023_04_21'.
    p.input_bucket_name = None

    p.countries_iso3_path = p.get_path('pyramids', 'countries_iso3.gpkg')

    # Downloading base_data via the google_cloud_api service needs a valid credentials
    # JSON file. Its location is held in the parameters CSV (data_credentials_path key).
    # The tracked template ships this blank; put your machine's path in the untracked
    # input/ copy. Email jajohns@umn.edu if you need credentials.
    p.parameter_definitions_filename = parameter_definitions_filename
    p.parameter_definitions_path = os.path.join(p.input_dir, p.parameter_definitions_filename)
    params = pd.read_csv(p.parameter_definitions_path)
    params = dict(zip(params['key'], params['value']))
    cred = params.get('data_credentials_path')
    p.data_credentials_path = cred if isinstance(cred, str) and cred.strip() else None

    p.L = hb.get_logger('example_global_invest')
    hb.log('Created ProjectFlow object at ' + p.project_dir)

    if execute:
        p.execute()

    return p


if __name__ == '__main__':
    run_project()
