# Devstack guidance for AI coding agents

Shared guidance for Claude Code (and similar agents) working anywhere in the
Earth-Economy devstack. This file is committed and version-controlled so the
whole team gets the same rules; each repo's `CLAUDE.md` imports it, and the EE
Spec conventions live alongside it in `docs/_conventions_reference.md`.

## Reuse before you build

These repositories form one interdependent Python stack. **hazelbean is the
shared base library**: seals, global_invest, gtap_invest, gep, and others all
`import hazelbean as hb` and rely on its utilities.

**Rule: search for an existing utility before writing a new one.**
Before adding any general-purpose helper — file/path handling, I/O, raster or
vector operations, array math, timers, logging, ProjectFlow tasks — search
hazelbean first. Most cross-cutting helpers already exist there as top-level
`hb.*` functions (e.g. `hb.timer()`, `hb.ProjectFlow()`, path utilities).

- Only add a utility to a downstream repo if it is genuinely specific to that
  repo's domain and does not belong in a shared library.
- If you are about to duplicate something that exists in hazelbean (or another
  shared lib), stop and reuse or extend the existing function instead. If the
  existing one is close but not quite right, prefer improving it over forking a
  copy.
- When unsure where a helper belongs, say so and ask rather than silently
  creating a parallel implementation.

## Ownership map (where things live)

| Repo | Owns |
|------|------|
| `hazelbean/hazelbean_dev` | Geospatial + general utilities: paths, GDAL/raster/vector ops, arrays, ProjectFlow task engine. The base every other repo builds on. |
| `seals/seals_dev` | Land-use / land-cover change allocation (SEALS model). |
| `global_invest/global_invest_dev` | Global ecosystem-service / InVEST-style economic modeling on hazelbean. |
| `gtap_invest/gtap_invest_dev` | GTAP-InVEST economic modeling integration. |
| `gtap_invest/gtap_invest_viz` | Visualization for GTAP-InVEST outputs. |
| `gtappy/gtappy_dev` | Python tooling around GTAP. |
| `gep/gep_dev` | GEP modeling. |
| `linneabean/linneabean_dev` | linneabean library. |
| `earth_economy_devstack` | Umbrella / install + docs for the whole stack (specs, scenario definitions). |
| `base_data` | Shared **data**, not code — do not add code utilities here. |

## EE Spec conventions

The coding/naming conventions (identifiers, labels, correspondences,
scenario/file naming, Python style, docstrings, UTF-8, ProjectFlow tasks, Git
Flow) are the canonical reference in `docs/_conventions_reference.md` — the same
content published on the conventions page of the devstack website. Follow it. It
is imported here so a repo that imports this file gets the full spec:

@docs/_conventions_reference.md

## Note for contributors

If you want these rules to apply in *every* repo you open (not just when your
working directory is inside a repo whose `CLAUDE.md` imports this file), add a
single import line to your own user-level `~/.claude/CLAUDE.md`:

```
@<path-to>/earth_economy_devstack/devstack_guidance.md
```
