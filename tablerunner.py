from pathlib import Path
import pandas as pd
from multiprocessing.pool import Pool
from .lisemrunner import LisemRunner, nse

import logging



class TableRunner:
    """
    This class runs openlisem from a pandas dataframe, (eg. loaded from Excel), either sequentially
    or parallel using multiprocessing

    UNTESTED!
    """
    def __init__(self, lisempath: Path, basepath: Path=None, ncores: int = 1):
        self.ncores = ncores
        self.lisempath = Path(lisempath)
        if basepath:
            self.basepath = Path(basepath)
        else:
            self.basepath = None

    def _make_path(self, path):
        if self.basepath:
            return (self.basepath / path).absolute()
        else:
            return Path(path).absolute()

    def _run(self, runfile, name, **parameters):
        run_path = self._make_path(runfile)
        res_path = run_path.parent.parent / 'res'
        lr = LisemRunner(self.lisempath, run_path, name, res_path)
        return lr.run(**parameters)

    def _run_row(self, row) -> tuple:
        runfile, observation, name = row.iloc[:3]
        return name, observation, self._run(runfile, name, **row.iloc[3:])
    
    @staticmethod
    def _create_result_df(table):
        result_df = pd.DataFrame(table.iloc[:, :3], index=table.index)
        result_df['NSE'] = float("nan")
        result_df['pBias'] = float("nan")
        return result_df
    
    def _run_row_objective(self, row_index_tuple):
        index, row = row_index_tuple
        runfile, observation, name = row.iloc[:3]
        result = self._run(runfile, name, **row.iloc[3:])
        NSE, pbias = nse(observation, result)
        return dict(runfile=runfile, observation=observation, name=name, NSE=NSE, pBias=pbias)

    def _run_parallel(self, table: pd.DataFrame):
        with Pool(self.ncores) as pool:
            return pd.DataFrame(
                pool.imap(self._run_row_objective, table.iterrows()),
                index=table.index
            )

    def _run_sequential(self, table: pd.DataFrame):
        result_df = self._create_result_df(table)
        for index, row in table.iterrows():
            name, observation, result = self._run_row(row)
            NSE, pbias = nse(observation, result)
            result_df['NSE'][index] = NSE
            result_df['pBias'][index] = pbias
            print(index, name, NSE)
        return result_df


    def __call__(self, table: pd.DataFrame):
        if self.ncores == 1:
            return self._run_sequential(table)
        else:
            return self._run_parallel(table)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(level)s: %(message)s')
    df = pd.DataFrame([dict(runfile='run1.run', name='run1-ksat-1', ksat=1, nManning_calib=0.24)])
    tr = TableRunner('./Lisem', ncores=1)

