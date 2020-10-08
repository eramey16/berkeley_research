### AO_util.py: Utility functions for the Keck AO system
### Author: Emily Ramey
### Date: 09/11/2020

import yaml
from AO_devices import Channel, Flag, Stage

FLAG = 'flag'

param_dir = "./"
channel_file = param_dir+"channels.yaml"
ops_file = param_dir+"aoopsmodes.yaml"

def message(text):
    """ Sends message to user (or the console, at the moment) """
    print(f"Message: {text}")

def read_yaml(file):
    """ Reads a YAML file """
    with open(file, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    
    return data

def read_aoopsmodes(file=ops_file):
    """ Reads the parameter file and returns the results """
    aoopsmode_data = read_yaml(file)
    
    # Insert logic for setting the SOD stage
    
    return aoopsmode_data

def read_all_channels(file=channel_file):
    """ Reads channels from given YAML file and parses them into variables """
    channel_data = read_yaml(file)
    
    channels = {}
    # Logic for making channel objects
    for tag, info in channel_data.items():
        # Channel variables
        read = info['read_channel']
        name = info.get('name', None)
        write = info.get('write_channel', None)
        data_type = info.get('type', None)
        
        if data_type==FLAG:
            channels[tag] = Flag(read_channel=read, write_channel=write, name=name)
            continue
        
        if data_type:
            data_type = eval(data_type)
        
        channels[tag] = Channel(read_channel=read, write_channel=write, channel_type=data_type,
                                name=name)
    
    return channels
    

### Dummy functions, for now
def abort_acq(data):
    """ Aborts guide star acquisition (TODO) """
    message("Aborting guide star acquisition")
    # TODO

def choose_SOD(lgs):
    """ Allows the user to choose the SOD stage position in NGS_STRAP mode (TODO) """
    choices = ['beamSplitter', 'sodiumDichroic']
    # TODO
    # Make a random choice
    i = np.random.randint(2)
    choice = choices[i]
    message(f"Choosing SOD stage - {choice}")
    
    # Update OPSMode variables
    lgs['aotsgold'] = float(i)
    lgs['obsdname'] = choice

def named_position(dev, name, axis=None):
    # TODO
    print("Getting named position:", dev, name)
    return [1, 2, 3]

def write_all(channels, values):
    """ Writes all values to their corresponding channels """
    if len(channels) != len(values):
        raise ValueError(f"List size mismatch: channel list ({len(channels)}), value list ({len(values)})")
    for i, channel in enumerate(channels):
        channel.write(values[i])

def get_TT_pnt(data):
    """ Placeholder (line 380 in setup_bench.pro) """
    print('Getting TT pointing')
    pass #TODO

def effective_rmag(rmag, aoopsmode=None, obsdname=None, strap=False):
    """ Placeholder (line 494 in setup_bench.pro) """
    print("Checking rmag")
    return 15 # TODO

def setup_strap(straprmag):
    """ Placeholder (ln 499 in setup_bench.pro) """
    status = 0 # TODO
    print("Setting up STRAP")
    return status

def wait_for_devices():
    print("Waiting for devices")
    pass # TODO

def set_framerate(lgsfrrt, prog=2, binning=None):
    print("Setting framerate")
    pass # TODO

def ao_settings_vmag(a):
    print("Getting AO Settings VMAG")
    return 10, 10 # TODO

def wfs_config():
    pass # TODO
 
def update_centroid_gain(data):
    pass #TODO

### Load the cog file (ln 665)
def aoacq_status(data):
    pass # TODO