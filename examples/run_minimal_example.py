"""The smallest possible ProjectFlow run file.

One task function, added explicitly with p.add_task(), then p.execute(). A function
becomes a task when you add it — nothing hidden. What you get for ~20 lines: an
organized project directory, one folder per task, skip-if-already-computed re-runs,
and logging. When you outgrow this — more tasks, variants, scenarios — collect the
add_task calls into a build_task_tree(p) function and graduate to the canonical form
with run_project(); see run_example_global_invest.py next to this file, and the
ProjectFlow conventions in docs/conventions.qmd.
"""
import os
import hazelbean as hb


def caloric_yield_sum(p):
    # Answers "what is the total caloric yield?" for a toy array. Everything
    # computationally intensive sits inside `if p.run_this:` and behind an
    # existence check, so re-runs skip completed work.
    p.summary_path = os.path.join(p.cur_dir, 'caloric_yield_sum.csv')
    if p.run_this:
        if not hb.path_exists(p.summary_path):
            import numpy as np
            yield_per_hectare = np.fromfunction(lambda i, j: (i + j) % 7, (100, 100))
            total = float(yield_per_hectare.sum())
            with open(p.summary_path, 'w') as f:
                f.write('statistic,value\ntotal_caloric_yield,' + str(total) + '\n')
            hb.log('Total caloric yield: ' + str(total))


if __name__ == '__main__':
    # Bare ProjectFlow() is git-aware: because this script lives inside a cloned repo,
    # the project dir is placed just OUTSIDE the repo at <repo_parent>/projects/minimal_example
    # (derived from this filename), so outputs never land in the git working tree.
    p = hb.ProjectFlow()
    p.add_task(caloric_yield_sum)
    p.execute()
