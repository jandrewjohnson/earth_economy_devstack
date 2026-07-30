"""Tree builders and definition-CSV hydration for the caloric-yield project.

This is the module that the Code layout axis is really about. The other two
modules hold code a run file never calls directly; this one holds the two things
a run file DOES call:

    build_standard_task_tree(p)      what the pipeline is
    initialize_*_definitions(p)      how the CSVs get onto p

Once these live here, a run file's build_task_tree shrinks to a one-line
delegation, and every project that wants this pipeline gets it by importing
rather than by copying. That is exactly the shape of seals_initialize_project,
gtappy_initialize_project, and gtap_invest_initialize_project.

Keeping the builder here rather than in the run file is also what makes the
Ownership axis possible: a downstream user can call build_standard_task_tree(p)
and add their own tasks around it without editing this file.
"""
import os

import pandas as pd

import caloric_yield_tasks


def build_standard_task_tree(p):
    """The standard caloric-yield pipeline.

    Assigns each task onto p as p.<name>_task. A caller composing on top of this
    tree can attach to those (parent=p.yield_analysis_task) -- see the note about
    extension points in run_template_downstream_user.py.
    """
    p.yield_analysis_task = p.add_task(caloric_yield_tasks.yield_analysis)
    p.yield_rasters_task = p.add_task(caloric_yield_tasks.yield_rasters, parent=p.yield_analysis_task)
    p.yield_summations_task = p.add_task(caloric_yield_tasks.yield_summations, parent=p.yield_analysis_task)
    p.yield_report_task = p.add_task(caloric_yield_tasks.yield_report)


def initialize_parameter_definitions(p):
    """Hydrate the parameters CSV onto p. Blank values read as None."""
    p.parameter_definitions_path = os.path.join(p.input_dir, p.parameter_definitions_filename)
    parameters_df = pd.read_csv(p.parameter_definitions_path)
    for _, row in parameters_df.iterrows():
        setattr(p, row['key'], None if pd.isna(row['value']) else row['value'])
    p.ndv = float(p.ndv)
    p.n_rows = int(p.n_rows)
    p.n_cols = int(p.n_cols)


def initialize_scenario_definitions(p):
    """Load the scenarios CSV -- the rows of work -- onto p."""
    p.scenario_definitions_path = os.path.join(p.input_dir, p.scenario_definitions_filename)
    p.scenarios_df = pd.read_csv(p.scenario_definitions_path)
