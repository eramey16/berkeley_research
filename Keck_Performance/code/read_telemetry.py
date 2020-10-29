### read_telemetry.py: Reads in all telemetry files and computes the mean and standard deviation of their 
### residual wavefront measurements
### Author: Emily Ramey
### Date: 10/14/20

import numpy as np
from scipy.io import readsav
import pandas as pd
import glob
import re

telem_dir = "/g/lu/data/keck_telemetry/"
telem_pattern = telem_dir+"**/*.sav"
lgs_pattern = telem_dir+"**/*LGS*.sav"
savefile = "../data/telem_statistics.dat"

colnames = ['filename', 'mjd', 'rms_mean', 'rms_std']

def get_rms(filenames, test=False):
    """ Returns an array with the mean and standard deviation 
    of the RMS residuals for each telemetry file """
    
    # Make empty dataframe
    N = len(filenames) if not test else 5
    data = pd.DataFrame(index=range(N), columns=colnames) # filename, mjd, rms_mean, rms_std
    data['filename'] = filenames[:N]
    
    ### Extract telemetry data
    for i in range(N):
        # Read telemetry file
        telem = readsav(filenames[i])
        
        # Get MJD
        if 'header' in telem.keys():
            mjd_idx = [i for i in range(len(telem.header)) if 'MJD-OBS' in str(telem.header[i])]
            if len(mjd_idx)!=1: # No MJD field in header or more than one
                print(f"Error in file {i} ({filenames[i]}) header: could not retrieve MJD")
            else: # Save MJD to dataframe
                mjd_idx = mjd_idx[0]
                mjd_i = float(re.findall("\d+\.\d+", str(telem.header[mjd_idx]))[0])
                data.at[i, 'mjd'] = mjd_i
        else:
            print(f"File {i} ({filenames[i]}) has no header")
        
        # Get mean and std of rms residuals
        data.at[i, 'rms_mean'] = np.mean(telem.a.residualrms[0][0])
        data.at[i, 'rms_std'] = np.std(telem.a.residualrms[0][0])
        
        # Log to output
        if i%100==0:
            print("Iteration:", i)
        # Nudge garbage collector
        del telem
    
    return data

if __name__=='__main__':
    # Get relevant filenames
    filenames = glob.glob(lgs_pattern, recursive=True)
    #Extract data
    data = get_rms(filenames)
    # Save to file
    data.to_csv(savefile, index=False)
    print(f"Data saved to {savefile}")