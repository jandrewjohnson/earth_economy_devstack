"""Minimal run file: one task.

    Configuration: level 1 of 4 -- one task, constants inline
    Code layout:   single file -- the task is defined here
    Ownership:     self-contained -- you own every file this run touches

Three independent axes describe a run file, and only Configuration is numbered;
a project sits somewhere on each. See docs/project_complexity.qmd for the model,
and ../run_templates_annotated/run_template_1_minimal.py for what each position
means and what moves you along an axis.
"""
import os

import numpy as np
import hazelbean as hb


def caloric_yield_sum(p):
    # Output paths above the gate; expensive work below it, behind an existence check.
    p.summary_path = os.path.join(p.cur_dir, 'caloric_yield_sum.csv')

    if p.run_this:
        if not hb.path_exists(p.summary_path):
            # Real inputs come from p.get_path('crops', 'yield_per_cell.tif').
            yield_per_hectare = np.fromfunction(lambda i, j: (i + j) % 7, (100, 100))
            total = float(yield_per_hectare.sum())

            with open(p.summary_path, 'w') as f:
                f.write('statistic,value\n')
                f.write('total_caloric_yield,' + str(total) + '\n')
            hb.log('Total caloric yield: ' + str(total))


if __name__ == '__main__':
    # Bare ProjectFlow() puts the project dir outside the repo, named after this file.
    p = hb.ProjectFlow()
    p.add_task(caloric_yield_sum)
    p.execute()
