"""The smallest possible ProjectFlow run file ("Level 0").

There is no build_task_tree and no run_project here — when p.execute() is called
with an empty task tree, ProjectFlow adds every top-level function in this script
as a task, in the order they are defined. That is the whole contract, so a
Level-0 script must contain ONLY task functions at module level (put helpers
inside the tasks or in an imported module).

What you get for ~20 lines: an organized project directory, one folder per task,
skip-if-already-computed re-runs, and logging. When you outgrow this — variants,
scenarios, shared trees — graduate to the canonical form with build_task_tree()
and run_project(); see run_example_global_invest.py next to this file, and the
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
    p.execute()
