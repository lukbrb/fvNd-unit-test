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
from abc import ABC, abstractmethod
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
        self.x1: np.ndarray = self._data[1]
        self.rho: np.ndarray = self._data[2]
        self.p: np.ndarray = self._data[3]
        self.u: np.ndarray = self._data[4]
        self.v: np.ndarray = self._data[5]
        self.w: np.ndarray = self._data[6]
        self.Bx: np.ndarray = self._data[7]
        self.By: np.ndarray = self._data[8]
        self.Bz: np.ndarray = self._data[9]
    
    def rescale(self):
        self.x1 = self.x1 / self.x1[0]
    

@dataclass
class IniFile:
    """Dataclass to handle the inifiles"""
    def __init__(self, filename: Path | str, athena_fmt=False):
        self.filename = filename
        self.athena_fmt = athena_fmt
        self.config = configparser.ConfigParser()
        self.read()

    def __post_init__(self):
        if isinstance(filename, str):
            filename = Path(filename)
        if not filename.exists():
            raise FileNotFoundError(f"File {filename} does not exist")
        
    def read(self):
        """ Transform the athena format to a standard ini format"""
        if self.athena_fmt:
            with open(self.filename, 'r') as f:
                data  = f.read()
            data = data.replace("<", "[")
            data = data.replace(">", "]")
            return self.config.read_string(data)
        else:
            return self.config.read(self.filename)

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


class Code(ABC):
    @abstractmethod
    def compile(self, mhd: bool = False):
        pass
    @abstractmethod
    def run(self, inifile: Path | str, destination: Path | str = Path('.'), *, outname: str = "run"):
        pass


class Fv2dCode(Code):
    """ Dataclass to handle the fv2d code
    i.e. the ini file, the compilation and the run
    """
    def __init__(self, ini_file: Path | str, base_path: Path | str):
        """
        Parameters
        ----------
        ini_file : Path | str
            Path to the ini file
        base_path : Path | str
            Path to the root of the fv2d code
        """
        if isinstance(ini_file, str):
            ini_file = Path(ini_file)
        self.ini_file = IniFile(ini_file)
        self.base_path = Path(base_path) if isinstance(base_path, str) else base_path

    def compile(self, mhd: bool = False):
        """Compile the fv2d code"""
        command = ["cmake"]
        if mhd:
            command.append("-DMHD=ON")
        command.append("..")
        subprocess.run(command, cwd=self.base_path / "build")
        subprocess.run(["make", "-j"], cwd=self.base_path / "build")
    
    def run(self, inifile: Path | str, destination: Path | str = Path('fv2d_output'), *, outname: str = "run"):
        """Run the fv2d code""" 
        inifile = Path(inifile) if isinstance(inifile, str) else inifile
        if not inifile.exists():
            raise FileNotFoundError(f"File {inifile} does not exist")
        destination = Path(destination) if isinstance(destination, str) else destination
        command = [self.base_path]  
        command.append(str(inifile))
        subprocess.run(command, executable=self.base_path / "build/fv2d")
        # Move the data to the right folder 
        if destination is not None:
            destination = destination
            destination.mkdir(parents=True, exist_ok=True)
            shutil.move(f"{outname}.h5", destination / Path(f"{outname}_{inifile.name}.h5"))
            shutil.move(f"{outname}.xdmf", destination / Path(f"{outname}_{inifile.name}.xdmf"))

ATHENA_PROBS = {
    "shock_tube": "bw", # brio-wu shock tub   
}

class AthenaCode(Code):
    def __init__(self, ini_file: Path | str, base_path: Path | str):
        """
        Parameters
        ----------
        ini_file : Path | str
            Path to the ini file
        base_path : Path | str
            Path to the executable
        """
        if isinstance(ini_file, str):
            ini_file = Path(ini_file)
        self.ini_file = IniFile(ini_file, athena_fmt=True)
        self.base_path = Path(base_path) if isinstance(base_path, str) else base_path

    def _get_config(self):
        """ get the configuration arguments for compilation"""
        config = self.ini_file.config
        prob = config.get("comment", "configure")
        probname = prob.split("=")[-1].strip()
        return probname
    
    def compile(self, mhd: bool = True, python_kind="python3"):
        """ Note, on MacOS and some Linux versions
        it is necessary to specify python3 instead of python
        Parameters
        ----------
        prob : str
            Problem to compile
        python_kind : str
            Python version to use
        """
        prob = self._get_config()
        assert prob in ATHENA_PROBS.keys(), f"Problem {prob} not in {ATHENA_PROBS.keys()}"
        command = [python_kind, "configure.py", "--prob", prob]
        if mhd:
            command.append("-b")
        subprocess.run(command, cwd=self.base_path)
        command = ["make", "clean"]
        subprocess.run(command, cwd=self.base_path)
        command = ["make", "-j"]
        subprocess.run(command, cwd=self.base_path)
    
    def run(self, inifile: Path | str, destination: Path | str = Path('athena_output')):
        """Run the Athena code""" 
        inifile = Path(inifile) if isinstance(inifile, str) else inifile
        if not inifile.exists():
            raise FileNotFoundError(f"File {inifile} does not exist")
        destination = Path(destination) if isinstance(destination, str) else destination
        # command = [self.base_path) / "bin/athena"]
        command = [self.base_path]
        command.append("-i")     
        command.append(str(inifile))
        subprocess.run(command, executable=self.base_path / "bin/athena")
        # Move the data to the right folder
         
        if destination is not None:
            destination.mkdir(parents=True, exist_ok=True)
            for file in Path('.').glob("*.tab"):
                shutil.move(file, destination / Path(f"{file.name}.tab"))
