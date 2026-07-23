import os, sys
import hazelbean as hb
import pandas as pd
# import global_invest.ecosystem_services_functions
# import global_invest.ecosystem_services_functions
import example_tasks


def main():
    ### ------- ENVIRONMENT SETTINGS -------------------------------
    # Users should only need to edit lines in this ENVIRONMENT SETTINGS section

    # A ProjectFlow object is created from the Hazelbean library to organize directories and enable parallel processing.
    # project-level variables are assigned as attributes to the p object (such as in p.base_data_dir = ... below)
    # The only agrument for a project flow object is where the project directory is relative to the current_working_directory.
    # This organization, defined with extra dirs relative to the user_dir, is the EE-spec.
    user_dir = os.path.expanduser('~')        
    extra_dirs = ['Files', 'global_invest', 'projects']

    # The project_name is used to name the project directory below. Also note that
    # ProjectFlow only calculates tasks that haven't been done yet, so adding 
    # a new project_name will give a fresh directory and ensure all parts
    # are run.
    project_name = 'test_example'
    
    # The project-dir is where everything will be stored, in particular in an input, intermediate, or output dir
    # IMPORTANT NOTE: This should not be in a cloud-synced directory (e.g. dropbox, google drive, etc.), which
    # will either make the run fail or cause it to be very slow. The recommended place is (as coded above)
    # somewhere in the users's home directory.
    project_dir = os.path.join(user_dir, os.sep.join(extra_dirs), project_name)

    # Create the ProjectFlow Object
    p = hb.ProjectFlow(project_dir)

    # Build the task tree via a building function and assign it to p
    # IF YOU WANT TO LOOK AT THE MODEL LOGIC, INSPECT THIS FUNCTION
    build_example_task_tree(p)

    # Set the base data dir. The model will check here to see if it has everything it needs to run.
    # If anything is missing, it will download it. You can use the same base_data dir across multiple projects.
    # Additionally, if you're clever, you can move files generated in your tasks to the right base_data_dir
    # directory so that they are available for future projects and avoids redundant processing.
    # NOTE THAT the final directory has to be named base_data to match the naming convention on the google cloud bucket.
    p.base_data_dir = os.path.join(user_dir, 'Files/base_data')

    # In order for SEALS to download using the google_cloud_api service, you need to have a valid credentials JSON file.
    # Identify its location here. If you don't have one, email jajohns@umn.edu. The data are freely available but are very, very large
    # (and thus expensive to host), so I limit access via credentials.
    p.data_credentials_path = '..\\api_key_credentials.json'

    # There are different versions of the base_data in gcloud, but best open-source one is 'gtap_invest_seals_2023_04_21'
    p.input_bucket_name = None
    

    p.countries_iso3_path = p.get_path('pyramids', 'countries_iso3.gpkg')


    # Assign useful locals to project flow level
    p.user_dir = user_dir
    p.project_name = project_name
    p.project_dir = project_dir
    
    p.execute()
    

def build_example_task_tree(p):
    
    p.ecosystem_services_task = p.add_task(example_tasks.ecosystem_services)
    p.water_yield_task = p.add_task(example_tasks.water_yield, parent=p.ecosystem_services_task)
    p.another_example_task = p.add_task(example_tasks.another_example, parent=p.ecosystem_services_task)
    



if __name__ == '__main__':
    main()