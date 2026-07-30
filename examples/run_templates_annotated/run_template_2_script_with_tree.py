"""Template 2 of 4 — SCRIPT WITH A TASK TREE.

    Configuration: level 2 of 4 -- a task tree, constants still inline
    Code layout:   single file -- tasks are defined here
    Ownership:     self-contained -- you own every file this run touches

See run_template_1_minimal.py in this directory for the three-axis map.

Read the __main__ block at the bottom closely: the run file configures p there
and then runs it. Template 3 keeps exactly that shape and only factors the
running part into run_project(p), which is why moving up the Configuration axis
never introduces a new mechanism -- just a place to put one.

WHEN THIS LEVEL IS THE RIGHT ONE
    You have more than one step, and you want each step named, cached, and given
    its own folder. There is still exactly one way you run this project.

WHAT THIS LEVEL DEMONSTRATES
    - build_task_tree(p) is the one place that answers "what is this pipeline?"
    - Tasks chain by PUBLISHING their output paths above their p.run_this gate,
      so a downstream task works whether or not the upstream task ran this time.
    - add_task(..., run=0) disables a task without deleting it from the tree.

WHAT THIS LEVEL DELIBERATELY DOES NOT HAVE
    No run_project(), no CSVs. Adding them before you need them is its own kind
    of overengineering -- earn each rung.

PROMOTE TO TEMPLATE 3 WHEN
    You want a second variant of this run (a quick smoke test, a different set of
    inputs) and your instinct is to copy this file and edit one line. That instinct
    is the retraction machine; template 3 varies data instead of forking code.
"""
import os

import numpy as np
import hazelbean as hb


def build_task_tree(p):
    # Only tree construction belongs in this function. Where a task's outputs go
    # is the task's own business (see the path lines inside each task below).
    p.yield_rasters_task = p.add_task(yield_rasters)
    p.cleaned_yield_task = p.add_task(cleaned_yield)
    p.yield_summary_task = p.add_task(yield_summary)


def yield_rasters(p):
    """Stand-in for acquiring inputs: writes four small yield rasters."""
    # Published above the gate: downstream tasks get these paths on every run.
    p.yield_paths = [os.path.join(p.cur_dir, 'yield_per_cell_' + str(i) + '.tif')
                     for i in range(1, 5)]

    if p.run_this:
        for i, path in enumerate(p.yield_paths):
            # One output file per input, each behind its own existence check.
            # Delete one file and re-run: only that one is recomputed.
            if not hb.path_exists(path):
                # Synthetic data so this template runs with nothing downloaded.
                # In a real project you would not generate inputs at all -- you
                # would resolve them with p.get_path(), which searches the project
                # input dir, then base_data, then the cloud, downloading if needed:
                #     path = p.get_path('crops', 'yield_per_cell.tif')
                # Note the values run from -1 to 5: the -1s are the "bad" cells
                # that the next task cleans.
                array = np.fromfunction(lambda r, c: ((r + c + i) % 7) - 1.0, (60, 120))
                # geotransform/projection/data_type are spelled out here only
                # because there is no real raster to copy them from. With real
                # inputs you pass geotiff_uri_to_match=<an input path> and all
                # four of these keyword arguments disappear.
                hb.save_array_as_geotiff(
                    array.astype(np.float32), path,
                    data_type=6, ndv=p.ndv,
                    geotransform_override=(-180.0, 3.0, 0.0, 90.0, 0.0, -3.0),
                    projection_override=hb.wgs_84_wkt)
                hb.log('Wrote ' + path)


def cleaned_yield(p):
    """Set negative (nonsensical) yield values to the no-data value."""
    p.cleaned_yield_paths = [os.path.join(p.cur_dir, hb.file_root(i) + '_cleaned.tif')
                             for i in p.yield_paths]

    if p.run_this:
        for input_path, output_path in zip(p.yield_paths, p.cleaned_yield_paths):
            if not hb.path_exists(output_path):
                # Vectorized numpy, one line -- never loop over rows and columns.
                # When the raster is larger than memory, this is the line that
                # becomes hb.raster_calculator(); see docs/project_complexity.qmd.
                array = hb.as_array(input_path)
                array = np.where(array < 0, p.ndv, array)
                hb.save_array_as_geotiff(array, output_path,
                                         geotiff_uri_to_match=input_path)
                hb.log('Cleaned ' + input_path)


def yield_summary(p):
    """Sum each cleaned raster into one summary table."""
    p.summary_path = os.path.join(p.cur_dir, 'yield_summary.csv')

    if p.run_this:
        if not hb.path_exists(p.summary_path):
            with open(p.summary_path, 'w') as f:
                f.write('layer,total_caloric_yield\n')
                for path in p.cleaned_yield_paths:
                    array = hb.as_array(path)
                    total = float(array[array != p.ndv].sum())
                    f.write(hb.file_root(path) + ',' + str(total) + '\n')
                    hb.log('Summed ' + hb.file_root(path) + ': ' + str(total))


if __name__ == '__main__':
    p = hb.ProjectFlow()

    # Constants live in the code at this level, and that is correct here: nothing
    # varies between runs yet. The moment one of these needs to differ per run
    # (or per machine), it belongs in a CSV -- that is templates 3 and 4. What
    # does NOT change when you get there is this block: configuring p in __main__
    # is the pattern the rest of this set keeps.
    p.ndv = -9999.0

    build_task_tree(p)
    p.execute()
