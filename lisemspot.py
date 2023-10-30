#!/usr/bin/env python
import spotpy
import pandas as pd
import numpy as np
import tables
from .lisemrunner import LisemRunner

def u(vmin, vmax, default=None, doc=None):
    """
    Creates a uniform distributed parameter
    :param vmin: Minimum value
    :param vmax: Maximum value
    :param default: Default value
    :param doc: Documentation of the parameter (use reStructuredText)
    :return: The parameter object
    """
    if default is None:
        default = 0.5 * (vmin + vmax)
    return spotpy.parameter.Uniform(vmin, vmax, optguess=default, doc=doc, minbound=vmin, maxbound=vmax)


class Parameters:

    def __get__(self, instance, owner):
        # A magic method for simple use of this object
        return spotpy.parameter.get_parameters_from_setup(self)

    @classmethod
    def to_string(cls):
        params = cls()
        return cls.__doc__ + '\n'.join(
            f':{p.name}: [{p.minbound:0.4g}..{p.maxbound:0.4g}] {p.description}'
            for p in spotpy.parameter.get_parameters_from_setup(params)
        )
    
    Ksat = u(1, 30, 11, 'Ksat calibration')
    Psi = u(0.2, 3, 1.0, 'Psi calibration')
    n0 = u(0.1, 10, 1.0, 'N calibration')
    theta = u(0.1, 2, 1.0, 'Theta calibration')



class LisemSpot:
    parameters = Parameters()

    def __init__(self, lisempath, runfile, name, resultpath, observation_file, silent=False) -> None:
        self.lisempath = lisempath
        self.runfile = runfile
        self.name = name
        self.resultpath = resultpath
        self.obs_df = pd.read_csv(observation_file)
        self.silent = silent


    def _lisem_runner_factory(self, id: int):
        lr = LisemRunner(self.lisempath, self.runfile, f'{self.name}_{id:08d}', self.resultpath, silent=self.silent)
        lr.alias.update({p.name: p.description for p in self.parameters})
        return lr
    
    def simulation(self, vector: Parameters):
        lr = self._lisem_runner_factory(hash(str(vector)) % 10**8)
        sim_df = lr.run(**dict(zip(vector.name, vector.random)))
        lr.clean()
        return np.array(sim_df.Channels)

    def objectivefunction(self, simulation, evaluation):
        return [
            spotpy.objectivefunctions.nashsutcliffe(evaluation, simulation),
            spotpy.objectivefunctions.pbias(evaluation, simulation)
            ]

    def evaluation(self):
        return np.array(self.obs_df.Channels)[:-1]


def read_h5(filename):
    """
    Reads a h5 table created by spotpy. 
    Returns the result dataframe with objective function values and parameters (res)
    and the 2D-array of simulation results. You can get the best run with

    sim[res.like1.idxmax()]

    Returns 
        res, sim
    
    """
    with tables.open_file(filename) as f:
        tab = list(f)[1].read()
        return pd.DataFrame(tab[list(tab.dtype.names[:-2])]), tab[tab.dtype.names[-2]]

