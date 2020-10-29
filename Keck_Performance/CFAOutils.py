### CFAOutils.py: describes useful functions for the CFAO Fall Retreat Hackathon
### Author: Emily Ramey
### Date: 10/29/2020

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import cm

def print_score(target, mae, r2):
    if target=='strehl': units = ''
    if target=='fwhm':
        units='mas'
        target='FWHM'
    print(f"{target.capitalize()} MAE: {mae:.3f} {units}, R-score: {r2:.3f}")

def plot_score(algorithm, target, true, pred):
    if target=='strehl': units = ''
    if target=='fwhm':
        units='mas'
        target = "FWHM"
    plt.plot(true, pred, '.')
    xmin, xmax = plt.xlim()
    plt.plot([xmin, xmax], [xmin, xmax], 'k--', label='1:1 ratio')
    plt.xlabel(f'True {target.capitalize()} {units}')
    plt.ylabel(f'Predicted {target.capitalize()} {units}')
    plt.title(f'{algorithm} Results')
    plt.legend()
    plt.show()

def clean_data(data, dropna=True, feature_limits={}, deltas={}):
    # Clean all columns
    for feature, bounds in feature_limits.items():
        if feature not in data.columns:
            continue
        lo, hi = bounds
        data = data[data[feature] > lo]
        data = data[data[feature] < hi]
    
    for other_mjd, max_delta in deltas.items():
        if other_mjd not in data.columns:
            continue
        delta_t = np.abs(data[other_mjd]-data['mjd'])*24*60 # min
        data = data[delta_t < max_delta]
    
    if dropna: data = data.dropna()
    data.reset_index(inplace=True)
    
    return data

def split_centroids(data): # data = telem_file.a.offsetcentroid[0], for example
    """ Splits mixed x/y centroid data into discrete x and y datasets """
    s = int(data.shape[1] / 2) # number of x or y coord.s
    xrange = range(0, s*2, 2)
    yrange = range(1, s*2, 2)
    x_vals = data[:, xrange]
    y_vals = data[:, yrange]
    
    return x_vals, y_vals

def combine_centroids(data, op=np.std):
    """ 
    Combines centroids from a 1D array with mixed x & y centroid values,
    where the centroid at (0,0) has x = values[0, :] and y = values[1, :]
    """
    # Centroids each have an x and y measurement that need to be combined
    # Data should be num_timestamps x 2*num_lenslets
    x_vals, y_vals = split_centroids(data)
    centroid_magnitude = np.sqrt(x_vals**2 + y_vals**2) # magnitude of offsets
    return op(centroid_magnitude, axis=0)

def plot_array(data, map_file, fig=None, axis=None, arrows=False, start=(0.1,0.1), spacing=None, pt_size=200, cmap = cm.viridis, 
               figsize=(12, 12)):
    """
    Plots an array of lenslet data given a mapping file for the lenslet array.
    For accurate axis labels, pass the spacing of the lenslets in mm.
    pt_size: the multiplier for the lenslets' circle sizes
    """
    # lens map = square grid of 1s and 0s indicating lenslet positions
    lens_map = pd.read_csv(map_file, delim_whitespace=True, header=None).to_numpy()
    len_x = lens_map.shape[0]
    len_y = lens_map.shape[1]
    
    # Set spacing of array
    if spacing is None:
        spacing = 0.2
        tickmarks = False # Not necessarily accurate spacing
    else:
        tickmarks = True # Accurate spacing given
    
    # Make x and y coordinate ranges
    stop_x = start[0]+len_x*spacing
    stop_y = start[1]+len_y*spacing
    x = np.arange(start[0], stop_x, spacing)
    y = np.arange(start[1], stop_y, spacing)
    
    # Make x and y meshgrids based on coordinates and mapping
    xx, yy = np.meshgrid(x, y)
    xx = xx*lens_map
    yy = yy*lens_map
    # Remove zero values
    xx = xx[xx!=0] # Actual x-coords of lenslets
    yy = yy[yy!=0] # Actual y-coords of lenslets
    
    # Set up graph, if needed
    if axis is None or fig is None:
        fig, ax = plt.subplots(figsize = figsize)
    else:
        fig, ax = fig, axis
    
    # Plot lenslets
    if arrows:
        u, v = split_centroids(data) # Passed in as mixed array (change?)
        c_mag = np.sqrt(u**2+v**2) # Magnitude of offset
        # TODO: get colors in there
        artist = ax.quiver(xx, yy, u, v, pivot='mid')
    else:
        artist = ax.scatter(xx, yy, s = data * pt_size, c = data, cmap = cmap)
    
    # Add overall mean & std
    mean = np.mean(data)
    std = np.std(data)
    ax.annotate(f"Mean={np.format_float_scientific(mean, precision=3)}\n"+
                f"$\sigma$={np.format_float_scientific(std, precision=2)}",
                 xy=(.02,.02), xycoords='axes fraction', fontsize=12)
    
    # Add label for each lenslet
    textoffset = spacing*0.6
    for i in range(len(xx)):
        ax.text(xx[i], yy[i] - textoffset, i, horizontalalignment='center', fontsize=12)
    
    # Remove tickmarks if no spacing is given
    if not tickmarks:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
    
    if not arrows:
        # Add colorbar
        color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
        colorbar = fig.colorbar(artist, cax = color_ax)
    
    return (fig, ax, colorbar) if not arrows else artist

def corner_plot(data, labels=None, limits={}, c_var=None, fig=None, axes=None, figsize=(12, 12), 
                fontsize=14, cmap='coolwarm', diag=True):
    """ 
    Performs a corner plot on a dataframe, with optional colorbar.
    diag = True will set 1:1 diagonals for all frames, False will turn them all off
    Passing a list of diagonals (len(diag)=len(data.columns)) will place a diagonal
        only if both variables' positions are True
    """
    # Separate color variable
    if c_var is not None:
        color = data[c_var]
        c_idx = list(data.columns).index(c_var)
        c_label = labels.pop(c_idx)
        data = data.drop(columns=c_var)
    
    # Set colorbar limits
    vmin, vmax = (None, None) if c_var not in limits else limits[c_var]
    
    # Get x and y columns
    y_vars = data.columns[1:]
    x_vars = data.columns[:-1]
    # Set x and y labels
    if labels is not None:
        y_labels = labels[1:]
        x_labels = labels[:-1]
    else:
        y_labels, x_labels = y_vars, x_vars
    
    x_len = len(x_vars)
    y_len = len(y_vars)
    
    # Set up diagonals
    if diag is True:
        diag_x = [True]*x_len
        diag_y = [True]*y_len
    elif diag is False:
        diag_x = [False]*x_len
        diag_y = [False]*y_len
    else: # Separate x and y diagonals
        diag_x = diag[:-1]
        diag_y = diag[1:]
    
    # Set up graph, if needed
    if axes is None or fig is None:
        fig, axes = plt.subplots(y_len, x_len, figsize = figsize, squeeze=False)
    
    plt.subplots_adjust(hspace = 0.04, wspace = 0.03)
    
    for i,y in enumerate(y_vars):
        for j,x in enumerate(x_vars):
            # Get the correct plot
            ax = axes[i, j]
            
            if j>i: # Above diagonal
                ax.axis('off')
                continue
            
            # Y labels and axes
            if j==0: # left axis
                ax.set_ylabel(y_labels[i], fontsize=fontsize)
            if j!=0: # other axes
                ax.set_yticks([])
            
            # X labels and axes
            if i==y_len-1: # bottom axis
                ax.set_xlabel(x_labels[j], fontsize=fontsize)
            else: # other axes
                ax.set_xticklabels([])
            
            # Plot data
            plot = ax.scatter(data[x], data[y], c='k' if c_var is None else color,
                               cmap=cmap, vmin=vmin, vmax=vmax, s=2)
            
            # Set limits
            if x in limits:
                ax.set_xlim(limits[x])
            if y in limits:
                ax.set_ylim(limits[y])
            
            # Set diagonals
            if diag_y[i] and diag_x[j]:
                x1, x2 = ax.get_xlim()
                diag = np.linspace(x1,x2,2)
                ax.plot(diag, diag, 'k--')
    
    # Add colorbar
    if c_var is not None:
        color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
        c = plt.colorbar(plot, cax = color_ax).set_label(label=c_label,size=fontsize)
    
    # Return plot
    return fig, ax