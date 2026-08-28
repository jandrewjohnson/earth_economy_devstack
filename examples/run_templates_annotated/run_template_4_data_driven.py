"""Template 4 of 4 — FULLY DATA-DRIVEN: scenarios CSV + parameters CSV.

    Configuration: level 4 of 4 -- + a parameters CSV; machine values leave the code
    Code layout:   single file -- tasks are defined here
    Ownership:     self-contained -- you own every file this run touches

See run_template_1_minimal.py in this directory for the three-axis map and
run_template_3_canonical.py for why run_project takes only p. This level
separates three things that are tangled together at every earlier level:

    scenarios   the rows of work this run iterates over ....... what VARIES
    parameters  values constant across all scenarios, including
                the machine-specific ones ...................... what is CONSTANT
    code        the pipeline .................................. changes when NEITHER does

WHERE THE run_project(p) RULE EARNS ITS KEEP
    Watch which CSV name is set where, at the bottom of this file:

        p.parameter_definitions_filename  both set by the CALLER: the full
        p.scenario_definitions_filename   definitions-filename block

    Since the 2026-08 amendment the caller sets the FULL block -- the project's
    interface manifest, one visible place naming every definitions file the run
    reads -- and a variant copies the block and overrides only the member that
    differs (usually the scenarios CSV). run_project only loads what the caller
    named. Under the rejected signature form each filename would be a keyword
    argument, growing once per class of CSV forever; ngfs_pnas, with six such
    filenames, showed where that leads.

WHEN THIS LEVEL IS THE RIGHT ONE
    A machine-specific value tries to enter your code (a credentials path, an ssh
    host, a scratch dir), or a collaborator needs to run your project on a machine
    where your paths do not exist. Both CSVs live in the tracked input_template/
    next to this run file; ProjectFlow copies anything missing into the project's
    untracked input/ on first run and NEVER overwrites the working copy, so
    per-machine values survive re-runs and never reach git.

WHAT ELSE THIS LEVEL DEMONSTRATES
    - An explicit tree with parent= nesting: child tasks get their dirs inside the
      parent's dir, so the filesystem mirrors the pipeline.
    - A cross-scenario task (yield_report) that consumes what the per-scenario
      task published, without knowing whether it ran this time or last week.
    - p.tasks_to_skip as the variant lever, set by the caller.

BEYOND THIS TEMPLATE
    The next things a real project adds are parallel iterators
    (p.add_iterator(..., run_in_parallel=1)) for per-zone work, and further CSV
    classes (outputs, figures, report sections) -- each of which is one more
    attribute here, and would have been one more keyword argument. Moving along
    the other two axes is a separate step: see run_template_seals_example.py in
    ../run_templates/. The full-scale reference implementation of this anatomy is
    ngfs_pnas; see examples/input_research_scripts/ngfs_pnas.py.
"""
import os

import numpy as np
import pandas as pd
import hazelbean as hb


def build_task_tree(p):
    """The one place that answers "what is this project's pipeline?".

    Always build the FULL tree here; variant runs pare it afterward via
    p.skip_tasks(), so the structure is identical across variants and only the
    run flags differ.
    """
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
                # Synthetic stand-in so this template runs with nothing
                # downloaded. In a real project the scenario row holds a ref_path
                # and this whole block is one line:
                #     path = p.get_path(row['yield_ref_path'])
                # which searches project input/, then base_data, then the cloud,
                # downloading if needed -- using p.data_credentials_path and
                # p.input_bucket_name, both of which came from parameters.csv.
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
                total = float(array[array != p.ndv].sum())  # p.ndv came from parameters.csv
                with open(summation_path, 'w') as f:
                    f.write('scenario_label,year,total_caloric_yield\n')
                    f.write(label + ',' + str(row['year']) + ',' + str(total) + '\n')
                hb.log('Summed ' + label + ': ' + str(total))


def yield_report(p):
    """Cross-scenario task: concatenate the per-scenario results into one table.

    It reads p.summation_paths, which yield_summations published ABOVE its gate.
    That is why this task works on a run where yield_summations was skipped
    entirely: the paths are always assigned, the files are already on disk.

    Note what is NOT here: an existence check. Expensive tasks are guarded so
    re-runs skip them; cheap aggregation tasks are not, because a guarded report
    would go stale the moment you add a scenario row. Guard on cost, not on habit.
    """
    p.report_path = os.path.join(p.cur_dir, 'yield_report.csv')

    if p.run_this:
        rows = [pd.read_csv(i) for i in p.summation_paths.values() if hb.path_exists(i)]
        pd.concat(rows, ignore_index=True).to_csv(p.report_path, index=False)
        hb.log('Wrote report across ' + str(len(rows)) + ' scenarios to ' + p.report_path)


def run_project(p):
    """Execute this project's pipeline against the ProjectFlow the caller configured.

    Reads from p, and only from p:
        p.scenario_definitions_filename   which rows of work to run (a variant changes this)
        p.tasks_to_skip                   optional; pares the tree for variant runs

    Everything else this project needs is set here, because no variant of it
    changes: the parameters CSV name, the base data location. Returns p.
    """
    build_task_tree(p)
    p.skip_tasks(p.tasks_to_skip)

    # PARAMETERS: constant across scenarios AND across variants. The caller named
    # the file (full-block rule); run_project only loads it. Vertical key,value,
    # hydrated onto p so tasks just use p.ndv, p.data_credentials_path, etc.
    # Blank values read as None. Machine-specific keys ship BLANK in the tracked
    # template; each machine fills in its own untracked input/ copy, so nothing
    # machine-specific is ever in the code or in git.
    hb.initialize_parameters(p, p.parameter_definitions_filename)
    # Cast the values used as numbers, so the tasks are honest about their types.
    p.ndv = float(p.ndv)
    p.n_rows = int(p.n_rows)
    p.n_cols = int(p.n_cols)

    # SCENARIOS: the rows of work. Add a row to extend the run; nothing else
    # changes. The caller chose which CSV, because that is exactly what a variant
    # run varies.
    hb.initialize_scenarios(p, p.scenario_definitions_filename)

    # Base data: checked for everything the model needs, with anything missing
    # downloaded. The directory must be named base_data to match the cloud bucket.
    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data')

    p.L = hb.get_logger(p.project_name)
    hb.log('Created ProjectFlow object at ' + p.project_dir +
           '\n    from script ' + p.calling_script +
           '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    # See run_template_3_canonical.py for the run_mode semantics.
    # The '_annotated' suffix keeps this set's project dir distinct from
    # ../run_templates/'s template 4; see run_template_3_canonical.py.
    p = hb.ProjectFlow(project_name='template_4_annotated', run_mode='check')
    p.parameter_definitions_filename = 'template_4_parameters.csv'
    p.scenario_definitions_filename = 'template_4_scenarios.csv'

    # Pare the tree for a variant run without forking the file:
    # p.tasks_to_skip = ['yield_report']

    run_project(p)
