"""Tree builders and definition-CSV hydration for the caloric-yield project.

This is the module that the Code layout axis is really about. The other two
modules hold code a run file never calls directly; this one holds the two things
a run file DOES call:

    build_standard_task_tree(p)      what the pipeline is
    initialize_project(p)            the model's post-load initializer

Once these live here, a run file's build_task_tree shrinks to a one-line
delegation, and every project that wants this pipeline gets it by importing
rather than by copying. The CSV loads themselves are hazelbean's job
(hb.initialize_parameters / hb.initialize_scenarios); what stays here is the
model-specific tail that runs after them. That is exactly the shape of
seals_initialize_project, gtappy_initialize_project, and
gtap_invest_initialize_project.

Keeping the builder here rather than in the run file is also what makes the
Ownership axis possible: a downstream user can call build_standard_task_tree(p)
and add their own tasks around it without editing this file.
"""
import hazelbean as hb

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


def initialize_project(p):
    """Caloric-yield's model initializer: everything model-specific that runs after
    the definitions loads. Ordering is load-bearing (EE Spec): the caller runs
    hb.initialize_parameters / hb.initialize_scenarios first, then one
    initialize_project(p) per included model.
    """
    if getattr(p, 'scenario_definitions_filename', None) and not hasattr(p, 'scenarios_df'):
        raise RuntimeError('caloric_yield initialize_project(p) was called before the scenarios file was initialized. Call hb.initialize_scenarios(p, p.scenario_definitions_filename) first (EE Spec ordering rule).')
    if getattr(p, 'parameter_definitions_filename', None) and not hasattr(p, 'parameters_df'):
        raise RuntimeError('caloric_yield initialize_project(p) was called before the parameters file was initialized. Call hb.initialize_parameters(p, p.parameter_definitions_filename) first (EE Spec ordering rule).')

    # CSV values arrive as strings; cast the ones this model uses as numbers.
    p.ndv = float(p.ndv)
    p.n_rows = int(p.n_rows)
    p.n_cols = int(p.n_cols)

    p.L = hb.get_logger(p.project_name)
