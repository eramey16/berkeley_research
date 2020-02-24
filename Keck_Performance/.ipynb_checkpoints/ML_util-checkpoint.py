### ML_util.py - contains useful functions for running ML algorithms
### Author: Emily Ramey
### Created: 02/06/2020

# imports
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from astropy.table import Table
import pandas as pd

### Files and folders
root_dir = "/g/lu/data/gc/" # root data directory
tables = "/u/steverobinson/work/keckao/" # folder of data tables found in Steve's directory
meta_file = tables+"lgs_metadata2.fits" # test metadata table
# strehl and fwhm are labels, the rest are features
use_cols = ['strehl', 'fwhm', 'airmass', 'az', 'MASS', 'DIMM', 'wind_speed', 
               'wind_direction', 'temperature', 'relative_humidity', 'pressure']
Y_data = use_cols[:2]
# guessing that DIMM is the DIMM seeing, MASS is the MASS seeing
# not really sure what units anything is in

def runRandomForest(X, y, max_depth, n_estimators, max_features, rand_state):
    """
    Initialize and run a random forest, given feature (X) and target (y) data.
    
    X: array of shape (n_samples, n_features)
    y: array of shape (n_samples,)
    return: validation error of the run
    """
    rf = RandomForestRegressor() # set up regressor
    
    # train-test split
    train_X, val_X, train_y, val_y = train_test_split(X, y, random_state=rand_state)
    rf.fit(train_X, train_y) # fit model
    
    # get predictions
    rf_predictions = rf.predict(val_X)
    rf_mape = np.mean(np.abs((rf_predictions-val_y)/val_y))
    
    # save results as mean absolute percentage error
    map_err = rf_mape
    
    return map_err

def clean(data):
    """
    Filter Steve's telemetry/weather/science data for invalid values:
    Strehl < 0
    FWHM < 30
    negative wind direction
    returns: the filtered array
    """
    data_clean = data.copy().dropna()
    
    # strehl
    data_clean = data_clean[data_clean['strehl']>0]
    
    # fwhm
    data_clean = data_clean[data_clean['fwhm']>30]
    
    # wind direction
    data_clean = data_clean[data_clean['wind_direction']>=0]
    
    return data_clean

def read_and_clean(data_file=meta_file):
    """
    Read in Steve's telemetry/weather/science data from a fits table and clean it
    returns: a pandas DataFrame of X and Y data
    """
    
    ### Read info from Steve's metadata files
    meta_data = Table.read(data_file)
    meta_data = meta_data.to_pandas() # convert to pandas
    
    # extract relevant data
    meta_data = meta_data[use_cols]
    # clean data
    meta_clean = clean(meta_data)
    
    return meta_clean