### AO_modes.py: Contains functions and enumerations for the different AO modes of the system
### Author: Emily Ramey
### Date: 09/11/2020

import enum
import AO_util

parfile = "aoopsmodes.yaml" # Parameter file for AOOPSMode data

### Probably will read this from a file eventually
### AO Operation modes, each tied to a specific number
@enum.unique
class OPSModes(enum.IntEnum):
    NGS = 0
    NGS_STRAP = 1
    LGS = 2
    
    def __getitem__(self, key):
        """ Gets a parameter from setup variables """
        ### Note: should maybe re-initialize variables upon exiting the state
        return self.__state_vars[key]
    
    def __setitem__(self, key, value):
        """ Sets a parameter in setup variables """
        self.__state_vars[key] = value
    
    def get_vars(self):
        """ Returns the full dictionary of setup variables """
        return self.__state_vars.copy()
    
    def __init__(self, value):
        """
        Reads in the parameter file and initializes the AO OPS Mode with its setup variables. 
        The integer value is attached by default as <mode>.value
        """
        modes = AO_util.read_aoopsmodes(parfile)
        if self.name not in modes:
            message(f"Error reading par file: {self.name} not defined")
            return
        self.__state_vars = modes[self.name]

### LGS modes, will fill in when I know more
class LGSModes(enum.IntEnum):
    ZERO = 0

### Rotation modes?
class ROTModes(enum.IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2