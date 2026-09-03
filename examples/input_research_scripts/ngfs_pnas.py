import os
import hazelbean as hb
import gtappy.gtappy_initialize_project as gtappy_initialize_project
import gtap_invest.gtap_invest_tasks as gtap_invest_tasks
import gtap_invest.gtap_invest_initialize_project as gtap_invest_initialize_project
import seals.seals_initialize_project as seals_initialize_project
import gtappy.gtappy_utils as gtappy_utils, gtappy.gtappy_tasks as gtappy_tasks
import seals.seals_generate_base_data as seals_generate_base_data
import seals.seals_process_coarse_timeseries as seals_process_coarse_timeseries
import seals.seals_main as seals_main
import seals.seals_visualization_tasks as seals_visualization_tasks
import seals.seals_tasks as seals_tasks

from gtap_invest_viz.config import (
REPORT_EXCLUDE_PATTERNS, REPORT_EXCLUDE_UNLESS,
INCOME_GROUPS, GEOGRAPHIC_REGIONS,
REGION_NAMES, get_region_display_name,
INCOME_GROUP_ORDER,
)


def build_task_tree(p):
    """Two-pass GTAP pipeline driven by shock_config column in scenarios CSV.

    shock_config = "just_cc cc_es" means each policy scenario gets run twice:
      Pass 1 (just_cc): CC shocks only (yield + labor) -- produces LCOV for SEALS
      Pass 2 (cc_es):   CC + ES shocks (yield + labor + carbon + pollination + fisheries)

    Always builds the FULL tree; variant runs pare it afterward via
    p.skip_tasks(p.tasks_to_skip) in run_project, so the tree structure is
    identical across variants and only run flags differ.
    """

    # =========================================================================
    # STEP 0: Convert GTAP base data to CSV
    # =========================================================================
    p.base_data_as_csv_task = p.add_task(gtappy_tasks.base_data_as_csv)

    # =========================================================================
    # STEP 1: Initial baseline GTAP run (single base year, starting point)
    # =========================================================================
    p.initial_gtap_runs_task = p.add_task(gtappy_tasks.initial_gtap_runs)
    p.solve_gtap_initial_task = p.add_task(gtap_invest_tasks.solve_gtap_initial)

    # =========================================================================
    # STEP 2: Build combined yield + labor shocks for just_cc pass
    # =========================================================================
    p.crop_yield_from_cc_task = p.add_task(gtap_invest_tasks.crop_yield_from_cc)
    p.build_combined_afeall_just_cc_task = p.add_task(gtap_invest_tasks.build_combined_afeall_just_cc)

    # =========================================================================
    # STEP 3: Generate ALL CMFs (just_cc + cc_es), then solve baseline + just_cc.
    # gtap_runs generates CMFs for all passes. solve_gtap_scenarios then dispatches each CMF to the
    # chosen backend (VM/SC/local) via solve_gtap_cmf — baseline first (solves afelabreg
    # 2023-2050), then just_cc policy scenarios. No separate copy step: the dispatch ships
    # only each CMF + its referenced inputs, per-file.
    # =========================================================================
    p.gtap_runs_task = p.add_task(gtappy_tasks.gtap_runs)
    # copy_gtap_runs_to_vm removed — solve_gtap_scenarios now dispatches via solve_gtap_cmf, which
    # ships only the CMF + its referenced inputs per-file (no more whole-dir copy).
    p.solve_gtap_scenarios_task = p.add_task(gtap_invest_tasks.solve_gtap_scenarios)

    # =========================================================================
    # STEP 4: Extract LCOV from just_cc results → regional projections for SEALS
    # =========================================================================
    p.extract_lcov_for_seals_task = p.add_task(gtap_invest_tasks.extract_lcov_for_seals)
    p.gtap_econ_run_luc_vector_task = p.add_task(gtap_invest_tasks.gtap_econ_run_luc_vector)

    # =========================================================================
    # STEP 5: SEALS — downscale just_cc LCOV to 300m LULC maps (2050 only)
    # Uses PIK MAgPIE for coarse spatial patterns, GTAP LCOV for regional totals
    # =========================================================================
    p.project_aoi_task = p.add_task(seals_tasks.project_aoi)
    p.fine_processed_inputs_task = p.add_task(seals_generate_base_data.fine_processed_inputs)
    p.generated_kernels_task = p.add_task(seals_generate_base_data.generated_kernels, parent=p.fine_processed_inputs_task, creates_dir=False)
    p.lulc_clip_task = p.add_task(seals_generate_base_data.lulc_clip, parent=p.fine_processed_inputs_task, creates_dir=False)
    p.lulc_simplifications_task = p.add_task(seals_generate_base_data.lulc_simplifications, parent=p.fine_processed_inputs_task, creates_dir=False)
    p.lulc_binaries_task = p.add_task(seals_generate_base_data.lulc_binaries, parent=p.fine_processed_inputs_task, creates_dir=False)
    p.lulc_convolutions_task = p.add_task(seals_generate_base_data.lulc_convolutions, parent=p.fine_processed_inputs_task, creates_dir=False)
    p.coarse_change_task = p.add_task(seals_process_coarse_timeseries.coarse_change)
    p.extraction_task = p.add_task(seals_process_coarse_timeseries.coarse_extraction, parent=p.coarse_change_task)
    p.coarse_simplified_task = p.add_task(seals_process_coarse_timeseries.coarse_simplified_proportion, parent=p.coarse_change_task)
    p.coarse_simplified_ha_task = p.add_task(seals_process_coarse_timeseries.coarse_simplified_ha, parent=p.coarse_change_task)
    p.coarse_simplified_ha_difference_from_previous_year_task = p.add_task(seals_process_coarse_timeseries.coarse_simplified_ha_difference_from_previous_year, parent=p.coarse_change_task)
    p.regional_change_task = p.add_task(seals_process_coarse_timeseries.regional_change)
    p.allocations_task = p.add_iterator(seals_main.allocations)
    p.allocation_zones_task = p.add_iterator(seals_main.allocation_zones, run_in_parallel=p.run_in_parallel, parent=p.allocations_task)
    p.allocation_task = p.add_task(seals_main.allocation, parent=p.allocation_zones_task)
    p.stitched_lulc_simplified_scenarios_task = p.add_task(seals_main.stitched_lulc_simplified_scenarios)

    # =========================================================================
    # STEP 6: Prepare ES shocks from pre-computed raw_dependencies (not from SEALS)
    # Reads Justin's dependency CSVs at 2050, interpolates linearly to annual
    # =========================================================================
    p.prepare_es_shocks_task = p.add_task(gtap_invest_tasks.prepare_es_shocks)

    # =========================================================================
    # STEP 7: Combine CC + ES → combined afeall HARs for second GTAP pass
    # =========================================================================
    p.build_combined_afeall_cc_es_task = p.add_task(gtap_invest_tasks.build_combined_afeall_cc_es)

    # =========================================================================
    # STEP 8: Second GTAP pass (cc_es — climate + nature shocks)
    # =========================================================================
    # copy_gtap_runs_to_vm_cc_es removed — dispatch ships per-file (see STEP 3 note).
    p.solve_gtap_scenarios_cc_es_task = p.add_task(gtap_invest_tasks.solve_gtap_scenarios_cc_es)

    # =========================================================================
    # STEP 9: Extraction — SL4/HAR → extended variable CSVs
    # Reads all scenarios (just_cc + cc_es + baseline) from gtap_runs/.
    # raw_csvs skips per-year if already extracted. vars/extended_vars always re-run.
    # To force full re-extract: delete intermediate/econ_results/
    # =========================================================================

    p.econ_results_task = p.add_task(gtappy_tasks.econ_results)
    p.raw_csvs_task = p.add_task(gtappy_tasks.raw_csvs, parent=p.econ_results_task)
    p.metadata_task = p.add_task(gtappy_tasks.metadata, parent=p.econ_results_task)
    p.variables_metadata_by_dims_task = p.add_task(gtappy_tasks.variables_metadata_by_dims, parent=p.econ_results_task)
    p.variables_by_dims_task = p.add_task(gtappy_tasks.variables_by_dims, parent=p.econ_results_task)
    p.vars_task = p.add_task(gtappy_tasks.vars, parent=p.econ_results_task)
    p.extended_vars_task = p.add_task(gtappy_tasks.extended_vars, parent=p.econ_results_task)

    # Path overrides — point to actual data directories
    p.extended_vars_dir = os.path.join(p.intermediate_dir, 'econ_results', 'extended_vars')
    p.gtap_runs_dir = os.path.join(p.intermediate_dir, 'gtap_runs')
    p.gtap_econ_run_luc_vector_dir = os.path.join(p.intermediate_dir, 'gtap_econ_run_luc_vector')
    p.extract_lcov_for_seals_dir = os.path.join(p.intermediate_dir, 'extract_lcov_for_seals')

    # =========================================================================
    # STEP 10: Visualization — figures + HTML report
    # Reads ngfs_pnas_figures.csv (one row per figure).
    # Reads ngfs_pnas_sections.csv (report structure).
    # Reads ngfs_pnas_figure_descriptions.md (captions).
    # Output: intermediate/gtap_invest_report/
    # =========================================================================

    import gtap_invest_viz
    from gtap_invest_viz import gtap_invest_viz_tasks

    p.report_parent_task = p.add_task(gtap_invest_viz_tasks.gtap_invest_report)
    p.get_vars_task = p.add_task(gtap_invest_viz_tasks.get_all_extended_vars, parent=p.report_parent_task, skip_existing=1, creates_dir=False)
    p.visualize_task = p.add_task(gtap_invest_viz_tasks.visualize_all_variables, parent=p.report_parent_task, skip_existing=0)
    p.summary_task = p.add_task(gtap_invest_viz_tasks.generate_summary_table, parent=p.report_parent_task, skip_existing=1)
    p.report_task = p.add_task(gtap_invest_viz_tasks.generate_automated_report, parent=p.report_parent_task, skip_existing=0)

    # =========================================================================
    # STEP 11: Paper manuscript — text + generated figures → .md + .docx
    # Reads input/ngfs_pnas_paper_text.md with {{figure_id}} placeholders.
    # Resolves each placeholder to the generated PNG from Step 10.
    # Output: intermediate/gtap_invest_report/generate_manuscript/
    # =========================================================================

    p.manuscript_task = p.add_task(gtap_invest_viz_tasks.generate_manuscript, parent=p.report_parent_task, skip_existing=0)


def run_project(p):
    """Execute the NGFS-PNAS pipeline against the ProjectFlow the caller configured.

    Reads p.scenario_definitions_filename, and optionally p.tasks_to_skip. Returns p.

    The full manuscript run and every test wrapper share this pipeline unchanged;
    what differs between them is the scenarios CSV, the project name, and the
    run_mode the caller sets, never the code here.
    """
    # TRICKY LINE, this dir would typically be set by the task, but if you don't run that task, you can have this be assigned manually.
    # p.gtap_runs_dir set below after p.user_dir is defined

    p.figure_definitions_filename = 'ngfs_pnas_figures.csv'
    p.section_definitions_filename = 'ngfs_pnas_sections.csv'
    p.figure_descriptions_filename = 'ngfs_pnas_figure_descriptions.md'

    # p.gtap_runs_dir is set in build_task_tree (line 125)

    p.run_in_parallel = 1 # Must be set before building the task tree if the task tree has parralel iterator tasks.

    build_task_tree(p)
    p.skip_tasks(tasks_to_skip)

    # Set the base data dir. The model will check here to see if it has everything it needs to run.
    # If anything is missing, it will download it. You can use the same base_data dir across multiple projects.
    # Additionally, if you're clever, you can move files generated in your tasks to the right base_data_dir
    # directory so that they are available for future projects and avoids redundant processing.
    # The final directory has to be named base_data to match the naming convention on the google cloud bucket.
    p.base_data_dir = os.path.join(p.user_dir, 'Files/base_data')

    # ProjectFlow downloads all files automatically via the p.get_path() function. If you want it to download from a different 
    # bucket than default, provide the name and credentials here. Otherwise uses default public data 'gtap_invest_seals_2023_04_21'.
    p.data_credentials_path = None
    p.input_bucket_name = None
    
    # ODD NOTE: This must come before initialize_parameter_Definitions because that calls set_derived_attributes, which has a default option set.
    p.processing_resolution = 4.0 # In degrees. Must be in pyramid_compatible_resolutions
    

    # Parameters defined here are constant across scenarios
    p.parameter_definitions_filename = 'ngfs_pnas_parameters.csv'
    p.parameter_definitions_path = os.path.join(p.input_dir, p.parameter_definitions_filename)
    gtappy_initialize_project.initialize_parameter_definitions(p)
       
    # Variables defined here are updated for each scenario row that is iterated over
    p.scenario_definitions_path = os.path.join(p.input_dir, p.scenario_definitions_filename)
    gtappy_initialize_project.initialize_scenario_definitions(p)
    
    # Variables defined here are updated for each scenario row that is iterated over
    p.output_definitions_filename = 'ngfs_pnas_outputs.csv'
    p.output_definitions_path = os.path.join(p.input_dir, p.output_definitions_filename)
    gtappy_initialize_project.initialize_output_definitions(p)

    # SEALS output definitions — no longer used in the main pipeline.
    # Figures are now driven by ngfs_pnas_figures.csv via the unified dispatch loop.
    # p.seals_output_definitions_filename = 'seals_outputs.csv'
    # gtappy_initialize_project.initialize_seals_output_definitions(p)

    ### HUGE ADDITION: Generates multiple coarse downscalings. this selects which to use for fine downscaling.
    p.aggregation_method_string = 'covariate_additive'
    # p.aggregation_method_string = 'covariate_multiply_regional_change_sum'
                      
    # # SEALS is based on an extremely comprehensive region classification system defined in the following geopackage.
    # global_regions_vector_ref_path = os.path.join('cartographic', 'ee', 'ee_r264_correspondence.gpkg')
    # p.global_regions_vector_path = p.get_path(global_regions_vector_ref_path)

    # # Set processing resolution: determines how large of a chunk should be processed at a time. 4 deg is about max for 64gb memory systems
    # p.processing_resolution = 1.0 # In degrees. Must be in pyramid_compatible_resolutions

    gtappy_initialize_project.set_advanced_options(p)
    
    
    seals_initialize_project.set_advanced_options(p)
    
    
    # This is a poorly supported option that chooses whether to use teh projections labor productivity veruss the endogenously determined one.
    # For the bau_no_es, we draw from the exogenous projections and swap those in for GDP. This makes countries have GDP growth rates that
    # match baseline projections. However, for subsequent scenarios, we want to use the endogenously determined labor productivity so that they are comparable
    p.force_standard_productivity = 0 # note this has to be after set_advanced_options cause it overrides that
    
    # In case you want to analyze the results of a statically provided model, can set this to True
    p.get_gtap_runs_dir_from_scenarios = 1 # If false, just assume that all of the files were put in a flat folder. this is how erwin currently does it.
    
    # Backend connection (vm_ssh_host, vm_disk_prefix, gempack_dir; sc_ssh_host / sc_scratch
    # for the cluster) is read from parameters.csv by initialize_parameter_definitions.
    # The tracked input_template/ CSV ships blank values; copy it into the untracked input/
    # and fill your machine's values there (or set GTAP_* in machine.env). Nothing
    # machine-specific stays in the code.

    p.L = hb.get_logger(p.project_name)
    hb.log('Created ProjectFlow object at ' + p.project_dir + '\n    from script ' + p.calling_script + '\n    with base_data set at ' + p.base_data_dir)

    p.execute()

    return p


if __name__ == '__main__':
    # run_mode: 'check' resumes in place | 'fresh_intermediate' rebuilds all
    # computation but keeps input/ (test projects only) | 'full' timestamps a new dir.
    p = hb.ProjectFlow(project_name='ngfs_pnas', run_mode='check')
    p.scenario_definitions_filename = 'ngfs_pnas_scenarios.csv'

    run_project(p)
