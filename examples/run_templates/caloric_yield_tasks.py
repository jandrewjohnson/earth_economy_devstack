"""Task functions for the caloric-yield project.

A TASK is a function that takes `p`, gets its own output directory at `p.cur_dir`
when it is added to a tree, publishes its output paths above the `if p.run_this:`
gate, and guards expensive work behind an existence check. That is the whole
distinction from the helpers in caloric_yield_functions.py and
caloric_yield_utils.py, which take plain arguments and know nothing about
ProjectFlow.

Task modules are plural and topic-named. `<project>_tasks.py` is the default
home; a topic splits off into its own module once it gets big (seals has
seals_process_coarse_timeseries.py, seals_visualization_tasks.py, and others).
"""
import os

import numpy as np
import pandas as pd
import hazelbean as hb

from caloric_yield_functions import caloric_yield_surface, total_caloric_yield
from caloric_yield_utils import save_global_geotiff


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
                array = caloric_yield_surface(float(row['yield_offset']), p.n_rows, p.n_cols)
                save_global_geotiff(array, path, p.ndv, p.n_rows, p.n_cols)
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
                total = total_caloric_yield(hb.as_array(p.scenario_yield_paths[label]), p.ndv)
                with open(summation_path, 'w') as f:
                    f.write('scenario_label,year,total_caloric_yield\n')
                    f.write(label + ',' + str(row['year']) + ',' + str(total) + '\n')
                hb.log('Summed ' + label + ': ' + str(total))


def yield_report(p):
    """Concatenate the per-scenario results. Cheap, so deliberately not guarded."""
    p.report_path = os.path.join(p.cur_dir, 'yield_report.csv')

    if p.run_this:
        rows = [pd.read_csv(i) for i in p.summation_paths.values() if hb.path_exists(i)]
        pd.concat(rows, ignore_index=True).to_csv(p.report_path, index=False)
        hb.log('Wrote report across ' + str(len(rows)) + ' scenarios to ' + p.report_path)
