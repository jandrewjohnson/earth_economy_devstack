"""Science-unaware helpers for the caloric-yield project.

Nothing in this module knows what caloric yield is. Every function takes plain
arguments and returns a value, so each is testable without a ProjectFlow.

_utils vs _functions -- the rule that decides which file a helper goes in:

    _utils.py      science-unaware. A project in a completely different domain
                   could call it unchanged. This module is therefore a PROMOTION
                   QUEUE, not a filing category: the moment a second project
                   needs one of these, it belongs in hazelbean instead. If
                   nothing ever leaves your _utils, you are not applying the rule.

    _functions.py  encodes this model's domain knowledge. Terminal -- it stays
                   with the model no matter how many projects use the model.

Every function here is already a fair hazelbean candidate; they live locally only
because this toy project is the only caller.
"""
import numpy as np
import hazelbean as hb


def global_geotransform(n_rows, n_cols):
    """Geotransform for a global raster of the given shape."""
    return (-180.0, 360.0 / n_cols, 0.0, 90.0, 0.0, -180.0 / n_rows)


def save_global_geotiff(array, output_path, ndv, n_rows, n_cols):
    """Write a float array as a global WGS84 GeoTIFF.

    With a real input raster you would pass geotiff_uri_to_match= instead and
    this helper would not need to exist.
    """
    hb.save_array_as_geotiff(array.astype(np.float32), output_path,
                             data_type=6, ndv=ndv,
                             geotransform_override=global_geotransform(n_rows, n_cols),
                             projection_override=hb.wgs_84_wkt)


def sum_excluding_ndv(array, ndv):
    """Sum of every cell that is not the no-data value."""
    return float(array[array != ndv].sum())
