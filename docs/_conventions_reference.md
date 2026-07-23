## Slashes vs backslashes

On Windows, at the most bare-metal level, paths separate levels with a backslash
`\`. However, nearly everything else within Windows correctly interprets a
forward slash `/` at the OS level. We can't control how *other* programs report
backslashes, but for anything we type into our repos we follow one rule:
**always use forward slash**, no matter the platform. Linux/mac always use
forward slash, so this works everywhere. ($5 bounty for a case inside our
devstack that genuinely needs an exception.)

## Identifiers and labels

These terms form a ladder from most-compact machine key to most-verbose human
text. Use them consistently.

- **`id`** — the unique identifier of an object. In the devstack, an integer
  **≥ 1**, where **0 denotes NDV** (no-data value). This enables fast
  computation with e.g. id-rasters and `reclassify_raster`. In a many-to-one
  correspondence it is sorted by the "one" side, alphabetically at generation
  time (not guaranteed to stay sorted downstream). **`id` is the stable key we
  persist** in data, files, and correspondences.

- **`index`** — the *position* of an element in a sequence (list, string, or the
  row position in a spreadsheet). It is **transient and not stable**: never
  persist it, and never use it as the identifier column in a DataFrame or file,
  because the position can change. Use `id` for anything durable. Generally avoid index.

- **`labelheader`** — an exactly-4-character, lowercase-alphanumeric string (no
  special symbols). Useful for the Header label in `.har` files. Technically
  case-insensitive; we assume lowercase.

- **`labelshort`** — an ≤8-character, lowercase-alphanumeric string (no special
  symbols). Useful for `.har` files, which cap label length at 8.

- **`label`** — a lowercase-alphanumeric string whose only allowed special
  symbol is the hyphen. Keep it short (≤8 characters is ideal for HAR
  compatibility). Avoid capitalization.

- **`name`** — a short human-readable string of any ASCII characters, with
  Python-style escaping of special characters. Short enough to serve as a column
  header or plot label, and has a 1:1 correspondence to a `label` (usually
  defined via a correspondence dictionary).

- **`description`** — a `name` of any length, with a detailed description,
  possibly formatted Markdown.

If a domain applies (see below), prepend it to the term, e.g. `gadm_id`.

### `id`/`index` in vector data

GeoPandas indexes vector data with an FID — the order geometries were added,
which gets wonky with legacy formats (e.g. ESRI Shapefiles). Also, writing a
GPKG to CSV drops the FID, so you can lose data. **EE spec therefore requires**
that any GPKG saved as CSV gets a new `id` column added as the first column,
generated starting at 1 and incrementing by 1 *after sorting on the simplest
non-FID label* (e.g. `iso3_label`). See `gtap_invest_generate_base_data.py`.

## Labels files

Based on the GTAP database structure, EE spec defines file types that
systematize how dimensions/sets are defined (and then used in e.g. plotting). A
single dimension is first defined by a **labels file**, which has at least three
columns — `domain_id`, `domain_label`, `domain_name` — and optionally a
`domain_description`. Every column present must be fully filled (no missing
values). Labels files are used elsewhere to go from id → name (e.g. labeling a
plot axis) and to build the correspondence files below.

## Correspondences

Model linkages often require mapping a many-to-one relationship consistently.
Correspondence files define this via a src-to-dst (source → destination)
mapping, named by a specific pattern. Using
`gadm_r263_gtapv7_r251_r160_r50_correspondence` as the example:

- `gadm` is the domain label,
- `r263` is a src dimension-size pair (`r` = region, `263` = number of unique
  entries),
- to be a correspondence there must be at least one dst dimension-size pair;
  here there are three (`r251`, `r160`, `r50`),
- each pair is identified with the domain named most closely before it (the
  later three are `gtapv7`),
- dst pairs are sorted by **decreasing size**,
- the pairs are followed by the word `correspondence`.

This maps GADM 263 regions → GTAPv7 251 → 160 → 50 regions.

A 2-domain correspondence table looks like this (replace `src`/`dst` with the
specific domain names):

| src_id | dst_id | src_label | dst_label | src_description | dst_description |
|--------|--------|-----------|-----------|-----------------|-----------------|
| 1 | 1 | aus | oceania | Australia | Oceania (including NZ and AUS) |
| 2 | 1 | nzl | oceania | New Zealand | Oceania (including NZ and AUS) |

If defined exactly right, 2-dimensional correspondence files work with Hazelbean
via `seals_utils.set_derived_attributes(p)` and:

``` python
p.lulc_correspondence_dict = hb.utils.get_reclassification_dict_from_df(
    p.lulc_correspondence_path, 'src_id', 'dst_id', 'src_label', 'dst_label')
```

That returns a dictionary useful for many reclassification tasks, including keys
such as `src_to_dst_reclassification_dict` (map to a specific dst value),
`dst_to_src_reclassification_dict` (one dst → the list of srcs that aggregate
into it), the corresponding label dicts, and the unique id/label sets. It can be
used to reclassify LULC geotiffs via:

``` python
rules = p.lulc_correspondence_dict['src_to_dst_reclassification_dict']
hb.reclassify_raster_hb(raster_path, rules, output_path)
```

### Combined ids

One special case is when two ids are combined into a single column by leveraging
decimal position to compress data. For example, a Region-AEZ id can be stored as
a 5-digit integer where the first three digits are `ee_r264` and the final two
are `aez18`. Note that a combined `_id` column intentionally violates the
single-id rule above (it encodes two identifiers).

### Correspondences with geometries

Because only one geometry can be assigned per file — and membership of
aggregated regions can get confusing — each correspondence file keeps all its
labels but is *also* saved alongside a geometry file that drops the other labels
(and drops the word `correspondence` from the filename):

``` python
p.ee_r264_correspondence_vector_path = p.get_path(
    os.path.join('gtap_invest', 'region_boundaries', 'ee_r264_correspondence.gpkg'))
p.ee_r264_vector_path = p.get_path(
    os.path.join('gtap_invest', 'region_boundaries', 'ee_r264.gpkg'))
```

## Project-level variable names

Project-level variable names are carefully structured. In
`gtapv7_r251_r160_correspondence_input_path`:

- `input` immediately before `path` means it is a **raw asset** obtained from an
  external source and not yet processed — so it may be a non-compliant XLSX.
- `path` means it is a string that points to a location on a storage device
  (as opposed to the loaded object itself — see src/dst vs input/output below).
- `gtapv7` is the domain of every dimension that follows until another domain
  label appears — here, 251 regions mapped to 160 regions within the `gtapv7`
  domain.

A single correspondence file can hold multiple mappings, e.g.
`gtapv7_r251_s65_r50_s26_correspondence_input_path` maps r251→r50 and sectors
s65→s26, all in the `gtapv7` domain.

Note: a **file path** may be plural (it contains many of the thing), but a
**column label** should almost never be plural — e.g. the file is
`..._regions_...` while the CSV column is `region`.

``` python
p.gtap11_region_correspondence_input_path = os.path.join(p.base_data_dir, 'gtappy', 'aggregation_mappings', 'GTAP-ctry2reg.xlsx')
p.gtap11_region_names_path = os.path.join(p.base_data_dir, 'gtappy', 'aggregation_mappings', 'gtap11_region_names.csv')
p.gtap11_gtapaez11_region_correspondence_path = os.path.join(p.base_data_dir, 'gtappy', 'aggregation_mappings', 'gtap11_gtapaez11_region_correspondence.csv')
```

### src/dst vs input/output

- **src/dst** is a pointer/reference to a thing; **input/output** is the thing
  itself. This is especially useful for paths: you often see
  `input_array = hb.as_array(src_path)`.
- `_path` and `_dir` imply the string is a reference, so `src_path` and
  `src_dir` are common.

## Scenario naming

Scenarios are defined in a nested structure. Each level is a `label`:

1. **Exogenous assumptions** (no hyphens) — e.g. which SSP, GDP, population.
   Typically fully defined by the SSP.
2. **Climate assumption** (no hyphens) — which RCP.
3. **Model** (**may** have hyphens — the only level allowed to, because hyphens
   are used for multi-step scenario processing) — e.g. `magpie`, `luh2-message`.
4. **Counterfactual** — policy assumption/definition, including `bau` (a special
   counterfactual others are compared against). Different counterfactuals
   correspond to different shockfiles or LUC projection priorities.
   - A counterfactual may have processing steps, appended as a hyphen + exactly
     4 characters. For example, a run that **excludes** ecosystem services uses
     the `-noes` suffix; the run that **includes** ES appends nothing (it is the
     default that gets referenced).
5. **Year** — see the year typing rules below.

The labels map to a directory hierarchy, with the final level folded into the
filename rather than becoming its own directory:

```
ssp2/rcp45/luh2-message/bau/filename_2050.tif
```

### Filename conventions

Two conventions are supported. In both, the variable name (e.g. `lulc`) stays at
the **front** of the filename.

- **Implied** — the directory structure supplies all labels except year (which
  is appended to the filename):

  ```
  project/intermediate/convert_netcdf/ssp2/rcp45/luh2-message/bau/lulc_2050.tif
  ```

- **Explicit** — every label is repeated in the filename even though the
  directory implies it:

  ```
  project/intermediate/convert_netcdf/ssp2/rcp45/luh2-message/bau/lulc_ssp2_rcp45_bau_luh2-message_2050.tif
  ```

  The same file with **no ES considered** carries the `-noes` suffix on the
  counterfactual:

  ```
  project/intermediate/convert_netcdf/ssp2/rcp45/luh2-message/bau-noes/lulc_ssp2_rcp45_bau-noes_luh2-message_2050.tif
  ```

### Nested variable names

A variable name may itself have nested layers, distinct from the scenario
nesting. For example:

```
base_data/lulc/esa/seals7/binaries/2014/lulc_esa_seals7_binary_2014_cropland.tif
```

Here `lulc` is the variable label; `esa` denotes origin, `seals7` denotes
recategorization, `binaries` denotes binary (is-class vs is-not-class)
processing, and year comes last. Keep sub-nest ordering consistent (it usually
depends on what you iterate over).

Because labels contain no spaces or underscores, the nested structure can
collapse to a single string, e.g. `filename_ssp2_rcp45_policyname_year.tif`.

### Year typing

- When a variable is **singular** it must be an `int`; when **plural** it is a
  list of ints. `base_years` is always a list even with a single entry (the name
  is plural). Always use `base_years`, **never** `baseline_years` (to avoid
  confusion between "baseline" and "bau").
- When stored in a DataFrame, type-check on read:
  - Singular: `str(value)`, `int(value)`, or `float(value)` as appropriate.
  - Plural: the cell is a space-delimited string — `[int(i) for i in value.split(' ')]`
    on read, `' '.join(values)` on write. (Being updated to the JSON-style
    parsing used in `scenarios.csv` files.)

### Scenario types

Three `scenario_type`s are supported: `baseline`, `bau`, and `policy`.

- **baseline** — the year has observed (not modelled) data; these years are in
  `p.years` and identically in `p.base_years`. (Exception: when e.g. GTAP updates
  the base year from 2017 to 2023, policies are then applied on 2023.)
- **bau** and **policy** — results are modelled; their years are in `p.years`
  but *not* in `p.base_years`.

### Supported filetypes

- NetCDF with the dimensions above, in the same order.
- A set of geotiffs embedded in directories — each label gets a directory level
  except year, which is **always** the last 4 characters of the filename before
  the extension (preceded by an underscore).
- A spreadsheet linkable to a geographic representation (shapefile or geopackage)
  in vertical format.

## get_path and ref_path

Paths that are ready to use end in `_path` (last 5 characters). Before
`get_path` is called, the root directory is not yet resolved; a **reference
path** ends in `ref_path` (last 8 characters) and is relative to one of several
possible root directories. `get_path` searches those roots in order and returns
the most useful hit:

1. `cur_dir` — the current task's directory (so a task can skip itself if its
   output already exists),
2. `input_dir` — project-specific inputs,
3. `base_data_dir` — cross-project data (also the default download location),
4. the cloud storage location.

``` python
p.ha_per_cell_10sec_ref_path = os.path.join('pyramids', 'ha_per_cell_10sec.tif')
```

Choosing a relative path that matches the desired location *relative to
base_data_dir* lets a task generate a file into its `cur_dir` and later have the
exact same relative path found in `base_data_dir` — this is how base-data-
generating tasks work. Outside a task (e.g. in the run file before the task tree
is built) the default roots don't apply, so pass them explicitly:

``` python
p.countries_iso3_path = p.get_path(
    os.path.join('cartographic', 'gadm', 'gadm_adm0_10sec.gpkg'),
    possible_dirs=[p.input_dir, p.base_data_dir])
```

## Function and method naming

**Factory / creation**
- **make** — factory functions/methods that create new *instances*
  (`make_dataset`, `make_grid`).
- **create** — generate new objects/files from scratch (`create_empty_raster`,
  `create_new_project`).

**File operations**
- **open** — open file handles/connections; load metadata, not full data
  (`gdal.Open`).
- **load** — read entire data into memory (`load_dataset`).
- **read** — get data into memory from a path or file-like object, often
  chunk-based (`read_csv`).
- **write** — output data to disk/stream, often incremental (`write_results`).
- **save** — persist a complete object/state to disk, typically all at once
  (`save_model`).

**Data manipulation**
- **extract** — pull specific portions from a larger structure
  (`extract_features`).
- **execute** — run commands/scripts/processes (`execute_query`).
- **convert** — transform between formats/types (`convert_crs`).

**Collections**
- **list** — return a collection, typically a Python list (`list_files`).
- **remove** — delete from an in-memory collection/structure
  (`remove_duplicates`).
- **delete** — permanently remove from disk/database (`delete_file`).
- **displace** — (in-house) rename a path with e.g. a timestamp so you can write
  a new file into the old place without destroying the original; has optional
  `delete_on_exit`.
- **rename** — change name, same location (`rename_column`).
- **replace** — substitute one value/object for another
  (`replace_missing_values`).
- **move** — relocate to a different location/container (`move_to_archive`).

## Directory and file naming

- **dir** — avoid as a standalone noun (directory or direction?); **use
  `directory`**. It *can* be a suffix (`temp_dir`), and is fine inside function
  names for brevity (`delete_dir()`, `create_dir()`), matching Unix heritage.
- **directory** — preferred over `dir` for clarity (`output_directory`).
- **folder** — avoid except in user-facing docs.
- **dirname** — preferred; matches stdlib. Name of a directory without its path.
- **dir_name** — avoid.
- **dir_path** — the full directory path.
- **directory_name** — avoid (too long).
- **path** — full path to a file/directory (`input_path`, `config_path`).
- **file_name** — full filename with extension (`data.csv`). Preferred over
  `filename`.
- **filename** — avoid (use `file_name`), though it is broadly used elsewhere.
- **file_root** — filename without extension (`data` from `data.csv`).
- **fileroot** — avoid (use `file_root`), though broadly used elsewhere.
- **file_extension** — suffix including the dot (`.csv`).
- **parent_directory** — one level up (`os.path.dirname(path)`).
- **grandparent_path** — two levels up; consider `pathlib` for clarity.

## Variable naming

**Counting and size**
- **n_cols** — shorthand for counts in scientific computing (`n_samples`).
- **num_cols** — more explicit; good for public APIs (`num_iterations`).
- **number_cols** — too verbose; prefer `n_` or `num_`.
- **shape** — dimensions tuple for arrays (`array.shape`).
- **size** — total number of elements or bytes (`array.size`).

**Data types**
- **data_type** — preferred, for consistency with numpy/pandas.
- **dtype** — avoid except where a library uses it explicitly (numpy).
- **datatype** — avoid except where a library uses it explicitly.

**Geospatial**
- **cell_size** — spatial resolution of a single raster cell.
- **res** — common abbreviation for resolution.
- **resolution** — full word preferred in public APIs/docs.
- **x_res / y_res** — horizontal / vertical resolution in map units.
- **raster_info / vector_info** — metadata object for gridded / feature data.

**Bounding boxes**
- **bb** — common abbreviation for bounding box.
- **bounding_box** — preferred for clarity.
- **bb_exact** — pyramids-specific: the bb aligns with a pyramidal ID raster
  (preferably named, like `bb_exact_30sec`).
- **bounding_box_min_max_notation** — `[xmin, ymin, xmax, ymax]`.
- **bounding_box_xy_notation** — `[xmin, xmax, ymin, ymax]`.
- **cr_widthheight** — `[col, row, width, height]`, optimized for GDAL.

**Coordinates**
- **lat** — latitude. **lon** — longitude (always `lon`, never `long`, which
  conflicts with a Python built-in).
- **lat_size / lon_size** — height / width in degrees or number of values.

**Identifiers and indexing** (see the full ladder above)
- **index** — position in a sequence or DB index; never use for an id column in
  a DataFrame (position can change).
- **id** — the unique identifier (integer ≥ 1, 0 = NDV); prefer domain-specific
  names like `feature_id`.
- **counter** — loop/accumulation counter (`iteration_counter`). With many
  counters, prefer `c_row, row in enumerate(rows)` to avoid confusion.

**Data processing**
- **valid** — boolean/mask for valid data; prefer `invalid` over `not_valid`.
- **mask** — boolean array for filtering (True where the condition holds).
- **ndv** — preferred over `nodata`, `no_data`, `no_data_value`, etc.
- **nonzero** — elements/indices where value != 0.

**Standard abbreviations**
- **array** — generic numpy array. **df** — pandas DataFrame (with many, use a
  `df_` prefix). **gdf** — GeoPandas GeoDataFrame.
- Import aliases: **np** (numpy), **pd** (pandas), **gpd** (geopandas).

**Special**
- **default** — default parameter values (`default_crs`).
- **paths_to_delete_at_exit** — cleanup list for temp files (preferred).
  `uris_to_delete_at_exit` is outdated — use `paths_...`.
- **plots_to_display_at_exit** — deferred plotting for batch processing.
- **info** — generic metadata container (`dataset_info`).
- **describe / desc** — statistical summary / description in metadata.
- **run_dir** — directory for the current execution's outputs.
- Postpend a type when helpful: `temps_array` vs `temps_list`.

**Naming to avoid**
- **globals** — avoid global variables; if unavoidable, use `UPPER_CASE`.
- **temp** — never use (temporary or temperature?). Use `temporary` or
  `temperature`.
- **old_** — prefix for previous versions during refactoring (`old_algorithm`).

## Priority and debug markers

- **todo / todoo / todooo** — increasing O's mean *lower* priority (standard,
  lower, lowest). (The priority ordering is deliberately opposite to most
  coders' convention, so it's stated explicitly.)
- **print()** with no space before the paren likely marks debug code to remove;
  **print ()** with a space marks intentional output to keep.

## File-type-specific

- **shapefile** — use only to specify an ESRI Shapefile explicitly (vs. e.g. a
  geopackage).
- **tiff** — never use except in the GDAL driver name `GTiff`.

## Python style

We follow PEP 8 with a few departures:

- **Line length** — more than 80 characters is allowed; keep lines within
  **160** characters (except comments trailing a code line).
- **Blank lines** — use a **single** blank line between functions, not two, so
  more functions are visible when folded.
- **Case** — `snake_case` for variables and functions, `CamelCase` for classes.
- **Quotes** — outer strings use **double quotes**; inner strings (e.g. dict-key
  string values inside an f-string) use single quotes. Preferring double quotes
  on the outside avoids escaping apostrophes.
- Avoid global variables; keep functions concise and focused on a single task.

## Docstrings

Use **Google-style docstrings** (they render well with Quarto):

``` python
def fibonacci(n):
    """Generate the nth Fibonacci number.

    Args:
        n (int): The position in the Fibonacci sequence.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        NameError: If n is not an int.

    Examples:
        Basic usage:
        ```python
        fibonacci(5)  # Returns 5
        fibonacci(10) # Returns 55
        ```
    """
```

## UTF-8 encoding

International datasets frequently hit Byte Order Mark (BOM) / encoding
mismatches — e.g. a first column read as `Ã¯Â»Â¿fao_country_id`, or "Åland"
mangled to "Ã…land". Excel assumes Windows-1252 for UTF-8 files that lack a BOM,
splitting each multi-byte character into garbled pieces.

- **Read** CSVs with `pd.read_csv('file.csv', encoding='utf-8-sig')`.
- **Write** CSVs with `df.to_csv('output.csv', encoding='utf-8-sig', index=False)`.
- The `-sig` adds the 3-byte BOM that tells Excel the file is UTF-8. For most
  data-analysis work, prefer `utf-8-sig` everywhere; use plain `utf-8` only when
  the consuming tool expects it (some Unix CLI tools).
- To strip a stray BOM from already-loaded columns:
  `df.columns = df.columns.str.replace('﻿', '')`.

## ProjectFlow conventions

- A ProjectFlow project's root is the directory holding its `run_<project>.py`
  entry file (ProjectFlow auto-detects this as `script_dir`; `input_template/`
  lives beside the run file). There is no separate markerfile.
- **`run_<project>.py` is the single entry point and defines `run_project()`
  itself.** The canonical shape: a module-level `build_task_tree(p)` — named
  exactly that in every run file — that constructs the project's task tree
  (always build the FULL tree — variants disable, they don't omit), then
  `run_project(scenario_definitions_filename=..., project_name=...,
  append_timestamp=False, tasks_to_skip=None, execute=True)` doing all
  ProjectFlow setup, calling `build_task_tree(p)` then
  `p.skip_tasks(tasks_to_skip)`, and ending in `p.execute()` (behind `execute`)
  and `return p`, then an `if __name__ == '__main__':` guard calling
  `run_project()`. The guard is mandatory — run files must never execute on
  import. Skipping is run configuration, so it lives in `run_project`, not in the
  builder; `p.skip_tasks()` (hazelbean) sets `run=0` by task name and warns on
  unknown names. Variant runs (fast, postprocess-only, backend tests) are thin
  wrappers that import `run_project` and pass `tasks_to_skip=[...]` and/or a
  different scenarios CSV — never duplicated files. Timestamped project dirs are
  opt-in via `append_timestamp`, never a commented-out line. Reference
  implementation: `gtap_invest/projects/ngfs/ngfs_pnas/ngfs_pnas/run_ngfs_pnas.py`.
- **Machine-specific configuration lives in `parameters.csv`, never in code and
  never in environment variables.** Connection settings (`vm_ssh_host`,
  `vm_disk_prefix`, `gempack_dir`, `sc_ssh_host`, `sc_scratch`), credentials
  paths, and any other per-machine values are keys in the project's
  `<project>_parameters.csv`. The tracked `input_template/` copy ships these keys
  with **blank** values; each machine fills in its own untracked `input/` copy.
- **Tasks are named as nouns** (this intentionally breaks PEP 8), referencing
  what is stored in the task's output directory, so the resulting file structure
  reads well to an outsider.
- A task is a function that takes `p` and returns `p`. Define project-level paths
  and attributes *before* the `if p.run_this:` block (these are the shared
  "project-level variables" other tasks may use); put all computationally
  intensive work *inside* `if p.run_this:`.
- Every computationally intensive step must be guarded by an existence check
  (usually `if not hb.path_exists(output_path):`) so completed work is skipped
  on re-run.
- **`input_template/` is tracked; `input/` is derived.** Definition files a run
  reads — scenarios CSV, parameters CSV, outputs CSV, figure/section definitions,
  and any other seed inputs — live in the repo's `input_template/` directory and
  **are committed to source control**. On first run, ProjectFlow copies each item
  that doesn't already exist in the project's `input/` directory (which lives under
  the timestamped/project run dir and is **outside source control**). So: edit the
  copy in `input_template/`; treat `input/` as a generated working copy. A run only
  copies files that are missing in `input/`, so a stale `input/` file will shadow an
  updated template — delete it (or use a fresh project dir) to pick up template edits.
- **scenarios.csv is authoritative for every attribute it has a column for.**
  Scenario iteration re-hydrates `p` from the CSV row at each scenario, so a
  run-file assignment like `p.aoi = 'RWA'` made after scenario initialization
  wins only until the first scenario iterates, then is silently overwritten.
  Run files may set scenario-varying attributes only inside the
  generate-defaults branch
  (`if not hb.path_exists(p.scenario_definitions_path):`), where they seed the
  CSV about to be written — on later runs that branch is dead code and the CSV
  rules. To run with a different AOI (or any other scenario-varying value),
  pass a different scenarios CSV via
  `run_project(scenario_definitions_filename=...)` — that is exactly what the
  pared `_test.csv` pattern is.
- **Every run file defines `build_task_tree(p)` — even when it only delegates.**
  `build_task_tree` is the one named place that answers "what is this project's
  pipeline?", so all run files share identical anatomy (imports,
  `build_task_tree`, `run_project`, `__main__` guard). Three forms, one name:
  a one-line shim delegating to a shared library builder (e.g.
  `seals_initialize_project.build_standard_task_tree(p)`); a composition of
  one or more library builders plus project-specific tasks; or a fully local
  tree built from library *task functions*. Two guardrails: (1)
  `build_task_tree` contains only tree construction — library-builder calls,
  `p.add_task`/`p.add_iterator`, and tree-structure decisions; no `p`
  configuration, CSV logic, or dir setup (that's `run_project`'s job). (2)
  `run_project` never calls a library builder directly — all tree construction
  flows through the local `build_task_tree`, with `p.skip_tasks(tasks_to_skip)`
  immediately after the call (skipping is run configuration, however the tree
  was assembled).
- **Library repos export task functions plus only truly generic builders.**
  A pipeline shared by many entry points (e.g. seals'
  `build_standard_task_tree`) lives in the library's `*_initialize_project`
  module so fixes propagate to every run file whose shim delegates to it. A
  research project's tree lives in the project's own `run_<project>.py` —
  the project must be free to evolve its tree without touching the shared
  library, at the accepted cost of some structural duplication between
  projects. Do not accumulate single-project builders in library
  `*_initialize_project` modules; when a project graduates to its own repo,
  its builder moves with it (renamed to the local `build_task_tree`). A
  variant run never justifies a new builder — use `tasks_to_skip` or a `mode`
  kwarg on `run_project`.
- **A test run differs from the full run only by its scenarios CSV.** Keep a pared
  `<project>_scenarios_test.csv` in `input_template/` (fewer scenarios, a single
  future year, a single AOI region) and a thin `run_<project>_test.py` (≤ ~25
  lines) that imports `run_project` from `run_<project>.py` and calls it with that
  filename, a stable `<project>_test` project name, and `append_timestamp=False`
  so repeated test runs resume in place. Don't fork the task tree for tests.
  Test files use the `_test` **suffix** (`run_<project>_test.py`,
  `run_<project>_<variant>_test.py`), never a `run_test_*` prefix.

## Git workflow

We use **Git Flow** (a `main` branch plus a `develop` branch):

- `main` holds working releases only.
- `develop` is the integration branch. Branch features off `develop` as
  `feature_<name>` (or `develop_<yourname>`).
- Open pull requests **into `develop`**, not `main`. `develop` is protected —
  only work that passes unit tests is merged. Releases are promoted from
  `develop` to `main` via pull request.
- External contributors fork, branch, and PR from their fork into the upstream
  `develop`.

See the full walkthrough on the *Contributing* page.
