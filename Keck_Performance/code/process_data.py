### process_data.py - runs a Principal Component analysis on the specified data
### Author: Emily Ramey

### imports
import numpy as np
import pandas as pd
from astropy.table import Table
from astropy.table import MaskedColumn
import sys
import os
import yaml

### Files and folders
data_dir = "../data/"
# strehl and fwhm are labels, the rest are features
use_cols = ['strehl', 'fwhm', 'airmass', 'az', 'mass', 'dimm', 'wind_speed', 
               'wind_direction', 'temperature', 'relative_humidity', 'pressure']
nirc2_mjd = "mjd"
weather_mjd = "cfht_mjd"
seeing_mjds = ["mass_mjd", "dimm_mjd", "masspro_mjd"]
telem_mjd = "telem_mjd"
X_cols = use_cols[2:]
Y_cols = use_cols[:2]

generic_usage = f"Usage: {sys.argv[0]} <fits_file>"
random_seed = 123
NAN_VALUE = -999.0

def remove_nans(array_like):
    """ Removes nans from array and replaces them with NAN_VALUE """
    data = array_like.copy()
    
    # Astropy table object
    if type(data) is Table:
        data = data.filled(NAN_VALUE)
    # Pandas DataFrame object
    elif type(data) is pd.DataFrame:
        data = data.fillna(NAN_VALUE)
    else:
        print("Unrecognized data format:", type(data))
        return None
    
    # Return final data structure
    return data

def replace_nans(array_like):
    """ Replaces NAN_VALUE with np.nan in an array """
    data = array_like.copy()
    
    if type(data) is Table: # Astropy Table
        for col in data.columns:
            mask = (data[col]==NAN_VALUE)
            if type(mask) is not np.ndarray: # Get around Python bug
                continue
            if any(mask): # Mask the column
                data[col] = MaskedColumn(data[col], mask=mask)
        # Fill the masked columns
        data = data.filled(np.nan)
    
    elif type(data) is pd.DataFrame: # Pandas DataFrame
        data[data==NAN_VALUE] = np.nan
    
    else: # Other
        print("Unrecognized data format:", type(data))
        return None
    
    return data

def clean(data, dropna=False, delta_t_weather=None, delta_t_seeing=None, delta_t_telem=None):
    """
    Filter telemetry/weather/science data for invalid values:
    Strehl < 0
    FWHM < 30
    negative wind direction
    NaN values (if specified)
    returns: the filtered array
    """
    data_clean = data.copy()
    data_clean.columns = [x.lower() for x in data.columns]
    
    if dropna:
        data_clean = data_clean.dropna()
    
    # strehl
    data_clean = data_clean[data_clean['strehl']>0]
    
    # fwhm
    data_clean = data_clean[data_clean['fwhm']>30]
    data_clean = data_clean[data_clean['fwhm']<150]
    
    # wind direction
    if 'wind_direction' in data_clean.columns:
        data_clean = data_clean[data_clean['wind_direction']>=0]
    
    # RMS WF Residual
    if 'lgrmswf' in data_clean.columns:
        data_clean = data_clean[data_clean['lgrmswf']<1500]
    
    # Filter weather
    if delta_t_weather and weather_mjd in data_clean:
        delta_t = np.abs(data_clean[weather_mjd]-data_clean[nirc2_mjd])*24*60 # minutes
        data_clean = data_clean[delta_t < delta_t_weather]
    
    # Filter seeing
    if delta_t_seeing and all(s in data_clean for s in seeing_mjds):
        for s_mjd in seeing_mjds:
            delta_t = np.abs(data_clean[s_mjd]-data_clean[nirc2_mjd])*24*60 # minutes
            data_clean = data_clean[delta_t < delta_t_seeing]
    
    # Filter telemetry
    if delta_t_telem is not None and telem_mjd in data_clean:
        delta_t = (data_clean[telem_mjd]-data_clean[nirc2_mjd])*24*3600 # seconds
        if isinstance(delta_t_telem, (float, int)): # Same +/- filter bounds
            data_clean = data_clean[np.abs(delta_t) < delta_t_telem]
        elif isinstance(delta_t_telem, (list, tuple)): # Different +/- filter bounds
            data_clean = data_clean[delta_t > delta_t_telem[0]]
            data_clean = data_clean[delta_t < delta_t_telem[1]]
    
    data_clean.reset_index(inplace=True)
    return data_clean

def split(data):
    """ Splits data into features and targets """
    xcols = [col for col in data.columns if col not in Y_cols]
    return data[xcols], data[Y_cols]

def save_data(data, filename):
    """ Takes a dataframe and a filename and saves data to filename.fits """
    print(f"Writing file: {filename}")
    
    if '.fits' in filename:
        t = Table.from_pandas(data)
        t = remove_nans(t) # Convert nan values to NAN_VALUE
        t.write(filename, overwrite=True)
        
    elif '.yaml' in filename:
        # Check for existing files to update
        checkfile = check_file(filename)
        if checkfile: # Read current data
            with open(checkfile) as f:
                yaml_dict = yaml.load(f, Loader=yaml.FullLoader)
        else:
            checkfile = filename
            yaml_dict = {} # Start with empty dictionary
        # Add new data
        yaml_dict.update(data)
        # Save new YAML data
        with open(checkfile, 'w') as file:
            yaml.dump(yaml_dict, file)
        
    else: # Assume pandas
        data.to_csv(filename, index=False)

def read_file(filename):
    checkfile = check_file(filename)
    if not filename:
        print("Invalid filename: "+filename)
        sys.exit(-1)
    filename = checkfile
    if ".fits" in filename:
        t = Table.read(filename)
        t = replace_nans(t)
        full_data = t.to_pandas()
    else:
        full_data = pd.read_csv(filename)
    
    full_data.columns = [c.lower() for c in full_data.columns]
    return full_data

def process_metadata(filename):
    """ Processes data in filename and returns result as pandas dataframes """
    full_data = read_file(filename)
    if all(col in full_data.columns for col in use_cols):
        prediction_data = full_data[use_cols]
    else: prediction_data = full_data
    
    # Clean data
    full_data_clean = clean(full_data, dropna=False)
    prediction_data_clean = clean(prediction_data, dropna=True)
    
    return full_data_clean, prediction_data_clean

def check_file(filename):
    if not os.path.exists(filename):
        # Check data directory
        if os.path.exists(data_dir+filename):
            filename = data_dir+filename # fix filename
        else: # It's not valid
            return False
    # Return proper filename
    return filename

def check_args(argv, usage=generic_usage):
    """ Verifies and returns filename argument """
    # Check arguments
    if len(argv)<2:
        print(usage)
        sys.exit(-1)
        
    # Get filename
    filename = check_file(argv[1])
    if not filename:
        print(f"{argv[1]} is not a valid path.")
        sys.exit(-1)
    
    return filename

def new_filename(filename, add_on="", truncate=True):
    """ Returns a new filename with the specified additions """
    file_handle = os.path.basename(filename).split(".")[0]
    if truncate:
        file_handle = file_handle.split("_")[0]
    file_ext = os.path.basename(filename).split(".")[1]
    if add_on:
        add_on = "_"+add_on
    savefile = data_dir+file_handle+add_on+"."+file_ext
    return savefile

if __name__=='__main__':
    ### Read info from metadata file
    filename = check_args(sys.argv)
    # Process data
    full, pred = process_metadata(filename)
    
    # Files for clean data
    
    full_savefile = new_filename(filename, "clean_wNA")
    pred_savefile = new_filename(filename, "clean_woNA")
    
    # Save processed files
    save_data(full, full_savefile)
    save_data(pred, pred_savefile)