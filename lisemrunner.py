"""
A wrapper to run open lisem from Python
"""
import os
from pathlib import Path
import re

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
    alias = dict(ksat='Ksat calibration', result_dir='Result Directory')

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
        self.name = name
        self.lisempath = Path(lisempath).absolute()
        self.path = Path(runfile).parent
        self.virtual_frame_buffer = virtual_frame_buffer and os.name == 'posix'
        self.runfile = Path(runfile).read_text()
        self['Result Directory'] += self.name + '/'

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
        value = str(value).replace('.', ',')
        new_runfile, n = re.subn(f'^{item}\\ *=\\ *(.*)', item + '=' + value, self.runfile, flags=re.MULTILINE)
        if n == 0:
            raise KeyError(f'{item} not in lisem runfile')
        elif n > 1:
            raise KeyError(f'{item} is duplicated')
        self.runfile = new_runfile

    def items(self):
        for m in re.finditer('(.*)=(.*)', self.runfile, flags=re.MULTILINE):
            yield m.group(1), m.group(2)

    def keys(self):
        for m in re.finditer('(.*)=(.*)', self.runfile, flags=re.MULTILINE):
            yield m.group(1)

    def values(self):
        for m in re.finditer('(.*)=(.*)', self.runfile, flags=re.MULTILINE):
            yield m.group(2)

    def runfilename(self) -> Path:
        """
        Returns:
            The Path of the modified runfile. The runfile will be saved here on calling `save`and `run`
        """
        return self.path / (self.name + '.run')

    def save(self):
        """Save the modified runfile"""
        self.runfilename().write_text(self.runfile)

    def __getattr__(self, item):
        return self[item]

    def run(self, **kwargs):
        """Saves the modified runfile and starts Lisem. On Posix systems usually without a GUI"""
        for k, v in kwargs.items():
            self[k] = v
        self.save()
        run_args = [str(self.lisempath.absolute())]
        env = os.environ
        if self.virtual_frame_buffer:
            run_args.insert(0, 'xvfb-run')
            env |= {'LISEM_CONSOLE': 'X'}

        run_args.extend(['-r', str(self.runfilename().absolute())])
        print('LISEM_CONSOLE=X ' + ' '.join(run_args))

        os.system('LISEM_CONSOLE=X ' + ' '.join(run_args)) # , env=env, shell=True)

