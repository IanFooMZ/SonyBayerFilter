"""Code for representing optimizers."""
import abc

import numpy.typing as npt

from vipdopt.optimization.device import Device


# TODO: Add support for otehr types of optimizers
class GradientOptimizer(abc.ABC):
    """Abstraction class for all gradient-based optimizers."""

    @abc.abstractmethod
    def step(self, device: Device, gradient: npt.ArrayLike, iteration: int):
        """Step forward one iteration in the optimization process."""
