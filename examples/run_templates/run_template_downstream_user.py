"""Downstream user: the pipeline is a read-only dependency, extended not edited.

    Configuration: level 4 of 4 -- scenarios CSV + parameters CSV (unchanged)
    Code layout:   single file -- this project's own task is defined right here
    Ownership:     downstream user -- caloric_yield_* is imported, never edited

THIS IS A MOVE ALONG ONE AXIS ONLY -- AND NOT THE ONE YOU MIGHT EXPECT
    Compare run_template_split_layout.py: same configuration level, same
    pipeline, same CSVs. What changed is who owns the code. And notice this file
    is back to a SINGLE-FILE layout while being further along the ownership axis
    than the split template -- because a downstream project with one extra task
    has no reason to split anything. The axes really are independent; the layout
    of your repo has nothing to do with who owns the library you import.

    In real life caloric_yield_* would be pip-installed from another repo. Here
    it sits in the same directory so the template runs. Pretend you cannot edit
    it -- that constraint is the entire lesson.

WHAT A DOWNSTREAM PROJECT OWNS
    this run file, its scenarios CSV, its parameters CSV, its own tasks, and its
    own project directory. Note that nothing here passes extra_dirs: the project
    lands beside YOUR repo, under YOUR project's name, not under the library's.

EXTENDING WITHOUT MODIFYING
    build_task_tree calls the library builder and then adds this project's own
    task. The library never learns that yield_ranking exists.

    p.tasks_to_skip is the other half: you can drop library tasks you do not want
    without touching the library.

    THE UNSOLVED PART, STATED HONESTLY: attaching to a specific library task
    (parent=p.yield_analysis_task) works only because builders assign p.<name>_task
    as a side effect. No contract says which of those names are public API or
    that the library will not rename them, so a rename upstream breaks your
    project silently. Until that contract exists, prefer attaching at the top
    level, as below, and depend on published attributes (p.report_path) rather
    than on task objects.
"""
import os

import pandas as pd
import hazelbean as hb

import caloric_yield_initialize_project


def build_task_tree(p):
    # The library's standard tree, unchanged...
    caloric_yield_initialize_project.build_standard_task_tree(p)
    # ...plus this project's own task, appended at the top level. This is the
    # whole extension mechanism: compose after the builder returns.
    p.yield_ranking_task = p.add_task(yield_ranking)


def yield_ranking(p):
    """This project's own contribution: rank the scenarios by total yield.

    It consumes p.report_path, which the library's yield_report task published
    above its own run_this gate. Depending on a published PATH rather than on a
    task object is the safer coupling: paths are what the library actually
    promises downstream.
    """
    p.ranking_path = os.path.join(p.cur_dir, 'yield_ranking.csv')

    if p.run_this:
        report_df = pd.read_csv(p.report_path)
        ranked = report_df.sort_values('total_caloric_yield', ascending=False)
        ranked.insert(0, 'rank', range(1, len(ranked) + 1))
        ranked.to_csv(p.ranking_path, index=False)
        hb.log('Ranked ' + str(len(ranked)) + ' scenarios into ' + p.ranking_path)


def run_project(p):
    """Execute this project's pipeline against the ProjectFlow the caller configured.

    Reads p.scenario_definitions_filename, and optionally p.tasks_to_skip. Returns p.
    """
    build_task_tree(p)
    p.skip_tasks(p.tasks_to_skip)

    # The library's own definition CSVs still drive the library's tasks. This
    # project supplies its own copies in input_template/ -- the library ships the
    # schema, you ship the rows. Loads first, then the library's model initializer
    # (the EE Spec ordering rule).
    hb.initialize_parameters(p, p.parameter_definitions_filename)
    hb.initialize_scenarios(p, p.scenario_definitions_filename)
    caloric_yield_initialize_project.initialize_project(p)

    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data')

    p.execute()

    return p


if __name__ == '__main__':
    # A downstream project names itself, and gets its own project dir. Six
    # scenario rows here against the library template's four -- the rows of work
    # are yours, the pipeline is theirs.
    p = hb.ProjectFlow(project_name='template_downstream_user', run_mode='check')
    p.parameter_definitions_filename = 'caloric_yield_parameters.csv'
    p.scenario_definitions_filename = 'caloric_yield_scenarios_downstream.csv'
    # Drop a library task you do not want, without touching the library:
    # p.tasks_to_skip = ['yield_report']

    run_project(p)
