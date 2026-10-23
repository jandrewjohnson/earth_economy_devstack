"""Publish base data: combine every dataset manifest (*_base_data_manifest.csv) under the local base_data and publish what
is new or changed as one release.

Each dataset folder carries its own manifest, written by the ingestion script beside it (<name>_base_data_ingestion.py).
A listed raster that isn't a POG yet is converted first, using its row's variable_class.

Leave DRY_RUN = True first: it reports every row (new, changed, unchanged, needs_pog, unfinished, missing locally,
unsupported, not in a manifest) and runs the gate on what would be published, writing nothing. To publish, set
DRY_RUN = False and describe the change in NOTE. Rerunning after publishing is safe: rows whose bytes are already
published are reported as unchanged and skipped. Every real run ends by rebuilding the pages of https://data.teemlabs.org
from the templates in docs/base_data (needs Quarto).
"""
import os

import hazelbean as hb

DRY_RUN = "2026-10-23"
NOTE = "Adding SEALS7 reclassified ESA CCI maps"  # REQUIRED to publish: like a commit message.
BASE_DATA_DIR = None  # None: ~/Files/base_data
SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "base_data")  # the page templates

hb.publish_base_data_from_manifests(base_data_dir=BASE_DATA_DIR, note=NOTE, dry_run=DRY_RUN, site_dir=SITE_DIR)
