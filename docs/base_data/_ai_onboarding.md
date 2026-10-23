# Base data store: onboarding for an AI assistant

Hand this file to a new conversation to pick up work on the Earth-Economy base data store. It summarises the design,
the code, the current state and the working rules agreed while building it (October 2026). The leading underscore
keeps the devstack Quarto site from rendering it.

Read these first, in this order; they are the authoritative versions of what is summarised here:

1. `earth_economy_devstack/docs/proposal_base_data_store.qmd`: the design, every decision and why, and the implementation order (steps A to G).
2. `earth_economy_devstack/docs/contributing_base_data.qmd`: how lab members submit data and how curators promote and publish it, including editing the website.
3. `earth_economy_devstack/docs/_conventions_reference.md`: the EE Spec conventions, especially "get_path and ref_path" and "Base data dataset folders and `raw/`".
4. `earth_economy_devstack/docs/pogs.qmd`: the POG raster specification.
5. `hazelbean/hazelbean_dev/hazelbean/base_data_processing.py`: the module docstring and function docstrings.

## The goal

Base data (shared input data for SEALS, GTAP-InVEST, global_invest and the rest of the devstack) used to live in
scattered, diverging copies: an out-of-date Google Cloud bucket, the TEEMs Google Drive, and local folders. It now has
one canonical, versioned store:

- **Cloudflare R2 is the truest source.** Bucket `teems-public-data` in the Cloudflare account
  `5df720878481d59b0cac2864b632248c` (the jandrewjohnson@gmail.com login), served publicly at `https://data.teemlabs.org`.
  A private bucket (`teems-private-data`, for paid access) is planned, not created.
- **The maintainer's local `~/Files/base_data` is the reference copy** it is published from.
- **Google Drive** becomes a submissions inbox (`NatCapTEEMs/Files/base_data_submissions/`, beside `base_data/`) and,
  later, a generated read-only mirror. The old Google Cloud bucket is abandoned, not migrated.
- **Every raster is a POG** (Pyramidal Cloud-Optimized GeoTIFF on one fixed global lattice of nested rungs).
- `p.get_path()` will eventually resolve ref paths from R2 (step D, not built).

## Vocabulary

- **Ref path:** a dataset's path relative to the base_data root, e.g. `lulc/esa/lulc_esa_2022.tif`. Lowercase, forward
  slashes, meaning in the name, never revisions (`_v2`, `_final`), never starting with `_` or `static/`.
- **Publish:** write to R2. The only operation that does. Always through `hb.publish_base_data`.
- **Promote:** move a lab member's submission from `base_data_submissions/` into `base_data/` with an ingestion script
  and manifest row. Writes nothing to R2. `hb.promote_base_data_submission` is reserved for step F and not built;
  promotion is done by hand.
- **Release:** one publication, ID `YYYY.MM.DD.N`. **Manifest**, **ingestion script**, **`raw/`**: see below.
- **Curator:** someone with R2 write credentials (currently only Justin).

## Layout

### In R2

| Key | What |
|---|---|
| `<ref path>` | Current version, at its plain path. Cache-Control `public, max-age=3600`. |
| `static/<ref path minus ext>/v<release, dots as underscores><ext>` | An archived (replaced) version, e.g. `static/pyramids/ha_per_cell_10sec/v2026_10_19_1.tif`. Skipped with `archive_previous=False`. |
| `_staging/<ref>/<sha16>.<ext>` | New bytes waiting for their release to commit. |
| `_catalogue/<ref>/<release>.json` | One entry per dataset version: files (size, sha256, md5), lattice, semantics (variable class, stats), licence, description, provenance (`source`, `code`, `promoted_from`, `published_by`, `published_at`, `note`), `previous` (with its `archive_key`). |
| `_release/<release>.json`, `_release/latest.json` | Full snapshot of every dataset's version and `dataset_sha256`; latest pointer (no-cache). |
| `index.html`, `<folder>/index.html`, `teems_logo.png` | The browsable website (max-age 300). |

Commit protocol: claim `_release/<id>.json` with `If-None-Match: *`, write catalogue entries, then compare-and-swap
`latest.json` with `If-Match <etag>`. On a 409/412 conflict, delete what this run wrote and tell the curator to rerun.
Only after the commit are staged files copied (server side) over their plain paths ("Moving into place inside R2").
The public domain doesn't expose `x-amz-meta-*`; ETag is the md5 for single-part uploads (`-N` suffix for multipart),
so readers should use `If-Match` on the ETag.

### Dataset folders in local `base_data`

```
base_data/lulc/esa/
    lulc_esa_base_data_ingestion.py    the lineage: raw/ -> POGs -> manifest. The only code allowed in base_data.
    lulc_esa_base_data_manifest.csv    one row per dataset, UTF-8 with BOM
    lulc_esa_1992.tif ... lulc_esa_2022.tif
    raw/                               input exactly as downloaded; never listed, uploaded or resolved by get_path
```

Manifest columns: `ref_path, kind, tier, variable_class, license, units, data_source, description, code`. Only
`kind=pog`, `tier=public` publish so far. `variable_class` is `extensive | intensive | categorical | covariate`.

Three kinds of ingestion script: (1) raw ingest living entirely in base_data (`lulc/esa`); (2) a thin call to code in
another repo (`pyramids`, calling `hb.write_ha_per_cell_pog`); (3) a bespoke move of a finished project's outputs (also
what a promoted submission usually becomes). A step whose history is unknown is a function that says so (e.g.
`ingest_cci_v2_0_7_from_raw` for ESA 1992-2015). The script's docstring is published as the folder page's About section.

A script with more than one step may be a **ProjectFlow run file** in the single-file form (`build_task_tree`,
`run_project(p)`, `__main__` guard): `lulc/esa/seals7` is the example. Being a base data script it departs from the
run-file conventions in two ways, both now stated in `_conventions_reference.md` ("Base data dataset folders"): its tasks
write straight to the ref paths under base_data, not to `p.cur_dir`, so the project folder (`~/Files/projects/<name>`,
placed with `extra_dirs=["Files", "projects"]` because base_data is no git repo) holds only logs; and its scenarios CSV
is `<name>_base_data_scenarios.csv` flat beside the script (passed to `hb.initialize_scenarios` as a full path), not in
`input_template/`, because the CSV is lineage and a dataset folder is a flat record. Decided 2026-10-20 after debate.

**`dry_run` may be a date** (`hb.resolve_dry_run`, in `base_data_processing.py`, called by all four public store
functions): a bool passes through; `"2026-10-20"` means a real run on that day or later and a dry run once it has passed,
so a script never stays armed. One log line says which.

## The code

### hazelbean (`~/Files/hazelbean/hazelbean_dev`, branch `feature_base_data_store`, UNCOMMITTED)

- `hazelbean/base_data_processing.py` (new; imported in `__init__.py`). Public:
  - `add_directory_to_base_data(source_dir, ref_folder, manifest_path, license, units, data_source, description, code=None, variable_class=None, overrides=None, include=None, include_subdirectories=True, make_pogs=True, overwrite=False, base_data_dir=None, parallel=True, n_workers=None, dry_run=True, client=None)`: places/keeps files, converts non-POGs in place (deleting originals), writes manifest rows, ends with a publish dry run.
  - `find_base_data_manifests(base_data_dir=None)`.
  - `publish_base_data_from_manifests(base_data_dir=None, manifest_paths=None, note=None, archive_previous=True, parallel=True, n_workers=None, dry_run=True, client=None, site_dir=None)`: combines manifests, statuses (`new, changed, unchanged, needs_pog, unfinished, missing_locally, unsupported, not_in_manifest`), converts, hashes, publishes; with `site_dir`, every real run rebuilds the website.
  - `publish_base_data(sources, ref_paths, note, license, units, data_source, description, code=None, archive_previous=True, parallel=True, n_workers=None, dry_run=False, client=None)`: the gate and the commit protocol.
  - `write_base_data_index_pages(site_dir, base_data_dir=None, manifest_paths=None, output_dir=None, dry_run=True, client=None)`: builds the website from templates + manifests + latest release + catalogue + `static/` listing; renders folder pages with Quarto in a temp project; uploads with `dry_run=False`.
  - `check_pog_publication_status(source_path, ref_path)`: the store's own gate (naming rules, `hb.is_path_pog(full_check=True)`, dependencies, hashes).
  - `resolve_dry_run(dry_run)`: bool or date to bool, see above.
  - Private helpers: `_run_each` / `_run_each_collecting_failures` (ThreadPoolExecutor, `hb.available_cpu_count() - 1` workers), `_read_manifest`, `_get_archive_key`, `_get_staging_key`, `_get_dataset_sha256`, page helpers (`_get_dataset_table_html`, `_get_docstring_html`, `_read_module_docstring`, `_get_docstring_texts`, `_get_folder_tree_html`, `_linkify`, `_format_size`, `_format_resolution`, `_natural_sort_key`, `_fill_placeholders`). Since 2026-10-21 a folder `_collections.yml` doesn't list gets its card tagline and text from its ingestion script's first docstring paragraph, and the landing page (`%%FOLDER_TREE%%` in `_landing.html`) lists every published folder as a tree; the pages name three levels: a **collection** (top-level folder) holds **datasets**, and a dataset holds **derived products**; a collection page heads its subfolder cards "Datasets", any deeper page heads them "Derived products", under the cards comes the same tree pared to that folder, and the table of a folder's rows is headed "Files" (on the pages, a dataset is a folder such as `lulc/esa`; the catalogue still calls each published file a dataset).
- `hazelbean/cloud_utils.py`: `get_r2_client` (boto3, lazy import, `max_pool_connections=64`), `get_r2_error_status`, `read_r2_json`, `write_r2_json`, `list_r2_keys`, `read_r2_object_metadata`, `upload_path_to_r2`, `copy_r2_object`, `R2TransferProgress`.
- `hazelbean/pog.py`: `get_pog_info(path)` reads stored exact statistics from metadata (GDAL's `GetStatistics(0,1)` recomputes and writes `.aux.xml` sidecars; never use it on POGs).
- `hazelbean/utils.py`: `hash_file_path` raises on errors. `project_flow.py` uses it. `setup.py`: extra `store = ["boto3"]`.
- `scripts/base_data/regenerate_pyramids.py`: columns, VRTs, match rasters and zone ids for `pyramids/`.
- Tests: `hazelbean_tests/unit/test_base_data_processing.py` (an in-memory `FakeR2`; page tests skip without Quarto), plus additions in `test_pog_spec.py` and `test_utils.py`. `hazelbean_tests/tools/utilities/manual_test_publish_base_data_r2.py` is a manual check against a throwaway bucket. Unit suite: 266 passed at last run. Run with `python -m pytest hazelbean_tests/unit/`.
- **Other people's in-progress files are also modified on this branch and must NOT be included in base-data commits:** `cog.py`, `raster_vector_interface.py`, `hazelbean_tests/integration/test_data_processing.py`, `hazelbean_tests/test_spatial_utils.py`, `hazelbean_tests/tools/utilities/manual_test_parallel.py`, `hazelbean_tests/unit/test_arrayframe.py`.

### earth_economy_devstack (`~/Files/earth_economy_devstack`, branch `main`, UNCOMMITTED)

- `publish_base_data.py`: the curator's runner (`DRY_RUN`, `NOTE`, `BASE_DATA_DIR`, `SITE_DIR` = `docs/base_data`).
- `docs/base_data/`: the website templates, `_landing.html` (custom animated landing page), `_folder_page.qmd`, `_styles.css`, `_collections.yml` (collection/folder titles and text, edited ad hoc), `teems_logo.png`; and `index.qmd` (the devstack's Base Data page, moved from `docs/base_data.qmd`, with an alias). Underscored files are ignored by the devstack Quarto build.
- Docs changed: `proposal_base_data_store.qmd`, `contributing_base_data.qmd` (rewritten), `base_data_release_notes.qmd`, `_conventions_reference.md` (dataset folders and `raw/`), `devstack_guidance.md` (ownership row for base_data), `code_standards.qmd` (link).
- `docs/_site/` is tracked in git: don't render into it when checking; render a copy in a scratch folder.

### base_data (`~/Files/base_data`, not a git repo)

- `pyramids/pyramids_base_data_ingestion.py` + manifest: 17 `ha_per_cell_<rung>sec.tif`, 10 s to 648000 s, extensive, CC-BY-4.0.
- `lulc/esa/lulc_esa_base_data_ingestion.py` + manifest: 31 `lulc_esa_<year>.tif`, 1992-2022, categorical, ESA CCI Land Cover licence, C3S v2.1.1 for 2016 onward (doi:10.24381/cds.006f2c9a).
- `lulc/esa/seals7/lulc_esa_seals7_base_data_ingestion.py` + `lulc_esa_seals7_base_data_scenarios.csv` (added 2026-10-20): the ProjectFlow run file above. Row `esa_seals7`: `lulc_src_label=esa`, `lulc_simplification_label=seals7`, `lulc_correspondence_path=seals/default_inputs/esa_seals7_correspondence.csv`, `base_years=1992 2000 2010 2015 2017 2022`. Task `lulc_simplified_rasters` reclassifies `lulc_esa_<year>.tif` with `hb.reclassify_raster_hb` (uint8, ESA 0 stays 0) then `hb.make_path_pog(variable_class="categorical")` to `lulc_esa_seals7_<year>.tif`, the same maps SEALS' `lulc_simplifications` task makes and searches base_data for; task `lulc_simplified_base_data_listing` calls `hb.add_directory_to_base_data` with `include=["lulc_esa_seals7_*.tif"]` and writes `lulc_esa_seals7_base_data_manifest.csv` in that folder. Licence and source are the ESA strings carried over, with the correspondence ref path appended. A second correspondence or year set is a second CSV row. The manifest exists only once the script has had a real run.
- `lulc/esa/seals7/convolutions/{2015,2023}/`: 28 `convolution_esa_seals7_<year>_<class>_gaussian_{1,5}.tif`, 78 GB, Float32 covariate POGs produced by some SEALS run, **not listed in any manifest and not published**. Their parents (per-class binaries) are not in base_data, and `lulc_esa_2023.tif` doesn't exist anywhere in the store. Binaries and convolutions are the next derived datasets to add, as their own manifest rows; the seals chain is `lulc_esa_<year>` -> `lulc_esa_seals7_<year>` -> `binaries/<year>/binary_esa_seals7_<year>_<class>.tif` (7 classes: urban, cropland, grassland, forest, othernat, water, other) -> convolutions, all in `seals/seals/seals/seals_generate_base_data.py`.

## Current state (2026-10-20)

- Releases: `2026.10.19.1` (17 pyramids, "Initial pyramid population.") and `2026.10.20.1` (adds 31 ESA maps; 48 datasets, about 10.6 GB).
- The website is live at https://data.teemlabs.org, with a Cloudflare URL Rewrite rule ("Folder index pages") on the `teemlabs.org` zone (Rules → Overview): expression `http.host eq "data.teemlabs.org" and ends_with(http.request.uri.path, "/")` → dynamic path `concat(http.request.uri.path, "index.html")`. Until 2026-10-21 it listed four fixed paths, so the nested `lulc/esa/seals7/` page returned 404 though its `index.html` object existed; any new folder page now needs nothing in Cloudflare.
- Credentials: `~/.config/hazelbean/machine.env` (`HB_R2_ACCOUNT_ID`, `HB_R2_ACCESS_KEY_ID`, `HB_R2_SECRET_ACCESS_KEY`). Never print or commit them.
- 2026-10-21: the user ran the seals7 ingestion and published release `2026.10.21.1` (54 datasets; its note is still "Adding ESA CCI", carried over). The pages rebuilt. Then (this session) page discoverability: docstring-derived card text and the landing-page folder tree (hazelbean + `_landing.html` + `_styles.css`, uncommitted); the pages must be rebuilt (`hb.write_base_data_index_pages(site_dir, dry_run=False)` or any real publish) to show it.
- 2026-10-20, later: the seals7 run file and `hb.resolve_dry_run` were added (see above) and `seals7/pog_dir_recursively.py`, a stray converter, deleted. Verified with a harness (`run_project` with `dry_run=True`: six years planned, nothing written) and a clipped-window reclassification that matched the rules cell for cell; the hazelbean unit file passed (38 tests). The user was about to run the real ingestion; check whether `lulc/esa/seals7/lulc_esa_seals7_<year>.tif` and the manifest now exist, and whether a release after `2026.10.20.1` includes them. The run file's `__main__` sets `p.dry_run = "2026-10-20"`, so it reverts to a dry run from 2026-10-21.
- `contributing_base_data.qmd` documents the run-file form and the date form of `DRY_RUN` (also uncommitted).
- 2026-10-22: `cartographic/ee` got its ingestion script (`cartographic_ee_base_data_ingestion.py`; the docstring is the
  record of the OpenStreetMap-derived geometry, the ODbL licence and the GADM crosswalk; the OSM build script is not
  available, and `ee_processing/` is an earlier, different construction) and a 6-row manifest: `ee_r264_ids.tif`,
  `eemarine_r566_ids.tif` (categorical POGs, 10 s) and the two correspondence geopackages with their CSVs (listed, but
  `unsupported` until the store publishes vectors and tables). Published in releases 2026.10.22.1 (under the old `_10sec`
  names) and 2026.10.22.2 (renamed); on 2026-10-23 the two `_10sec` objects, their catalogue entries and their rows in
  both release snapshots were deleted by hand (the store has no retire mechanism; a retiring design was built and
  reverted the same day as over-engineering while the site has no users) and the pages rebuilt. `ee_r250_ids.tif`
  (ee_r264 reclassified to ISO3 numeric codes by the script's `write_r250_zone_ids`) is listed by the script but not
  yet built or published. The standalone coarser id rasters were
  dropped (the POG overviews are the coarser rungs; regenerate_pyramids.py no longer writes zone ids) and the `_10sec`
  suffix was removed from single-POG names: a rung suffix only where separate files exist at several rungs
  (`_conventions_reference.md`, "Pyramid resolutions are expressed in arcseconds"). The user deletes the old coarse
  files and the displaced copy themself. `gadm/` is unlisted and GADM-licensed.
- Pending for the user: create `NatCapTEEMs/Files/base_data_submissions/` on Drive and move the old `base_data/submissions/` contents there; upload the pages once more to pick up the latest footer links; commit both repos.

## Not built yet (see the proposal's implementation order)

- C1: read-only status tool (local hashes vs Drive md5s vs catalogue). Proposed, deferred.
- D: `get_path` R2 tier (release fetch, hash-checked download, lock files, temporary Google Cloud fallback with a warning).
- E: `rung=` / `subset=` window reads into `base_data_cache/`, size guard; tileset, class_stack and zone_set datasets.
- F: Drive mirror, `get_path` resolving `base_data_submissions/…` refs and redirecting promoted ones, `hb.promote_base_data_submission`. Until then contributors use `prepend_possible_dirs=[~/Files]`.
- G: private tier.
- Publishing a metadata-only change (bytes unchanged → stays `unchanged`, catalogue keeps old metadata).
- Recording a derived dataset's parent in the catalogue's `depends_on` (the gate derives it only from a POG's denominator). Proposed as an optional `depends_on` manifest column; deferred.
- seals7 binaries and convolutions as manifest rows (see the base_data section); a `_collections.yml` entry for `lulc/esa/seals7` once it publishes.
- Automatic release notes.

## Working rules for this user (Justin Johnson, jajohns)

- **Environment:** `conda activate env1` for everything; ignore env names hardcoded in repo files.
- **Write only inside the folders loaded in the workspace**; never edit archived paths (`old`, `archive`, `deprecated`, `bak`, `legacy`...) or `external_repos/`. hazelbean owns general utilities; base_data holds only thin ingestion scripts and manifests.
- **The user runs real publishes and real ingestions.** Use `dry_run=True` when testing, and call functions directly with `dry_run=True` rather than running a user's script. **Re-read any file the user may have edited before running it** (an ingestion script was once run for real because its `DRY_RUN` had been flipped to `False`).
- **Don't commit unless asked.** End commit messages with the attribution lines the harness specifies.
- **Simplicity:** the user pushes back on over-engineered code. Reuse hazelbean functions (search first), avoid single-use abstractions, keep private helpers few, and build only what was asked; optional ideas are listed, not built.
- **Ask before deciding things that are the user's**: names, where things live, licensing text. Present options with a recommendation.
- Threads, not processes, for parallelism (macOS spawn would re-run flat scripts).
- POGs declare the per-type nodata value but no cell holds it; exact statistics are stored in metadata.
- **To test a run file, don't run it**: import `run_project` from the file, construct the ProjectFlow in a scratch `project_dir`, set `p.scenario_definitions_filename` and `p.dry_run = True`, and call `run_project(p)`. (The seals7 file locates its CSV from its own `__file__`, so the harness being the calling script doesn't matter.)
