import pytest
import numpy as np
import matplotlib.pyplot as plt

from testing import assert_close

from vipdopt.optimization import FoM, UniformMAEFoM, GradientAscentOptimizer, Device, LumericalOptimization, AdamOptimizer, GaussianFoM, UniformMSEFoM
from vipdopt.simulation import Power


@pytest.mark.smoke()
@pytest.mark.parametrize(
        'opt, device, fom',
        [
            (
                GradientAscentOptimizer(step_size=1e-4), 
                {'randomize': True, 'init_seed': 0},
                UniformMAEFoM('TE+TM', [], [], [], [], range(5), [], 0.5),
            ),
            (
                AdamOptimizer(step_size=1e-4),
                {'randomize': True, 'init_seed': 0},
                UniformMAEFoM('TE+TM', [], [], [], [], range(5), [], 0.5),
            ),
            (
                GradientAscentOptimizer(step_size=1e-4), 
                {'randomize': True, 'init_seed': 0},
                UniformMSEFoM('TE+TM', [], [], [], [], range(5), [], 0.5),
            ),
            (
                AdamOptimizer(step_size=1e-4), 
                {'randomize': True, 'init_seed': 0},
                UniformMSEFoM('TE+TM', [], [], [], [], range(5), [], 0.5),
            ),
        ],
        indirect=['device']
)
def test_step(opt, device: Device, fom: FoM):
    """Test a single step with the gradient."""
    initial_dist = np.abs(device.get_design_variable() - 0.5)

    opt.step(device, fom.compute_fom(device.get_design_variable()), 0)
    new_dist = np.abs(device.get_design_variable() - 0.5)

    assert new_dist.mean() <= initial_dist.mean()  # Should have moved closer to target


@pytest.mark.parametrize(
        'opt, device',
        [
            (
                GradientAscentOptimizer(step_size=1e-4), 
                {'randomize': True, 'init_seed': 0}
            ),
            (
                GradientAscentOptimizer(step_size=1e-4), 
                {'init_density': 1.0}
            ),
            (
                AdamOptimizer(step_size=1e-4),
                {'randomize': True, 'init_seed': 0}
            ),
        ],
        indirect=['device']
)
def test_uniform(opt, device: Device):
    """Test that a device conforms to uniformity in right circumstances."""
    n_freq = 5
    n_iter = 10000

    fom = UniformMAEFoM(
        'TE+TM',
        [],
        [],
        [],
        [],
        range(n_freq),
        [],
        0.5  # Tests  absolute value from 0.5
    )

    for i in range(n_iter):
        
        g = fom.compute_grad(device.get_design_variable())
        opt.step(device, g, i)

    f = fom.compute_fom(device.get_design_variable())
    assert_close(f, 1.0)

    assert_close(device.get_design_variable(), 0.5)
        


@pytest.mark.parametrize(
        'device',
        [
            {'randomize': True, 'init_seed': 0},
        ],
        indirect=True,
)
def test_dual_fom_uniform(device: Device):
    """Using two opposing FoMs should balance out."""
    n_iter = 10000

    # Tests squared error with 0.0
    fom1 = UniformMSEFoM('TE+TM', [], [], [], [], range(5), [], 0.0)
    # Tests squared error with 1.0
    fom2 = UniformMSEFoM('TE+TM', [], [], [], [], range(5), [], 1.0)

    # Since both are equally weighted, should balance out to 0.5 in theory
    fom = fom1 + fom2

    opt = GradientAscentOptimizer(step_size=1e-4)

    n_iter = 50000
    for i in range(n_iter):
        g = fom.compute_grad(device.get_design_variable())
        opt.step(device, g, i)

    # Check that FoM is maximized at x = 0.5
    f = fom.compute_fom(device.get_design_variable())
    assert_close(f, 1.5)
    assert_close(device.get_design_variable(), 0.5)


@pytest.mark.parametrize(
        'opt, device',
        [
            (
                GradientAscentOptimizer(step_size=1e-4), 
                {'randomize': True, 'init_seed': 0}
            ),
            (
                GradientAscentOptimizer(step_size=1e-4), 
                {'init_density': 1.0}
            ),
            (
                AdamOptimizer(step_size=1e-4),
                {'randomize': True, 'init_seed': 0}
            ),
        ],
        indirect=['device']
)
def test_gaussianfom(opt, device: Device):
    fom = GaussianFoM('TE+TM', [], [], [], [], range(5), [], 25, 5)

    for i in range(50000):
        g = fom.compute_grad(device.get_design_variable())
        opt.step(device, g, i)

    f = fom.compute_fom(device.get_design_variable())
    assert_close(f, 1.0)

    w = device.get_design_variable()
    k = fom.kernel[..., np.newaxis]
    
    assert_close(np.square(w - k), np.zeros(w.shape))