"""The science of the caloric-yield project.

What a yield surface is, and what the model counts as total yield. Plain
arguments in, values out -- no ProjectFlow and no `p`, so these are unit-testable
on their own.

Unlike caloric_yield_utils.py, nothing here belongs in hazelbean: it encodes this
model's domain knowledge and stays with the model however many projects use it.
"""
import numpy as np

from caloric_yield_utils import sum_excluding_ndv


def caloric_yield_surface(offset, n_rows, n_cols):
    """A modelled caloric-yield surface, in kcal per cell.

    Synthetic stand-in so the template runs with nothing downloaded. In a real
    project this is where the model's actual yield computation would live, and
    the run would read observed inputs instead of generating them.
    """
    return np.fromfunction(lambda r, c: ((r + c + offset) % 7) - 1.0, (n_rows, n_cols))


def total_caloric_yield(array, ndv):
    """The model's definition of a scenario's total yield.

    Today this is just a sum over valid cells, and it delegates the arithmetic to
    a science-unaware util. It lives here anyway because *what counts* as total
    yield is a modelling decision -- when the definition grows a weighting or an
    exclusion rule, it grows here, and the util stays generic.
    """
    return sum_excluding_ndv(array, ndv)
