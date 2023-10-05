from pathlib import Path

import pandas as pd
from multiprocessing.pool import Pool
from lisemrunner import LisemRunner
class TableRunner:
    """
    This class runs openlisem from a pandas dataframe, (eg. loaded from Excel), either sequentially
    or parallel using multiprocessing

    UNTESTED!
    """
    def __init__(self, table: pd.DataFrame, lisempath: Path, basepath: Path):
        self.table = table

        self.lisempath = Path(lisempath)
        self.basepath = Path(basepath)

    def _run(self, runfile, name, **parameters):
        lr = LisemRunner(self.lisempath, self.basepath / runfile, name)
        return lr.run(**parameters)

    def _run_row(self, row) -> tuple:
        runfile, name, observation = row.iloc[:3]
        return name, observation, self._run(runfile, name, **row.iloc[3:])

    def run_parallel(self, ncores=None):
        with Pool(ncores) as pool:
            rows = [row for _, row in self.table.iterrows()]
            result_df = pd.DataFrame(self.table.iloc[:, :2])
            result_df['NSE'] = float("nan")
            result_df['pBias'] = float("nan")
            for name, observation, result in pool.imap(self._run_row, rows):
                print(name)

if __name__ == '__main__':
    ...