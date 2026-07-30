"""Pared test run of template 3: same task tree, a one-row scenarios CSV.

    Configuration: level 3 of 4 -- inherited from run_template_3_canonical.py
    Code layout:   single file -- the pipeline is imported, not restated
    Ownership:     self-contained -- you own every file this run touches

A variant sits at the SAME position on all three axes as the run it varies. If it
has to move along an axis, it is not a variant. What differs here is data (a
one-row CSV) and placement (its own project dir) -- never code.

Annotated version: ../run_templates_annotated/run_template_3_canonical_test.py
"""
import hazelbean as hb

from run_template_3_canonical import run_project


if __name__ == '__main__':
    p = hb.ProjectFlow(project_name='template_3_concise_test', run_mode='check')
    p.scenario_definitions_filename = 'template_3_scenarios_test.csv'

    # The other variant lever: pare the tree instead of the data.
    # p.tasks_to_skip = ['yield_summations']

    run_project(p)
