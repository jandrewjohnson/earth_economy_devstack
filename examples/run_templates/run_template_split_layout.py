"""Split code layout: the same project as template 4, across five files.

    Configuration: level 4 of 4 -- scenarios CSV + parameters CSV (unchanged)
    Code layout:   split -- tasks, science, utils and tree builder are siblings
    Ownership:     self-contained -- you own every file this run touches

THIS IS A MOVE ALONG ONE AXIS ONLY
    Diff this against run_template_4_data_driven.py. The pipeline, the CSVs, the
    results and the configuration level are identical; the tasks moved out. That
    is what makes the axes worth separating: nothing about splitting your code
    requires a scenarios CSV, and nothing about a scenarios CSV requires
    splitting your code. global_invest's service runners are configuration level
    2 with a split layout.

WHERE EVERYTHING WENT, AND THE RULE FOR EACH

    caloric_yield_tasks.py               functions that take p, get a cur_dir,
                                         and join a tree
    caloric_yield_functions.py           the science: plain args in, values out.
                                         Terminal -- stays with the model
    caloric_yield_utils.py               science-unaware helpers: plain args in,
                                         values out. A PROMOTION QUEUE -- when a
                                         second project needs one, it goes to
                                         hazelbean
    caloric_yield_initialize_project.py  the tree builder and CSV hydration; the
                                         only module a run file calls directly
    this file                            what this particular run is

MOVE HERE WHEN
    A task module gets big enough that you scroll to navigate it, or a second run
    file needs the same task. Not before -- templates 1-4 are honest for a project
    with one run file and a handful of tasks.

WHAT MOVING COST
    One function changed: build_task_tree now delegates instead of containing.
    Everything else is imports.

NEXT AXIS
    run_template_downstream_user.py imports this project's builder as a read-only
    dependency and extends it, which is the Ownership axis.
"""
import os

import hazelbean as hb

import caloric_yield_initialize_project


def build_task_tree(p):
    # Delegates unchanged to the shared builder. Compose additional subtrees or
    # project-specific tasks here if this project's pipeline ever diverges; only
    # tree construction belongs in this function.
    caloric_yield_initialize_project.build_standard_task_tree(p)


def run_project(p):
    """Execute the pipeline against the ProjectFlow the caller configured.

    Reads p.scenario_definitions_filename, and optionally p.tasks_to_skip. Returns p.
    """
    build_task_tree(p)
    p.skip_tasks(p.tasks_to_skip)

    # Definitions loads first (the caller named the files), then the model's
    # initializer -- the EE Spec ordering rule, which initialize_project enforces.
    hb.initialize_parameters(p, p.parameter_definitions_filename)
    hb.initialize_scenarios(p, p.scenario_definitions_filename)
    caloric_yield_initialize_project.initialize_project(p)

    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data')

    p.execute()

    return p


if __name__ == '__main__':
    # run_mode: 'check' resumes in place | 'fresh_intermediate' rebuilds all
    # computation but keeps input/ (test projects only) | 'full' timestamps a new dir.
    p = hb.ProjectFlow(project_name='template_split_layout', run_mode='check')
    p.parameter_definitions_filename = 'caloric_yield_parameters.csv'
    p.scenario_definitions_filename = 'caloric_yield_scenarios.csv'
    # p.tasks_to_skip = ['yield_report']

    run_project(p)
