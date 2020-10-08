### AO_devices.py: Contains code for devices on the AO bench
### Author: Emily Ramey
### Date: 08/07/20

### Preamble
import numpy as np
import pandas as pd
from transitions import Machine
import yaml

### Global variables
WYKO_CLOSED = 1

### A class for reading and writing channel variables
class Channel:
    """ A class for reading and writing channel variables """
    
    def __init__(self, read_channel, write_channel=None, name=None, channel_type=None, allowed=None):
        """
        Initializes a channel and creates (will create once run on the right system)
        an EPICS process variable (PV) to control it programmatically
        name: The human-readable name for the channel
        read_channel: The EPICS channel keyword
        allowed: Allowed values for the channel (if any)
        """
        self.name = read_channel if name is None else name # For now
        self.__values = allowed
        self.type = object if channel_type is None else channel_type
        
        ### Can't get or put values yet bc no system access
#         self.__read_pv = epics.PV(read_channel)
#         self.__write_pv = self.__read_pv if write_channel is None else epics.PV(write_channel)
        # Value for process variable # For now
        self.__read_pv = read_channel if allowed==None or len(allowed)==0 else allowed[0]
        self.__write_pv = read_channel
    
    def read(self):
        """ Gets the value of the channel """
        print(f"\tValue of {self.name} is {self.__read_pv}")
#         return self.__read_pv.get()
        return self.__read_pv

    def write(self, value):
        """ Sets the value of the channel (if allowed) """
        # Check channel type
        if not type(value) is self.type:
            try:
                value = self.type(value)
            except:
                print(f"Invalid type for {self.name}\n\t Received: {type(value)}, Expected: {self.type}")
                return
        
        # Check channel value
        if self.__values is not None and value not in self.__values:
            print(f"Invalid value for {self.name}: {value}")
            return
        
        if self.read() == value: # Don't set twice
            return
        
        print(f"\tSetting {self.name} to {value}")
#       self.__write_pv.put(value)
        self.__write_pv = value
        self.__read_pv = value # Need this until I have actual channels
    
    def __eq__(self, other):
        """ Check for equality """
        if type(other) is type(self):
            return self.value == other.value
        
        return self.value == other
    
    # Hides user access to the PV behind the 'value' variable
    value = property(read, write)

class Flag(Channel):
    """ A channel specifically designed to be a flag (0/1) value """
    
    def __init__(self, read_channel, write_channel=None, name=None):
        """ Initializer """
        super().__init__(read_channel, write_channel=write_channel, name=name, 
                         channel_type=bool, allowed=[0,1])
    
    def set(self):
        """ Sets the flag """
        self.write(1)
    
    def clear(self):
        """ Clears the flag """
        self.write(0)

### TODO
class Stage():
    """ An object for stage devices """
    def __init__(self, name, read_channel, write_channel=None, allowed=None):
        pass

# Here for now: should read from param file
### Global channel variables
# Ones I know
abort_flag = Flag('ao.frautabort', 'abort flag')
dtlp = Channel('ao.dtlp', 'down tip-tilt loop', [0,1])
dmlp = Channel('ao.dmlp', 'deformable mirror loop', [0,1])
trsrec = Channel('ao.trsrec', "telemetry recording")
sod_stage = Channel('ao.obsdname', "SOD stage") # Sodium Dichroic stage
afm_stage = Channel('ao.obamname', "AFM stage") # AFM stage
afs_stage = Channel('ao.obasname', "AFS stage") # AFS stage
wyko_shutter = Channel('ao.aowykoshcmd', "WYKO Shutter")

# Ones I don't know
aofmmove = Channel('ao.aofmmove')
aolpmove = Channel('ao.aolpmove')
rotdest = Channel('dcs.rotdest')
rotmode = Channel('dcs.rotmode')

obptname = Channel('ao.obptname')
lbtmtocp = Channel('ao.lbtmtocp')
lgrmswf = Channel('ao.lgrmswf')

aofcosoc = Channel('ao.aofcosoc')
aofctroc = Channel('ao.aofctroc')
aofcngct = Channel('ao.aofcngct')
aofclgct = Channel('ao.aofclgct')
aofclbct = Channel('ao.aofclbct')

obwfdsrc = Channel('ao.obwfdsrc')
obwfmove = Channel('ao.obwfmove')
aofcc0so = Channel('ao.aofcc0so')
obwpdsrc = Channel('ao.obwpdsrc')
obwpmove = Channel('ao.obwpmove')
obwpname = Channel('ao.obwpname')

guidwave = Channel('dcs.guidwave')
aodrzsim = Channel('ao.aodrzsim')
aodrena = Channel('ao.aodrena')
aotfenb = Channel('ao.aotfenb')
aotsbsgx = Channel('ao.aotsbsgx')
aotsbsgy = Channel('ao.aotsbsgy')
aotsbsgz = Channel('ao.aotsbsgz')
aotssdgx = Channel('ao.aotssdgx')
aotssdgy = Channel('ao.aotssdgy')
aotssdgz = Channel('ao.aotssdgz')
aotsgold = Channel('ao.aotsgold')

aotsx = Channel('ao.aotsx')
aotsy = Channel('ao.aotsy')
aotsgo = Channel('ao.aotsgo')

aofmx = Channel('ao.aofmx')
aofmy = Channel('ao.aofmy')
aofmgo = Channel('ao.aofmgo')

# Laser config?
lsltlson = Channel('ao.lsltlson')
# WFO period # not sure what that is
aofotthr = Channel('ao.aofotthr')
# Other unknowns
lspntrci = Channel('ao.lspntrci')
dtsensor = Channel('ao.dtsensor')

# STRAP state?
ststate = Channel('ao.ststate')
ststby = Channel('ao.ststby')

obsi = Channel('ao.obsi')
# LBWFS
aolbloop = Channel('ao.aolbloop')
aolblpstr = Channel('ao.aolblpstr')
lblpnfra = Channel('ao.lblpnfra')
aolbsvcg = Channel('ao.aolbsvcg')
aofclbct = Channel('ao.aofclbct')
lbtmtocp = Channel('ao.lbtmtocp')

recapsmt = Channel('ao.recapsmt')

dtdst = Channel('ao.dtdst')
utdst = Channel('ao.utdst')

dtservo = Channel('ao.dtservo')
utservo = Channel('ao.utservo')
dmservo = Channel('ao.dmservo')
dtclp = Channel('ao.dtclp')
utclp = Channel('ao.utclp')
dtgain = Channel('ao.dtgain')
dmgain = Channel('ao.dmgain')
utgain = Channel('ao.utgain')

obwnname = Channel('ao.obwnname')

obpsxfs = Channel('ao.obpsxfs')
wssmbin = Channel('ao.wssmbin')
wsfrrt = Channel('ao.wsfrrt')

loops = ['ao.aoloop', 'ao.utlp','ao.aottmode', 'ao.aofomode','ao.lspntrce']
loopnames = ['AO Loop?', 'UT Loop?', 'TT Mode?', 'FO Mode?', 'lspntrce???']
for i,loop_channel in enumerate(loops):
    loops[i] = Channel(loop_channel, loopnames[i])

dtsensors = ['WFS','STRAP']

