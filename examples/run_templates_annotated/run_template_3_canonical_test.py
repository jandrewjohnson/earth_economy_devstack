"""Pared test run of template 3: same task tree, a one-row scenarios CSV.

    Configuration: level 3 of 4 -- inherited from run_template_3_canonical.py
    Code layout:   single file -- the pipeline is imported, not restated
    Ownership:     self-contained -- you own every file this run touches

A variant sits at the SAME position on all three axes as the run it varies. That
is the test: if a variant has to move along an axis, it is not a variant.

This file is the whole answer to the "copy the run file and edit one line"
instinct. It imports the pipeline unchanged and configures it differently. What
differs from the full run is data (a one-row CSV) and placement (its own project
dir) -- never code.

Under this set's rule -- run_project(p) sets what no variant ever changes, the
caller sets what a variant might -- a variant is just another __main__ block.
Everything it varies is stated here, at the call site, rather than being passed
positionally into a signature whose defaults you would have to open the callee to
read.

Run it, then run run_template_3_canonical.py: they are separate project dirs, so
neither disturbs the other's cached results.
"""
import hazelbean as hb

from run_template_3_canonical import run_project


if __name__ == '__main__':
    p = hb.ProjectFlow(project_name='template_3_annotated_test', run_mode='check')
    p.scenario_definitions_filename = 'template_3_scenarios_test.csv'

    # The other variant lever: pare the tree instead of the data. Uncomment to
    # build the rasters but skip the summations.
    # p.tasks_to_skip = ['yield_summations']

    run_project(p)
