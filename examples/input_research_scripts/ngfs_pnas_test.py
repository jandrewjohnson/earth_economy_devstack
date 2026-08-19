"""Pared-down NGFS-PNAS test run.

Runs the SAME task tree as run_ngfs_pnas.py, but driven by a minimal scenarios CSV:
  - only the baseline + one policy scenario (below_2c, the 2 degC pathway),
  - a single future year (2024) reached by backward-interpolating the 2050 shocks,
  - a single AOI region (2705) so SEALS downscaling is fast.

Use this to smoke-test the whole pipeline end-to-end quickly. For the full model
(all scenarios, full 2023-2050 span, global AOI, full manuscript) run run_ngfs_pnas.py.

The only difference from the full run is the scenarios CSV filename below;
input_template/ngfs_pnas_scenarios_test.csv is copied to the project input/ on first run.

This is the 'check' variant of the test: it reuses the stable ngfs_pnas_test
project dir and standard ProjectFlow skip-existing logic, so only missing files
are recomputed. See run_ngfs_pnas_test_fresh_intermediate.py to rerun all
computation while keeping input/, and run_ngfs_pnas_test_full.py for a fully
fresh timestamped project dir.
"""
import hazelbean as hb

from run_ngfs_pnas import run_project

# START HERE: Failing on pick_modality. Next, to do is validating the below_2c policy run end-to-end at 2024 — your policy_*.cmf templates are placed and the test CSV points at them, so it's ready to exercise the full two-pass policy solve (just_cc → cc_es, combined-shock injection, fisheries line). Just say the word.

if __name__ == '__main__':
    p = hb.ProjectFlow(project_name='ngfs_pnas_test', run_mode='check')
    p.scenario_definitions_filename = 'ngfs_pnas_scenarios_test.csv'

    run_project(p)
