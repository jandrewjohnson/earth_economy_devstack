"""Canonical run file: run_project(p), driven by a scenarios CSV.

    Configuration: level 3 of 4 -- what varies is rows in a scenarios CSV
    Code layout:   single file -- tasks are defined here
    Ownership:     self-contained -- you own every file this run touches

run_project(p) sets what no variant ever changes; the caller sets what a variant might.

This template's three-column scenarios CSV is illustrative only; the real schema is
specified in docs/proposed_changes.qmd.

A variant run is its own file, never a fork: run_template_3_canonical_test.py.

Annotated version: ../run_templates_annotated/run_template_3_canonical.py
"""
import os

import numpy as np
import hazelbean as hb


def build_task_tree(p):
    p.yield_rasters_task = p.add_task(yield_rasters)
    p.yield_summations_task = p.add_task(yield_summations)


def yield_rasters(p):
    """One raster per scenario row."""
    p.scenario_yield_paths = {row['scenario_label']: os.path.join(p.cur_dir, row['scenario_label'] + '.tif')
                              for _, row in p.scenarios_df.iterrows()}

    if p.run_this:
        for _, row in p.scenarios_df.iterrows():
            path = p.scenario_yield_paths[row['scenario_label']]
            if not hb.path_exists(path):
                # Real inputs: path = p.get_path(row['yield_ref_path'])
                offset = float(row['yield_offset'])
                array = np.fromfunction(lambda r, c: ((r + c + offset) % 7) - 1.0, (60, 120))
                hb.save_array_as_geotiff(
                    array.astype(np.float32), path,
                    data_type=6, ndv=p.ndv,
                    geotransform_override=(-180.0, 3.0, 0.0, 90.0, 0.0, -3.0),
                    projection_override=hb.wgs_84_wkt)
                hb.log('Wrote ' + path)


def yield_summations(p):
    """One output file per scenario row, each behind an existence check.
    
    # ARCHITECTURE NOTE: I went back and forth on when a run_project() is needed. 
    # Say for instance you wanted a test run that just had a smaller aoi. Why not just have a run_*_test.py like before?
    # This new file would duplicate fourtenen lines and change only one. 
    # The cost isn't the typing — it's that the other fourteen must stay in sync, and the failure is silent. 
    # Bump lulc_esa_2017 → 2020 in the main file and forget the test file, and the 
    # smoke test still passes while testing different inputs than the run it's supposed to smoke-test. 
    """
    p.summation_paths = {label: os.path.join(p.cur_dir, label + '_sum.csv')
                         for label in p.scenario_yield_paths}

    if p.run_this:
        for _, row in p.scenarios_df.iterrows():
            label = row['scenario_label']
            summation_path = p.summation_paths[label]
            if not hb.path_exists(summation_path):
                array = hb.as_array(p.scenario_yield_paths[label])
                total = float(array[array != p.ndv].sum())
                with open(summation_path, 'w') as f:
                    f.write('scenario_label,year,total_caloric_yield\n')
                    f.write(label + ',' + str(row['year']) + ',' + str(total) + '\n')
                hb.log('Summed ' + label + ': ' + str(total))


def run_project(p):
    """Execute the pipeline against the ProjectFlow the caller configured.

    Reads p.scenario_definitions_filename, and optionally p.tasks_to_skip. Returns p.
    """
    build_task_tree(p)
    # Build the tree in full, then pare it, so structure is identical across variants.
    p.skip_tasks(p.tasks_to_skip)

    # Project constants: no variant changes these. Template 4 replaces this block
    # with a parameters CSV read into the same attributes.
    p.ndv = -9999.0

    # Tracked in input_template/ next to this file; ProjectFlow seeds input/ from it.
    # Loads p.scenarios_df and hydrates row 0 onto p.
    hb.initialize_scenarios(p, p.scenario_definitions_filename)

    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data')

    p.L = hb.get_logger(p.project_name)
    hb.log('Created ProjectFlow object at ' + p.project_dir +
           '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    # run_mode: 'check' resumes in place | 'fresh_intermediate' rebuilds all
    # computation but keeps input/ (test projects only) | 'full' timestamps a new dir.
    p = hb.ProjectFlow(project_name='template_3_concise', run_mode='check')
    p.scenario_definitions_filename = 'template_3_scenarios.csv'

    run_project(p)
