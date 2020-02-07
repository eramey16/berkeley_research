### ML_util.py - contains useful functions for running ML algorithms
### Author: Emily Ramey
### Created: 02/06/2020

# imports
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

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
    data_clean = data_clean[data_clean['wind_direction']>0]
    
    return data_clean