"""
This Python module aims to provide a set of function to handle the set up for a run with
the fv2d code, as well as the Athena++ one, and to handle the data output from these codes.
The functions are designed to be used in a Jupyter notebook.

The contents of this module are:
- A dataclass to hold the data from the Athena++ outputs
- A dataclass to handle both the ini files from Athena and fv2d
- A function to set up the run for fv2d :
    - Create the ini file
    - Modify its parameters
    - Write the ini file
    - Run the code
    - Move the data to the right folder
- A function to set up the run for Athena++ :
    - Create the ini file
    - Modify its parameters
    - Write the ini file
    - Compile the specific code (Athena++ has to be recompiled depending on the parameters chosen)
    - Run the code
    - Move the data to the right folder
""" 
import configparser
from pathlib import Path
import subprocess
import shutil
from dataclasses import dataclass
import numpy as np


@dataclass
class AthenaTabular:
    """Tabular format of Athena output
    Format is:
    # i       x1v         rho          press          vel1         vel2         vel3         Bcc1         Bcc2         Bcc3  
    """
    def __init__(self, filename):
        self._data: np.ndarray = np.loadtxt(filename).T
        self.cells: np.ndarray = self._data[0]
        self.x: np.ndarray = self._data[1]
        self.rho: np.ndarray = self._data[2]
        self.p: np.ndarray = self._data[3]
        self.u: np.ndarray = self._data[4]
        self.v: np.ndarray = self._data[5]
        self.w: np.ndarray = self._data[6]
        self.Bx: np.ndarray = self._data[7]
        self.By: np.ndarray = self._data[8]
        self.Bz: np.ndarray = self._data[9]
    
    def rescale(self):
        self.x = self.x + abs(self.x[0])

@dataclass
class Fv2DH5:
    """HDF5 format of fv2d output
    Format is:
    <KeysViewHDF5 ['bx', 'by', 'bz', 'prs', 'rho', 'u', 'v', 'w']>
    """
    def __init__(self, filename, reshape=False):
        import h5py
        self._data = h5py.File(filename, 'r')
        self.x = self._data['x'][:]
        self.y = self._data['y'][:]
        Nite = len(self._data.keys()) - 2 # removing x and y
        ite = self._data[f'ite_{Nite-1:04d}']
        self.Bx = ite['bx'][:]
        self.By = ite['by'][:]
        self.Bz = ite['bz'][:]
        self.p = ite['prs'][:]
        self.rho = ite['rho'][:]
        self.u = ite['u'][:]
        self.v = ite['v'][:]
        self.w = ite['w'][:]
        if reshape:
            N_guess = self.rho.shape[1]
            print("Reshaping to Nx = ", N_guess)
            self.reshape(Nx=N_guess)
    
    def reshape(self, Nx):
        self.x  = self.x[:Nx]
        self.Bx = self.Bx[0]#[:Nx]
        self.By = self.By[0]#[:Nx]
        self.Bz = self.Bz[0]#[:Nx]
        self.p  = self.p[0]#[:Nx]
        self.rho = self.rho[0]#[:Nx]
        self.u  = self.u[0]#[:Nx]
        self.v  = self.v[0]#[:Nx]
        self.w  = self.w[0]#[:Nx]

@dataclass
class IniFile:
    """Dataclass to handle the inifiles"""
    def __init__(self, filename: Path | str, athena_fmt=False):
        self.filename = Path(filename)
        self.athena_fmt = athena_fmt
        self.config = configparser.ConfigParser()
        self.read()

    def __post_init__(self):
        if isinstance(self.filename, str):
            self.filename = Path(self.filename)
        if not self.filename.exists():
            raise FileNotFoundError(f"File {self.filename} does not exist")
        
    def read(self):
        """ Transform the athena format to a standard ini format"""
        if not self.athena_fmt:
            return self.config.read(self.filename)
        with open(self.filename, 'r') as f:
            data  = f.read()
        data = data.replace("<", "[")
        data = data.replace(">", "]")
        return self.config.read_string(data)

    def set_param(self, section, field, value):
        """Set a parameter in the ini file"""
        self.config.set(section, field, str(value))
    
    def write(self, destination=None):
        """Write the ini file"""
        if destination is None:
            destination = self.filename.name
        with open(destination, 'w') as configfile:
            self.config.write(configfile)
        if self.athena_fmt:
            with open(destination, 'r') as f:
                data  = f.read()
            data = data.replace("[", "<")
            data = data.replace("]", ">")
            with open(destination, 'w') as f:
                f.write(data)
    
    def _get_problem(self):
        """The problem is written in the comment field 
            of the Athena ini file.
        """
        if not self.athena_fmt:
            raise ValueError("This is not an Athena ini file")
        return self.config.get("comment", "configure").split("=")[-1].strip()


def run_command(command, executable=None):
    try:
        result = subprocess.run(command, executable=executable, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)
        return e.stderr
    

class Fv2dCode:
    """ Dataclass to handle the fv2d code
    i.e. the ini file, the compilation and the run
    """
    def __init__(self, base_path: Path):
        """
        Parameters
        ----------
        base_path : Path | str
            Path to the root of the fv2d code
        """
        self.base_path = Path(base_path) if isinstance(base_path, str) else base_path
    
    def compile(self, mhd: bool = True, *, parallel: bool = True, clean: bool = False):
        """Compile the fv2d code"""
        command = ["cmake"]
        if clean:
            command.append("--clean")
        command.append("-DCMAKE_BUILD_TYPE=Release")
        if mhd:
            command.append("-DMHD=ON")
        command.append("..")
        subprocess.run(command, cwd=self.base_path / "build", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        command = ["make"]
        if clean:
            subprocess.run(["make", "clean"], cwd=self.base_path / "build", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        if parallel:
            command.append("-j")
        subprocess.run(command, cwd=self.base_path / "build", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    
    def run(self, inifile: Path | str, destination: Path | str = Path('fv2d_output'), *, outname: str = "run"):
        """Run the fv2d code""" 
        inifile = Path(inifile) if isinstance(inifile, str) else inifile
        if not inifile.exists():
            raise FileNotFoundError(f"File {inifile} does not exist")
        destination = Path(destination) if isinstance(destination, str) else destination
        command = [self.base_path, str(inifile)]
        run_command(command, executable=self.base_path / "build/fv2d")
        # Move the data to the right folder 
        destination.mkdir(parents=True, exist_ok=True)
        shutil.move(f"{outname}.h5", destination / Path(f"{outname}_{inifile.stem}.h5"))
        shutil.move(f"{outname}.xdmf", destination / Path(f"{outname}_{inifile.stem}.xdmf"))

ATHENA_PROBS = {
    "shock_tube": "bw", # brio-wu shock tub   
}

class AthenaCode:
    def __init__(self, base_path: Path | str):
        """
        Parameters
        ----------
        base_path : Path | str
            Path to the executable
        """
        self.base_path = Path(base_path) if isinstance(base_path, str) else base_path
    
    def compile(self, inifile: IniFile, *, mhd: bool = True, python_kind: str="python3", flux: str = "hlld"):
        """ Note, on MacOS and some Linux versions
        it is necessary to specify python3 instead of python
        Parameters
        ----------
        prob : str
            Problem to compile
        python_kind : str
            Python version to use
        """
        prob = inifile._get_problem()
        assert prob in ATHENA_PROBS.keys(), f"Problem {prob} not in {ATHENA_PROBS.keys()}"
        command = [python_kind, "configure.py", "--prob", prob, "--flux", flux]
        if mhd:
            command.append("-b")
        subprocess.run(command, cwd=self.base_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        command = ["make", "clean"]
        subprocess.run(command, cwd=self.base_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        command = ["make", "-j"]
        subprocess.run(command, cwd=self.base_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    
    def run(self, inifile: Path | str, destination: Path | str = Path('athena_output')):
        """Run the Athena code""" 
        inifile = Path(inifile) if isinstance(inifile, str) else inifile
        if not inifile.exists():
            raise FileNotFoundError(f"File {inifile} does not exist")
        destination = Path(destination) if isinstance(destination, str) else destination
        command = [self.base_path, "-i", str(inifile)]
        run_command(command, executable=self.base_path / "bin/athena")
        # Move the data to the right folder

        if destination is not None:
            destination.mkdir(parents=True, exist_ok=True)
            for file in Path('.').glob("*.tab"):
                shutil.move(file, destination / Path(f"{file.stem}.tab"))
