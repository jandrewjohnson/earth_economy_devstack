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

**Failure semantics are skip-aware.** When a ref_path resolves nowhere,
`get_path` raises a `NameError` listing the ref_path as given and every root
searched — but only in a *consume* context: a running task (`p.run_this`
truthy) or run-file-level code. In a **skipped** task (`p.run_this == 0`),
pre-`run_this` code executes purely to publish paths for later tasks, so
`get_path` never raises there: it forms the would-be path under the first
searched root, logs the assumption, and lets any real failure surface in the
next task that actually consumes the file. This makes `p.get_path()` safe to
use in the project-level-variables zone above `if p.run_this:`; a task that is
about to *generate* a file should still pass `raise_error_if_fail=False` (or
guard with `hb.path_exists`).

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

- **Name a directory for its *kind* of content, in the singular.** `input/`,
  `output/`, `intermediate/`, `input_template/` — never `inputs/`, `outputs/`,
  or `input_templates/`. The directory holds one *kind* of thing, and the
  plural adds nothing: `output/` already contains many outputs, exactly as
  `input/` contains many inputs. This matches the Python ecosystem's dominant
  convention and keeps the directory name identical to the stem of the
  attribute that points at it, so `p.output_dir` → `output/` with no
  translation step. Reserve the plural for a directory holding many
  *heterogeneous* items that share no single kind.
- **Corollary: the `*_dir` attribute and its directory must agree.** A
  singular attribute pointing at a plural directory (`p.output_dir` →
  `outputs/`) is the failure mode this rule exists to prevent; it was the
  actual state of `ProjectFlow` until 2026-07-31, alongside a vestigial
  `p.inputs_dir` → `inputs/` that nothing read. Both are now singular.
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

- **A run file's complexity is three independent axes, and only one is
  numbered.** *Configuration* — how a run varies — has levels 1–4: one task with
  inline constants; a task tree; + a scenarios CSV; + a parameters CSV.
  *Code layout* — where the code lives — runs single file → split
  (`<project>_tasks.py`; `<project>_functions.py` for science helpers;
  `<project>_utils.py` for science-unaware helpers, which is a promotion queue
  into hazelbean rather than a filing category; `<project>_initialize_project.py`
  for tree builders) → library package. *Ownership* — who owns the code you run —
  runs self-contained → devstack developer → downstream user, where the library
  is a read-only dependency in your own repo. The axes are independent: moving
  along one never requires moving along another, so **"level" unqualified always
  means the configuration axis**. Copy-me templates are described on the [Run Templates](run_templates.qmd)
  page; the same code with the reasoning written out is in
  `examples/run_templates_annotated/`. The six numbered stages in
  project_complexity.qmd are a historical narrative, not these levels.
- A ProjectFlow project's root is the directory holding its `run_<project>.py`
  entry file (ProjectFlow auto-detects this as `script_dir`; `input_template/`
  lives beside the run file). There is no separate markerfile.
- **Bare `hb.ProjectFlow()` is git-aware and never writes inside a repo.** With
  no `project_dir` argument, the default is the script's parent dir — unless the
  script lives inside a git repo, in which case ProjectFlow walks up to the repo
  root, steps one level above it, and uses `<repo_parent>/projects/<name>`
  (`<name>` = the run file's stem minus any `run_` prefix), logging the choice.
  For a repo in the standard devstack layout (`~/Files/<stack>/<repo>`) this
  reproduces the house convention (`~/Files/<stack>/projects/<name>`) without
  the run file spelling it out. An explicit `project_dir` or `project_name`
  always overrides. Construction only *resolves* the paths — the dirs are created
  (and `input_template/` seeded) on the first call that needs them, so a bare
  constructor that is later re-pointed leaves no orphan project dir behind.
- **`run_<project>.py` is the single entry point, and `run_project` takes only
  `p`.** The canonical shape is four parts:
  - a module-level `build_task_tree(p)` — named exactly that in every run file —
    containing nothing but `add_task` calls. Always build the FULL tree; variants
    disable tasks, they never omit them, so the tree's structure (parents, dirs,
    iterators) is identical across every variant of a project.
  - `run_project(p)`, which reads its configuration off the `p` the caller
    handed it, calls `build_task_tree(p)` then `p.skip_tasks(p.tasks_to_skip)`,
    ends in `p.execute()` (unconditional — there is no `execute` flag; calling
    `run_project` means running the project) and `return p`. The ProjectFlow
    constructor initializes `tasks_to_skip` to `None`, so a run that sets nothing
    skips nothing and no guard is needed.
  - an `if __name__ == '__main__':` guard that **builds and configures the
    ProjectFlow** — `p = hb.ProjectFlow(project_name=..., run_mode=...)`, then the
    attributes this run varies — and calls `run_project(p)`. The guard is
    mandatory: run files must never execute on import.
  - the definition CSVs the run reads, in `input_template/` beside the run file.
- **The rule that decides what goes where: `run_project(p)` sets what no variant
  ever changes; the caller sets what a variant might.** When a project constant
  starts varying, it moves one line up — out of `run_project`, into the caller.
  There is no signature to edit, no keyword to add, and no default that can drift
  out of sync with the thing it duplicates. This is why `run_project` takes no
  keyword arguments: a signature full of defaults restates what is already known
  (`project_name` restates the file's own name, `run_mode` restates ProjectFlow's
  default), it grows once per class of CSV forever, and its values are invisible
  to everything except Python. Attributes on `p` can be listed, logged, and
  diffed between variants. The cost, stated plainly: bare `run_project()` no
  longer works, and a variant wrapper is four lines instead of three — in
  exchange, every knob a run uses is visible at the call site, and omitting one
  raises a named `AttributeError` instead of silently using another run's default.
- **Directory setup is the single constructor call
  `hb.ProjectFlow(project_name=..., run_mode=...)`, made by the caller.** It
  validates `run_mode` and infers the project dir git-aware from the run file's
  repo: `<stack>/projects/<project_name>` for a run file in a library repo, and
  the repo's wrapper-parent for a project repo nested under a `projects/` tree
  (so outputs land beside the checkout, never inside it). Pass `extra_dirs`
  explicitly only for placements the inference cannot know: grouping subfolders
  (`projects/ntsp/...`), another stack's tree (the devstack examples), or scripts
  outside any git repo. Because the caller owns this call, a notebook or harness
  can pass `extra_dirs` (or a fully custom `project_dir`) without the run file
  needing a pass-through argument for it.
- **Variant runs are their own file and share the pipeline by import — never by
  copy.** A variant (fast, postprocess-only, smoke test, backend test) imports
  `run_project`, constructs its own ProjectFlow with a distinct `project_name`,
  sets only what differs — a different scenarios CSV, `p.tasks_to_skip = [...]` —
  and calls `run_project(p)`. It sits at the same position on all three
  complexity axes as the run it varies; if a variant has to move along an axis,
  it is not a variant. `p.skip_tasks()` (hazelbean) sets `run=0` by task name and
  warns on unknown names; skipping is run configuration, so the *choice* belongs
  to the caller and the *application* belongs in `run_project`, never in the
  builder.
- **`run_mode` selects how much prior work is reused** (since 2026-07-24,
  replacing the old `append_timestamp` boolean): `'check'` (default) reuses the
  stable project dir with standard skip-existing logic; `'fresh_intermediate'`
  deletes the stable dir's `intermediate/` and `output/` in place so everything
  recomputes while `input/` (machine config) is kept — refused unless the
  resolved project name contains `'test'`; `'full'` mints a timestamped fresh
  project dir, also exercising `input_template/` seeding. `run_mode` is about
  reuse policy, not location, so it composes with an explicit `project_dir` as
  well as with `project_name`.
- **Canonical examples of the shape** (see [Run Templates](run_templates.qmd)):
  `run_template_3_canonical.py` (a scenarios CSV),
  `run_template_4_data_driven.py` (+ a parameters CSV), and
  `run_template_seals_example.py` (the same anatomy against a real library task
  tree). `examples/run_templates_annotated/` holds the same code with the
  reasoning written out, including the variant wrapper as a real file.
  `gtap_invest/projects/ngfs/ngfs_pnas/ngfs_pnas/run_ngfs_pnas.py` is the
  largest real pipeline on this anatomy, and shows it holding at a scale where
  the task tree runs to hundreds of lines.
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
- **Definitions-CSV hydration resolves paths by NAME: only `*_path` columns run
  through `get_path`.** (Since 2026-07-24; previously any dotted or slashed
  value was treated as a path, which broke on ssh targets like
  `user@192.168.64.2`, backend-machine paths like `C:\GP`, and free text like
  `Expansion/Loss`.) A column holding a local path must therefore be named
  `*_path`; blank and `skip` values pass through, `nan` hydrates to `None`,
  cat-ears values resolve with `leave_ref_path_if_fail=True`. Columns whose
  values are only *sometimes* paths (`aoi`, `calibration_parameters_source`)
  are left literal by hydration and resolved by their consumers via
  `hb.looks_like_path(value)` + `p.get_path(value, leave_ref_path_if_fail=True)`.
- **scenarios.csv is authoritative for every attribute it has a column for.**
  Scenario iteration re-hydrates `p` from the CSV row at each scenario, so a
  run-file assignment like `p.aoi = 'RWA'` made after scenario initialization
  wins only until the first scenario iterates, then is silently overwritten.
  Run files may set scenario-varying attributes only inside the
  generate-defaults branch
  (`if not hb.path_exists(p.scenario_definitions_path):`), where they seed the
  CSV about to be written — on later runs that branch is dead code and the CSV
  rules. To run with a different AOI (or any other scenario-varying value),
  point the run at a different scenarios CSV — set
  `p.scenario_definitions_filename` in the caller before `run_project(p)` — which
  is exactly what the pared `_test.csv` pattern is.
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
  flows through the local `build_task_tree`, with the `p.skip_tasks(...)` call
  immediately after it (skipping is run configuration, however the tree was
  assembled).
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
  filename, a stable `<project>_test` project name, and `run_mode='check'`
  so repeated test runs resume in place (`run_mode='fresh_intermediate'` on the
  same stable name forces full recompute while keeping `input/`'s machine
  config; `run_mode='full'` tests the fresh-machine first-run path). Don't fork
  the task tree for tests.
  Test files use the `_test` **suffix** (`run_<project>_test.py`,
  `run_<project>_<variant>_test.py`), never a `run_test_*` prefix.

## Slides from prose: `*_marked.qmd` and revealjs

Some pages double as **slide decks**. Rather than maintaining a prose page and a
deck separately, we write one ordinary `.qmd` and generate the deck from it.

- **`<page>.qmd` is the source and the only file you edit.** It is plain prose
  with `#`/`##` headings, and renders normally as a website page.
- **`<page>_marked.qmd` is GENERATED. Never edit it by hand** — your edits are
  destroyed the next time the deck is built. The `_marked` suffix means exactly
  this: "auto-generated slide version of the file with the same stem." Regenerate
  it after any change to the source.
- Generation is two hazelbean calls, usually wrapped in a small script (see
  `website_dev/scripts/create_seals_walkthrough_slides.py`):

  ``` python
  marked_path = hb.suri(src_qmd_path, 'marked')          # <page>.qmd -> <page>_marked.qmd
  hb.qmd_path_to_marked_qmd_path(src_qmd_path, marked_path)
  hb.qmd_to_revealjs(marked_path)                        # quarto render
  ```

**What the marking pass does** (`hb.qmd_path_to_marked_qmd_path`): it prepends a
revealjs YAML header if the source has none, splits content into slides at `#`
and `##` headings, expands the slide tags below, and auto-wraps any slide whose
content exceeds ~300 characters in `::: r-fit-text` so it scales to the slide.

**Slide tags** are written inline in a heading in the *source* file and are
expanded by the marking pass. They are inert in the prose rendering, so a tagged
source page still reads correctly as a web page:

| tag | effect on the generated slide |
|-----|-------------------------------|
| `<imgbg>` | uses the slide's image as a full-bleed background |
| `<nonincremental>` | reveals the whole list at once instead of bullet by bullet |
| `<list-left-images-right>` | two columns — list at 70% left, images at 30% right |

Because the deck is generated, **keep the source free of anything that only makes
sense in one medium**. Screenshots in particular age badly and are invisible to
search; prefer text and fenced code blocks, which carry to both renderings and
stay correct when the code changes.

## `external_repos/` is out of scope

A directory named `external_repos/` holds checkouts that are *not ours to
change*: someone else's repository, a second clone of one of ours pinned to a
collaborator's branch, or a vendored dependency. **Never edit anything under an
`external_repos/` directory**, and exclude it from every stack-wide sweep —
renames, convention refactors, link fixes, grep-and-replace of any kind.

- A hit inside `external_repos/` is not a finding. Do not report it as work
  remaining, and do not "fix" it for consistency with the canonical copy.
- If a file there genuinely needs to change, the change belongs upstream in the
  repo that owns it, applied through that repo's own workflow.
- When a path appears in both a canonical repo and `external_repos/`, the
  canonical repo is the one to edit. The duplicate is a mirror, and editing it
  creates spurious diffs on whatever branch it happens to be sitting on.

## Archived paths are frozen

Alongside the live tree, every repo accumulates superseded work kept for
reference. **Never edit, delete, reformat, or "fix" anything under an archived
path**, even though it sits inside a canonical repo and even when it contains a
genuine bug. It is a record of what we did, and its value is that it still says
what it said.

A path is archived if any component of it is — case-insensitively, with or
without surrounding underscores — `old`, `older`, `oldest`, `archive`,
`archived`, `deprecated`, `bork`, `bak`, `backup`, `legacy`, `attic`, or an
obvious variant (`*_old_spec.py`, `run_seals_old/`, `_BORK/`). When the name
says the content has been superseded, treat it as superseded.

- A hit inside an archived path is not a finding, exactly as with
  `external_repos/`. Mention it if it explains something; do not report it as
  work remaining.
- Exclude archived paths from stack-wide sweeps: renames, convention
  refactors, link fixes, grep-and-replace of any kind.
- If live code needs something an archived file has, copy the content into a
  live path and change it there. Do not revive the archived file, and do not
  import from it.
- Archiving is a deliberate act by a person. Do not create archive directories,
  move files into them, or rename a file to `*_old` on your own initiative —
  propose it and let the owner decide.

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
