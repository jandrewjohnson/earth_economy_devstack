"""Template 1 of 4 — MINIMAL: one task, added explicitly.

    Configuration: level 1 of 4 -- one task, constants inline
    Code layout:   single file -- the task is defined here
    Ownership:     self-contained -- you own every file this run touches

THREE AXES, NOT ONE LADDER
    A run file's complexity is three independent questions, and a project sits
    somewhere on each. Only the first is numbered, because only the first is a
    ladder you climb in order.

    Configuration -- how a run varies
        1  one task; constants inline
        2  a task tree; constants inline
        3  + a scenarios CSV: the rows of work become data
        4  + a parameters CSV: machine-specific values leave the code

    Code layout -- where the code lives
        single file      tasks defined in the run file (templates 1-4)
        split            tasks in <project>_tasks.py, science helpers in
                         <project>_functions.py, science-unaware helpers in
                         <project>_utils.py (promotion candidates for hazelbean),
                         tree builders in <project>_initialize_project.py
        library package  the above installed and imported by many projects
                         (run_template_seals_example.py)

    Ownership -- who owns the code you run
        self-contained      you own every file the run touches (templates 1-4)
        devstack developer  you import a devstack library and could edit it
                            (run_template_seals_example.py)
        downstream user     the library is a read-only dependency in your own
                            repo (seals: run_seals_standalone_project_template.py)

    The axes are independent. global_invest's service runners are Configuration
    level 2 with a library-package layout; nothing forces you up one axis before
    moving along another. Templates 1-4 hold Code layout and Ownership FIXED so
    that Configuration is the only thing changing between them -- that is what
    makes them a diff. run_template_seals_example.py then moves the other two.

THIS DIRECTORY
    The annotated set: the same code as ../run_templates/ with the reasoning
    written out. Read these once; copy from ../run_templates/.

    Templates 1 and 2 deliberately keep the bare hb.ProjectFlow() constructor, so
    they share a project dir with ../run_templates/'s templates 1 and 2 --
    harmless, since they compute exactly the same thing. Templates 3 and 4 carry
    distinct project names.

THE RULE THAT APPEARS AT CONFIGURATION LEVEL 3

    run_project(p) sets what no variant ever changes.
    The caller sets what a variant might.

    When a constant needs to start varying, you move it one line up, out of
    run_project and into the caller. No signature to edit, no keyword to add, no
    default to keep in sync -- and nothing grows as a project accumulates CSVs.

    Templates 1 and 2 have no run_project to configure, so they configure p in
    __main__. Level 3 keeps exactly that shape and only factors the running part
    into run_project(p), so the ladder stays continuous.

  1. minimal ............ this file. One task. ~25 lines.
  2. script_with_tree ... several tasks, a build_task_tree(p), constants inline.
  3. canonical .......... run_project(p) + a scenarios CSV; variants are data.
     + _test.py wrapper . the variant, four lines, never a fork.
  4. data_driven ........ + a parameters CSV; nothing machine-specific in code.
  + seals_example ...... same Configuration level 3, but layout and ownership move.

WHEN THIS LEVEL IS THE RIGHT ONE
    You have one thing worth computing, and you want it cached.

WHAT YOU GET FOR THESE 25 LINES
    A project directory outside your repo, one folder per task, skip-if-already-
    computed re-runs, and logging. Run it twice: the second run finishes instantly
    because the output already exists. That is the honest trade: about the effort
    of a throwaway script, for benefits it took the devstack six iterations to
    reach (see docs/project_complexity.qmd).

MOVE UP THE CONFIGURATION AXIS WHEN
    You add a second task, or you catch yourself wanting to name the pipeline.
"""
import os

import numpy as np
import hazelbean as hb


def caloric_yield_sum(p):
    # A plain function becomes a TASK at the p.add_task() call below -- nothing
    # is hidden. The task gets its own output folder at p.cur_dir.
    #
    # Output paths are declared ABOVE the p.run_this gate so that even a skipped
    # run of this task still publishes where its products live. Everything
    # expensive goes below the gate, behind an existence check.
    p.summary_path = os.path.join(p.cur_dir, 'caloric_yield_sum.csv')

    if p.run_this:
        if not hb.path_exists(p.summary_path):
            # Synthetic stand-in for a real raster, so this template runs with no
            # data downloaded. In a real project this line would be
            # array = hb.as_array(p.get_path('crops', 'yield_per_cell.tif'))
            yield_per_hectare = np.fromfunction(lambda i, j: (i + j) % 7, (100, 100))
            total = float(yield_per_hectare.sum())

            with open(p.summary_path, 'w') as f:
                f.write('statistic,value\n')
                f.write('total_caloric_yield,' + str(total) + '\n')
            hb.log('Total caloric yield: ' + str(total))


if __name__ == '__main__':
    # The __main__ guard is mandatory in the EE spec: importing a run file must
    # never start a run.
    #
    # Bare ProjectFlow() is git-aware. Because this script lives inside a cloned
    # repo, the project dir is placed just OUTSIDE the repo, at
    # <repo_parent>/projects/template_1_minimal (derived from this filename), so
    # outputs never land in the git working tree. Passing project_dir= overrides.
    p = hb.ProjectFlow()
    p.add_task(caloric_yield_sum)
    p.execute()
