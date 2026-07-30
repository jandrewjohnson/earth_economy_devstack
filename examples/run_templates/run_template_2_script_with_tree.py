"""Several tasks, one build_task_tree(p). No CSVs yet; constants live in __main__.

    Configuration: level 2 of 4 -- a task tree, constants still inline
    Code layout:   single file -- tasks are defined here
    Ownership:     self-contained -- you own every file this run touches

Annotated version: ../run_templates_annotated/run_template_2_script_with_tree.py
"""
import os

import numpy as np
import hazelbean as hb


def build_task_tree(p):
    # add_task calls only. Use parent= to nest, run=0 to disable without deleting.
    p.yield_rasters_task = p.add_task(yield_rasters)
    p.cleaned_yield_task = p.add_task(cleaned_yield)
    p.yield_summary_task = p.add_task(yield_summary)


def yield_rasters(p):
    """Stand-in for acquiring inputs: writes four small yield rasters."""
    # Published above the gate, so downstream tasks get these paths even on a skipped run.
    p.yield_paths = [os.path.join(p.cur_dir, 'yield_per_cell_' + str(i) + '.tif')
                     for i in range(1, 5)]

    if p.run_this:
        for i, path in enumerate(p.yield_paths):
            if not hb.path_exists(path):
                # Real inputs: path = p.get_path('crops', 'yield_per_cell.tif')
                array = np.fromfunction(lambda r, c: ((r + c + i) % 7) - 1.0, (60, 120))
                # With a real input raster, pass geotiff_uri_to_match= instead of these four.
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
                # Larger than memory? This becomes hb.raster_calculator().
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

    p.ndv = -9999.0

    build_task_tree(p)
    p.execute()
