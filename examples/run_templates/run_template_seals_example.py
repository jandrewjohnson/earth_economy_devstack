"""Standard SEALS run: the standard task tree, driven by standard_scenarios.csv.

    Configuration: level 3 of 4 -- what varies is rows in a scenarios CSV
    Code layout:   library package -- tasks and the tree builder come from seals
    Ownership:     devstack developer -- seals is imported, and you could edit it

This is the first template whose Code layout is not "single file": nothing in it
defines a task. Compare templates 1-4, which sit at the same Configuration levels
with everything in one file -- that is the point of separating the axes. Moving
along Code layout changed exactly one function here, build_task_tree, which now
delegates instead of containing.

This file is a teaching copy of seals/seals/run_seals.py, which is
the real reference SEALS run. If you change the anatomy in one, change it in the
other.

For the Ownership axis one step further -- a library as a read-only dependency in
your own repo, with your own tasks composed onto its tree -- see
run_template_downstream_user.py next to this file. See
docs/project_complexity.qmd for the full model.
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
    # exactly what a variant run varies. The CSV ships in seals' tracked
    # input_template/ and is read there in place (after the project's input/).
    hb.initialize_scenarios(p, p.scenario_definitions_filename)

    # Seals' model initializer: advanced options, derived attributes, calibration
    # override dict, logger. Must come AFTER the scenarios load (EE Spec ordering rule).
    seals_initialize_project.initialize_project(p)

    p.execute()

    return p


if __name__ == '__main__':
    # run_mode: 'check' resumes in place | 'fresh_intermediate' rebuilds all
    # computation but keeps input/ (test projects only) | 'full' timestamps a new dir.
    p = hb.ProjectFlow(project_name='seals', run_mode='check')
    # NOTE: standard_scenarios.csv is GLOBAL; for a quick first run point at
    # standard_scenarios_test.csv (RWA, one projection year) instead.
    p.scenario_definitions_filename = 'standard_scenarios.csv'
    # p.tasks_to_skip = ['stitched_lulc_simplified_scenarios']

    run_project(p)
