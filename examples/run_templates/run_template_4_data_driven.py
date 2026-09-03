"""Data-driven run file: scenarios CSV (what varies) + parameters CSV (what is constant).

    Configuration: level 4 of 4 -- + a parameters CSV; machine values leave the code
    Code layout:   single file -- tasks are defined here
    Ownership:     self-contained -- you own every file this run touches

run_project(p) sets what no variant ever changes; the caller sets what a variant
might -- with one deliberate exception: the caller sets the FULL definitions-filename
block (the project's interface manifest), and run_project only loads it.
Machine-specific keys ship blank in the tracked input_template/ CSV (read in place); to
fill them, copy that CSV into the machine's untracked input/, so they never reach the code or git.

Annotated version: ../run_templates_annotated/run_template_4_data_driven.py
"""
import os

import numpy as np
import pandas as pd
import hazelbean as hb


def build_task_tree(p):
    p.yield_analysis_task = p.add_task(yield_analysis)
    p.yield_rasters_task = p.add_task(yield_rasters, parent=p.yield_analysis_task)
    p.yield_summations_task = p.add_task(yield_summations, parent=p.yield_analysis_task)
    p.yield_report_task = p.add_task(yield_report)


def yield_analysis(p):
    """Container task: groups the per-scenario steps under one directory."""
    pass


def yield_rasters(p):
    """One raster per scenario row. Shape and no-data come from parameters.csv."""
    p.scenario_yield_paths = {row['scenario_label']: os.path.join(p.cur_dir, row['scenario_label'] + '.tif')
                              for _, row in p.scenarios_df.iterrows()}

    if p.run_this:
        for _, row in p.scenarios_df.iterrows():
            path = p.scenario_yield_paths[row['scenario_label']]
            if not hb.path_exists(path):
                # Real inputs: path = p.get_path(row['yield_ref_path'])
                offset = float(row['yield_offset'])
                array = np.fromfunction(lambda r, c: ((r + c + offset) % 7) - 1.0,
                                        (p.n_rows, p.n_cols))
                hb.save_array_as_geotiff(
                    array.astype(np.float32), path,
                    data_type=6, ndv=p.ndv,
                    geotransform_override=(-180.0, 360.0 / p.n_cols, 0.0,
                                           90.0, 0.0, -180.0 / p.n_rows),
                    projection_override=hb.wgs_84_wkt)
                hb.log('Wrote ' + path)


def yield_summations(p):
    """One output file per scenario row, each behind an existence check."""
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


def yield_report(p):
    """Concatenate the per-scenario results. Cheap, so deliberately not existence-guarded."""
    p.report_path = os.path.join(p.cur_dir, 'yield_report.csv')

    if p.run_this:
        rows = [pd.read_csv(i) for i in p.summation_paths.values() if hb.path_exists(i)]
        pd.concat(rows, ignore_index=True).to_csv(p.report_path, index=False)
        hb.log('Wrote report across ' + str(len(rows)) + ' scenarios to ' + p.report_path)


def run_project(p):
    """Execute the pipeline against the ProjectFlow the caller configured.

    Reads p.scenario_definitions_filename, and optionally p.tasks_to_skip. Returns p.
    
    # ARCHITECTURE NOTE: I went back and forth on when a run_project() is needed. 
    # Say for instance you wanted a test run that just had a smaller aoi. Why not just have a run_*_test.py like before?
    # This new file would duplicate fourtenen lines and change only one. 
    # The cost isn't the typing — it's that the other fourteen must stay in sync, and the failure is silent. 
    # Bump lulc_esa_2017 → 2020 in the main file and forget the test file, and the 
    # smoke test still passes while testing different inputs than the run it's supposed to smoke-test. 
    """
    build_task_tree(p)
    p.skip_tasks(p.tasks_to_skip)

    # Parameters: constant across scenarios AND across variants. The caller named
    # the file (full-block rule); run_project only loads it. Hydrated onto p;
    # blank values read as None.
    hb.initialize_parameters(p, p.parameter_definitions_filename)
    # Cast the values used as numbers (hydration leaves plain numerics usable,
    # but being explicit here keeps the tasks honest about their types).
    p.ndv = float(p.ndv)
    p.n_rows = int(p.n_rows)
    p.n_cols = int(p.n_cols)

    # Scenarios: the rows of work. The caller chose which CSV.
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
    p = hb.ProjectFlow(project_name='template_4_concise', run_mode='check')
    p.parameter_definitions_filename = 'template_4_parameters.csv'
    p.scenario_definitions_filename = 'template_4_scenarios.csv'
    # p.tasks_to_skip = ['yield_report']

    run_project(p)
