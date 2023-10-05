"""
A wrapper to run open lisem from Python
"""
import sys
import os
from pathlib import Path
import re
import pandas as pd
import numpy as np
import locale

class LisemRunner:
    """
    Wraps the Lisem model and its runfile in a python style

    Usage:

    >>> lr = LisemRunner('C:/path/to/Lisem.exe', 'path/to/runfile_template.run', name='variant')

    The result directory of Lisem is taken from the template runfile and extended with the name
    of the runner. It can be changed with the parameter 'Result Directory' or its alias 'result_dir'

    Parameters of Lisem can be changed like a dict:
    eg.

    >>> lr['Canopy Openess'] = 0.5

    The alias dict is used for parameter alias and can be extended with more shortcuts:

    >>> lr['ksat'] = 3.4

    is the same as

    >>> lr['Ksat calibration'] = 3.4

    Lisem is started with the run method, you can use any parameter as a keyword. The Runfile is saved alongside
    the template runfile, except the path has been changed to another Path.

    >>> lr.run(ksat=2)

    """
    alias = dict(
        ksat='Ksat calibration',
        result_dir='Result Directory',
        map_dir='Map Directory',
        n_cores='Nr user Cores',
        adv_options = 'Advanced Options'
    )

    def __init__(self, lisempath, runfile, name, virtual_frame_buffer=True):
        """
        Creates the Lisem wrapper
        Args:
            lisempath: Path to the Lisem executable
            runfile: Path to the Lisem template runfile
            name: Name of the instance. USed to save the modified runfile and used as a directory name for results.
                For parallel execution, make sure to use unique names
            virtual_frame_buffer: A boolean flag to indicate if Lisem should be run in a virtual framebuffer for speed up
                                and to run on headless systems. Ignored on non-posix systems
        """
        locale.setlocale(locale.LC_NUMERIC, '')
        self.runfile = Path(runfile).read_text()
        self.name = name
        self.lisempath = Path(lisempath).absolute()
        self.path = Path(runfile).parent
        self.virtual_frame_buffer = virtual_frame_buffer and os.name == 'posix'
        self.result_path = Path(self['Result Directory'])
        self['Advanced Options'] = 1
        self['n_cores'] = 1

    def __getitem__(self, item):
        item = self.alias.get(item, item.replace('_', ' '))
        m = re.search(f'^{item}\\ *=\\ *(.*)', self.runfile, flags=re.MULTILINE)
        if not m:
            raise KeyError(f'{item} not in lisem runfile')

        for conv in (int, lambda v: float(v.replace(',', '.'))):
            try:
                return conv(m[1])
            except (ValueError, TypeError):
                continue
        else:
            return m[1]

    def __setitem__(self, item, value):
        item = self.alias.get(item, item.replace('_', ' '))

        # Use os locale to convert float to str
        # Check for float and any np.float: https://stackoverflow.com/questions/28292542/how-to-check-if-a-number-is-a-np-float64-or-np-float32-or-np-float16
        if isinstance(value, (np.floating, float)):
            value = locale.format('%0.2f', value)
        else:
            value = str(value)
        print(item, '=', value)
        new_runfile, n = re.subn(f'^{item}\\ *=\\ *(.*)', item + '=' + value, self.runfile, flags=re.MULTILINE)
        if n == 0:
            raise KeyError(f'{item} not in lisem runfile')
        elif n > 1:
            raise KeyError(f'{item} is duplicated')
        self.runfile = new_runfile

    def __contains__(self, item):
        return item in list(self.keys())

    def items(self):
        for m in re.finditer('(.*)=(.*)', self.runfile, flags=re.MULTILINE):
            yield m.group(1), m.group(2)

    def keys(self):
        for m in re.finditer('(.*)=(.*)', self.runfile, flags=re.MULTILINE):
            yield m.group(1)

    def __iter__(self):
        return self.keys()

    def values(self):
        for m in re.finditer('(.*)=(.*)', self.runfile, flags=re.MULTILINE):
            yield m.group(2)

    def __str__(self):
        return f'LisemRunner(name={self.name}, result_path={self.result_path.as_posix()}, run_path={self.runfilename().as_posix()})'

    def runfilename(self) -> Path:
        """
        Returns:
            The Path of the modified runfile. The runfile will be saved here on calling `save`and `run`
        """
        return self.path / (self.name + '.run')

    def save(self):
        """Save the modified runfile"""
        print((self.result_path / self.name).as_posix() + '/')
        self['Result Directory'] = (self.result_path / self.name).as_posix() + '/'
        self.runfilename().write_text(self.runfile)

    def get_result(self):
        """
        Reads the result CSV file ('totalseries.csv'), filters the data based on the first and tenth columns,
        converts the 'Time' column which is an integer, and return the filtered data.

        Returns:
        filtered_df

        """
        sim_file = self['Result Directory'] + 'totalseries.csv'
        print('Load simulation file:',sim_file)
        df = pd.read_csv(sim_file, usecols=[0, 10], skiprows=1)
        # Convert values in 'Column1' to numeric
        df['Time(min)'] = pd.to_numeric(df['Time(min)'])
        # Filter rows with integer values in the first column
        filtered_df = df[df['Time(min)'].astype(int) == df['Time(min)']]
        # Rename the second column to 'Channels'
        filtered_df = filtered_df.rename(
            columns={filtered_df.columns[1]: 'Channels'})
        filtered_df.reset_index(drop=True, inplace=True)
        return filtered_df


    def run(self, **kwargs) -> pd.DataFrame:
        """
        Saves the modified runfile and starts Lisem. On Posix systems usually without a GUI
        
        Returns the filtered result
        """
        for k, v in kwargs.items():
            self[k] = v
        self.save()
        os.makedirs(self.result_path, exist_ok=True)

        run_args = [str(self.lisempath.absolute())]

        if self.virtual_frame_buffer:
            run_args.insert(0, 'LISEM_CONSOLE=X xvfb-run')

        run_args.extend(['-r', str(self.runfilename().absolute())])
        print('$', ' '.join(run_args))
        os.system(' '.join(run_args))
        return self.get_result()
    
    

def nse(obs_file, output_df):
    """
    Calculates the Nash-Sutcliffe Efficiency (NSE) using observation and simulation data from CSV files.
    Parameters:
        obs_file (str): Path to the observation CSV file.
        output_df (pd.DataFrame): A dataframe containing the simulation result, as prepared by filterdata

    Returns:
        float: Nash-Sutcliffe Efficiency (NSE) value.

    """
    import numpy as np
    obs_df = pd.read_csv(obs_file)
    # Calculate the Nash-Sutcliffe Efficiency
    nse = (1 -
           ((output_df.Channels - obs_df.Channels) ** 2).sum() /
           ((obs_df.Channels - obs_df.Channels.mean()) ** 2).sum()
           )
    pbias = (output_df.Channels.mean() - obs_df.Channels.mean()) / obs_df.Channels.mean() * 100
    print('Nash-Sutcliffe Efficiency:', nse, 'pBias:', pbias )
    return nse, pbias


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.stderr.write('Usage: python calibration.py <lisem_path> <runfile> <observation_file>')
    lisem_path, run_path, obs_file = sys.argv[1:4]
    lr = LisemRunner(lisem_path, run_path, os.path.basename(run_path).replace('.run', ''))
    lr.result_path = lr.path.parent.absolute() / 'res'
    lr['map_dir'] = (lr.path.parent / 'map').absolute().as_posix() + '/'
    print(lr)
    sim_df = lr.run()
    nse(obs_file, sim_df)

