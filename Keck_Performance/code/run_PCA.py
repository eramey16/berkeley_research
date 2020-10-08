### run_PCA.py: Runs PCA and saves explained variance ratios
### Author: Emily Ramey

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import numpy as np
import pandas as pd
import process_data as pc
import sys

def run(data, tolerance=1.0):
    """ Runs PCA on data and returns transform """
    # Select feature data
    X, _ = pc.split(data)
    # Scale data to mean 0, std 1 (important)
    X_scaled = StandardScaler().fit_transform(X)
    # Run PCA and get transformed data
    pca = PCA(tol=1.0-tolerance, random_state=pc.random_seed)
    pca_data = pca.fit_transform(X_scaled)
    ncols = pca_data.shape[1]
    pca_data = pd.DataFrame(pca_data, columns=['comp'+str(i) for i in range(ncols)])
    
    # Pull relevant data
    pca_meta = pd.DataFrame()
    pca_meta['explained_variance'] = pca.explained_variance_
    pca_meta['explained_variance_ratio'] = pca.explained_variance_ratio_
    for i,xcol in enumerate(pc.X_cols):
        pca_meta[xcol+"_weight"] = pca.components_[:,i]
    
    for col in pc.Y_cols:
        pca_data[col] = data[col]
    
    # Return transform and relevant data
    return pca, pca_meta, pca_data

if __name__ == "__main__":
    # Read file
    filename = pc.check_args(sys.argv)
    _, data = pc.process_metadata(filename)
    
    # Get PCA results
    _, pca_meta, pca_data = run(data) # Will add tolerance opt later
    
    # Save to file
    meta_savefile = pc.new_filename(filename, "pca_metadata")
    data_savefile = pc.new_filename(filename, "pca_components")
    pc.save_data(pca_meta, meta_savefile)
    pc.save_data(pca_data, data_savefile)
    