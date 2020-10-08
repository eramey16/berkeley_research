### run_ML.py: Contains code for running a Random Forest Fitting algorithm on the specified data or file
### Author: Emily Ramey

from sklearn.metrics import mean_absolute_error as mae
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV
import numpy as np
import pandas as pd
import process_data as pc
import sys
import os

# Important files
default_yaml = "../data/ML_metrics.yaml"

# Usage Message
usage = f"Usage: {sys.argv[0]} <fits_file> <algorithm_abbrev>"

algorithms = {
    'RF': RandomForestRegressor,
    'SVR': SVR,
    'ANN': MLPRegressor,
}
result_types = ["pred", "err", "percent_err"]
mae_str = "Mean Absolute Error"
mape_str = "Mean Absolute Percentage Error"

# def get_ANN_tuples(n_layers=1, layer_sizes=[1, 20, 1]):
#     return 0
#     tuples = []
#     for layer_size in range(layer_sizes[0], layer_sizes[1], layer_sizes[2]):
#         ann_tuple = []
#         for layer in n_layers:
#             for i in range(len_tuple):
#                 ann_tuple.append(layer_size)

# Search Parameters
search_params = {
#     'RF': {"n_estimators":np.arange(10, 200, 20), "max_depth": np.arange(5, 50, 10), 
#           "max_features":np.arange(2, 10)},
    'RF': {"n_estimators":np.arange(10, 100, 20), "max_depth": np.arange(5, 50, 10), 
          "max_features":np.arange(2, 10)},
    'SVR': {'kernel': ['poly'], 'degree':range(1, 10),
          'coef0':[1], 'C':[x for x in np.arange(0.1,5,0.1)], 'gamma':['scale']},
    'ANN': {'learning_rate_init': [0.01], 'hidden_layer_sizes': [(2,),(3,),(4,),(5,),(6,),(7,),(8,),(9,),(10,),
                                                                (11,),(12,),(13,),(14,),(15,),(16,),(17,),(18,),(19,),
                                                                (20,),(2,20),(3,19),(4,18),(5,17),(6,16),(7,15),(8,14),
                                                                (9,13),(10,12),(11,11),(12,10),(13,9),(14,8),(15,7),
                                                                 (16,6),(17,5),(18,4),(19,3),(20,2)],
            'learning_rate': ['invscaling'], 'max_iter': [200]},
#     'ANN': {'activation': ['tanh', 'relu'], 'hidden_layer_sizes': get_ANN_tuples(),
#            'alpha': np.arange(0.0001, .1, 0.001)},
}

regular_params = {
    'RF': {"n_estimators":100, 'max_depth':50, 'max_features':7},
    'SVR': {'kernel': 'poly', 'degree':3},
    'ANN': {'hidden_layer_sizes': (20, 10)},
}

def calc_errs(alg_name, grid_search, data, X, y, train_idxs, test_idxs):
    """ Searches a set of parameters and returns the best performing algorithm """
    
    # Make new columns in dataframe
    cols = []
    for r in result_types:
        s = f"{y.name}_{alg_name}_{r}"
        cols.append(s)
        data[s] = np.nan
    pred_col, err_col, percent_err_col = cols
    
    metric = {}
    # Deal with data
    train_X, test_X = X.iloc[train_idxs], X.iloc[test_idxs]
    train_y, test_y = y[train_idxs], y[test_idxs]
        
    # Find best algorithm
    if grid_search:
        params = search_params[alg_name]
        algorithm = algorithms[alg_name]()
        best = GridSearchCV(algorithm, params, n_jobs=-2, cv=5, verbose=10, scoring="neg_mean_absolute_error")
    else:
        best = algorithms[alg_name](**(regular_params[alg_name]))
    
    best.fit(train_X, train_y)
    
    # Get results
    train_pred = best.predict(train_X)
    test_pred = best.predict(test_X)
    
    # Calculate errors
    train_err, test_err = (train_y-train_pred), (test_y-test_pred)
    train_percent_err, test_percent_err = train_err/train_y, test_err/test_y
    
    # Save error values in data frame
    data.loc[train_idxs, pred_col], data.loc[test_idxs, pred_col] = train_pred, test_pred
    data.loc[train_idxs, err_col], data.loc[test_idxs, err_col] = train_err, test_err
    data.loc[train_idxs, percent_err_col], data.loc[test_idxs, percent_err_col] = train_percent_err, test_percent_err
    
    metric[mae_str+" [TRAIN]"], metric[mae_str+" [TEST]"] = [mae(train_y, train_pred),
                                                                 mae(test_y, test_pred)]
    metric[mape_str+" [TRAIN]"], metric[mape_str+" [TEST]"] = [np.mean(np.abs(train_percent_err)),
                                                                         np.mean(np.abs(test_percent_err))]
    # Format float data
    for key, value in metric.items():
        if "Percentage" in key:
            newval = f"{np.round(value*100, 2)}%"
        else:
            newval = float(np.round(value, 2))
        metric[key] = newval
    
    return metric

def run(data, alg_name, grid_search, pca=False):
    """ Runs Random Forest prediction with or without a PCA transform """
    # Set up structure for aggregated metrics
    agg_metrics = {alg_name: {}}
    # Split data into features and targets
    X, Y = pc.split(data)
    
    if pca: # TODO
        pass
    
    # Seed random generator
    np.random.seed(123)
    idxs = np.arange(0, len(data))
    # Train/test split indices (same for all targets)
    train_idxs, test_idxs = train_test_split(idxs)
    
    # Specify training flag in original dataframe
    data['train'] = [(i in train_idxs) for i in range(len(data))]
    
    # Run ML algorithm on each column
    cols = []
    for y_col in Y.columns:
        y = Y[y_col]
        # Set up data structure
        agg_metrics[alg_name][y_col] = {}
        metric = agg_metrics[alg_name][y_col]
        
        # Initialize algorithm
        algorithm = algorithms[alg_name]() # Create instance of ML class
        # Find best results
        metric.update(calc_errs(alg_name, grid_search, data, X, y, train_idxs, test_idxs))
    
    agg_metrics['settings'] = search_params[alg_name] if grid_search else regular_params[alg_name]
    
    return data, agg_metrics

def check_ML_args(argv):
    """ Checks that the program is being called correctly"""
    filename = pc.check_args(argv, usage)
    
    # Check argv
    if len(argv) < 3:
        print(usage)
        sys.exit(-1)
        
    # Get algorithm name
    alg_name = argv[2]
    if alg_name not in algorithms:
        print("Invalid algorithm name: "+alg_name)
        sys.exit(-1)
    
    grid_search = True if len(argv)==4 and argv[3]=="grid" else False
    
    return filename, alg_name, grid_search

### Main program
if __name__ == "__main__":
    # Read file
    filename, alg_name, grid_search = check_ML_args(sys.argv)
    
    
    _, data = pc.process_metadata(filename)
    
    # Get ML results
    new_data, metrics = run(data, alg_name, grid_search)
    
    grid_tag = "gridsearch" if grid_search else "ML"
    data_savefile = pc.new_filename(filename, grid_tag+"_"+alg_name)
    file_tag = os.path.basename(filename).split("_")[0]
    metrics_savefile = pc.new_filename(f"{file_tag}_{grid_tag}_{alg_name}_metrics.yaml",
                                       truncate=False)
    pc.save_data(new_data, data_savefile)
    pc.save_data(metrics, metrics_savefile)
    