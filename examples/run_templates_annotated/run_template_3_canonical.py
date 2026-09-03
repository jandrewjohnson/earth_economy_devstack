"""Template 3 of 4 — CANONICAL: run_project(p), driven by a scenarios CSV.

    Configuration: level 3 of 4 -- what varies is rows in a scenarios CSV
    Code layout:   single file -- tasks are defined here
    Ownership:     self-contained -- you own every file this run touches

See run_template_1_minimal.py in this directory for the three-axis map. This is
the level where run_project() appears, and the shape it takes was a real choice.
The rejected alternative put configuration in the signature:

    rejected:  def run_project(scenario_definitions_filename='template_3_scenarios.csv',
                               project_name='template_3_canonical',
                               run_mode='check',
                               tasks_to_skip=None):

    adopted:   def run_project(p):

THE RULE THAT REPLACES THE SIGNATURE
    run_project(p) sets what no variant ever changes.
    The caller sets what a variant might.

    When a constant needs to start varying, you move it one line up -- out of
    run_project and into the caller. There is no signature to edit, no keyword to
    add, and no default that can drift out of sync with the thing it duplicates.

WHY NOT DEFAULTS IN THE SIGNATURE
    - They restate what is already known. project_name restates this file's name
      (ProjectFlow derives it); the scenarios filename restates the project name
      plus a suffix; run_mode restates ProjectFlow's own default.
    - The signature grows once per class of CSV, forever. A real project accretes
      parameters, outputs, figures, and report sections; ngfs_pnas already has six
      such filenames, of which only three are parameters -- the split is arbitrary,
      and it happened because the signature got embarrassing, not because the
      knobs differ in kind. Here they are all just attributes on p.
    - A signature default is invisible to everything except Python. Attributes on
      p can be listed, logged, diffed between variants, and set from anywhere.
    - Configuring p in __main__ is what template 2 already does. This keeps the
      ladder continuous instead of introducing a new mechanism at rung 3.

THE COST, STATED HONESTLY
    You lose "bare run_project() always works" -- the caller must now hand it a
    ProjectFlow. A variant wrapper is four lines instead of three. In exchange,
    every knob a run uses is visible at the call site rather than in a callee's
    signature, and forgetting one raises a named AttributeError instead of
    silently running with somebody else's default.

THE ANATOMY (all four parts are required at this level)
    build_task_tree(p)   what the pipeline is; the only thing in it is add_task calls
    run_project(p)       how it is executed; returns p
    __main__ guard       importing this file must never start a run; it is also
                         where this project's own configuration lives
    a scenarios CSV      the rows of work -- what varies

    This template's three-column scenarios CSV is illustrative only; the real
    schema is specified in docs/proposed_changes.qmd.

THE VARIANT RUN IS FOUR LINES, NEVER A FORK
    See run_template_3_canonical_test.py next to this file.

PROMOTE TO TEMPLATE 4 WHEN
    A machine-specific value (a credentials path, an ssh host) tries to enter the
    code, or a second class of constants shows up that is not scenario-varying.
"""
import os

import numpy as np
import hazelbean as hb


def build_task_tree(p):
    p.yield_rasters_task = p.add_task(yield_rasters)
    p.yield_summations_task = p.add_task(yield_summations)


def yield_rasters(p):
    """One raster per scenario ROW -- the loop is now driven by the CSV."""
    p.scenario_yield_paths = {row['scenario_label']: os.path.join(p.cur_dir, row['scenario_label'] + '.tif')
                              for _, row in p.scenarios_df.iterrows()}

    if p.run_this:
        for _, row in p.scenarios_df.iterrows():
            path = p.scenario_yield_paths[row['scenario_label']]
            if not hb.path_exists(path):
                # Synthetic stand-in, parameterized by the CSV column. In a real
                # project the scenario column holds a ref_path and this line is
                # simply: path = p.get_path(row['yield_ref_path'])
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

    Same skip logic as template 2, now driven by the CSV: a finished scenario is
    skipped on re-run, delete one file to redo one scenario, and add a row to the
    CSV to extend the run -- no code changes in any of those cases.
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
    """Execute this project's pipeline against the ProjectFlow the caller configured.

    Reads from p, and only from p:
        p.scenario_definitions_filename   which rows of work to run (a variant changes this)
        p.tasks_to_skip                   optional; pares the tree for variant runs

    Anything read here that the caller did not set raises AttributeError naming
    the missing attribute -- which is the intended behavior. A missing knob should
    stop the run, not silently resolve to a default that belongs to a different run.

    Returns p.
    """
    build_task_tree(p)
    # The tree is always built in full and pared afterward, so its structure is
    # identical across variants and only the run flags differ. ProjectFlow
    # initializes tasks_to_skip to None, so a run that sets nothing skips nothing.
    p.skip_tasks(p.tasks_to_skip)

    # Project constants: values no variant changes, so they are set here rather
    # than by the caller. Template 2 kept its constants in __main__ because it had
    # no run_project to put them in; from here on this is their home. Template 4
    # replaces exactly this block with a parameters CSV read into the same
    # attributes, which is the whole of that promotion.
    p.ndv = -9999.0

    # The scenarios CSV: the rows of work. Its tracked home is the input_template/
    # directory next to this run file; ProjectFlow copied anything missing into the
    # project's untracked input/ when the caller constructed it, and never
    # overwrites the working copy -- so your edits survive re-runs.
    # hb.initialize_scenarios loads p.scenarios_df and hydrates row 0 onto p.
    hb.initialize_scenarios(p, p.scenario_definitions_filename)

    # Base data: the model checks here for everything it needs and downloads
    # anything missing. The directory must be named base_data to match the naming
    # convention on the cloud bucket. One base_data serves every project, and no
    # variant of this project changes it -- so it belongs here, not in the caller.
    p.base_data_dir = os.path.join(p.user_dir, 'Files', 'base_data')

    p.L = hb.get_logger(p.project_name)
    hb.log('Created ProjectFlow object at ' + p.project_dir +
           '\n    from script ' + p.calling_script +
           '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    # This block is this project's configuration, in visible greppable code rather
    # than in a callee's signature. A variant run is another block just like it --
    # see run_template_3_canonical_test.py.
    #
    # run_mode selects how much prior work is reused:
    #   'check'              stable project dir; standard skip-existing logic, so
    #                        only missing files are recomputed. What you want
    #                        almost always.
    #   'fresh_intermediate' stable project dir, but intermediate/ and output/ are
    #                        deleted first so all computation reruns while input/
    #                        (your edited CSVs) is kept. Refused unless the project
    #                        name contains 'test'.
    #   'full'               a fresh timestamped project dir per run; also exercises
    #                        base-data downloads, i.e. the first-run experience on
    #                        a new machine.
    #
    # The project_name carries the '_annotated' suffix only so that this set's
    # results never land in the same project dir as ../run_templates/'s template 3,
    # which shares this filename. In a real project the name is just
    # the project's name. project_name IS the identity of a run: two runs with the
    # same name share (and resume) each other's results.
    p = hb.ProjectFlow(project_name='template_3_annotated', run_mode='check')
    p.scenario_definitions_filename = 'template_3_scenarios.csv'

    run_project(p)
