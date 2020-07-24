### plot_util.py - Contains useful plotting functions for papers
### Author: Emily Ramey
### Date: 06/26/20

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib as mpl
from scipy.io import readsav
from astropy.stats import sigma_clip
import os

plot_dir = "plots/"
tel_plots = plot_dir+"telemetry_plots/"
weather_plots = plot_dir+"data_on_data/"
sub_ap_file = "ao_telemetry/sub_ap_map.txt"

good_color = 'blue'
bad_colors = [(1,1,0), (1,128/255.0,0), (1,0,0)]

default_settings = {
    'label': {
        'mass': 'MASS [as]',
        'dimm': 'DIMM [as]',
        'masspro': 'MASSPRO [as]',
        'wind_speed': 'Wind Speed [kts]',
        'wind_direction': 'Wind Direction',
        'temperature': 'Temperature [C]',
        'pressure': 'Pressure [mb]',
        'strehl': 'Strehl Ratio',
        'fwhm': 'FWHM [mas]',
        'mjd': 'MJD',
        'az': 'Azimuth',
        'relative_humidity': 'Relative Humidity [%]',
        'airmass': 'Airmass',
        'lgrmswf': 'RMS WF Residual [nm]',
        'aolbfwhm': 'LB-FWHM [as]',
        'lsamppwr': 'Laser Power [W]',
        'aoaoamed': 'Median Subaperture Light [DN]',
        'wsfrrt': 'WFS Frame Rate',
        'dmgain': 'Target CB gain',
        'dtgain': 'Tip-Tilt Loop Gain',
        'tubetemp': 'Tube Temperature [C]'
    },
    'abbrv': {
        'wind_speed': 'wspeed',
        'temperature': 'tmp',
        'pressure': 'P',
        'strehl': 'str',
        'relative_humidity': 'hum',
        'airmass': 'am',
        'wind_direction': 'wdir',
        'lgrmswf': 'rms-resid',
        'aolbfwhm': 'lbfw',
        'lsamppwr': 'lpow',
        'aoaomed': 'aocam',
    },
    'limits': {
        'strehl': [0, 0.6],
        'fwhm': [45, 125],
    }
}

default_figsize = (20, 10)
default_fontsize = 12

### Grid plotting function
def plot_vars(data, x_vars, y_vars, c_var=None, settings=default_settings,
              figsize=default_figsize, fontsize=default_fontsize, cmap='viridis',
              save=False, filename=None
             ):
    """
    Plots each x-variable against each y-variable in a grid
    c_var is a variable that describes the colorbar, if specified
    labels are specified in a label dictionary, or the default above is used
    """
    x_len = len(x_vars)
    y_len = len(y_vars)
    # Figure setup
    fig, axes = plt.subplots(y_len, x_len, figsize=figsize)
    plt.subplots_adjust(hspace = 0.01, wspace = 0.01)
    
    # Set labels to variables if not passed
    settings = settings.copy()
    for var in x_vars+y_vars+[c_var]:
        if var not in settings['label']:
            settings['label'].update({var: var})
            
    for i,y in enumerate(y_vars):
        for j,x in enumerate(x_vars):
            if x_len==1 and y_len==1:
                ax = axes
            else:
                ax = axes[i, j]
            
            # Y labels and axes
            if j==0: # left axis
                ax.set_ylabel(settings['label'][y], fontsize=fontsize)
            if j!=0: # other axes
                ax.set_yticks([])
            
            # X labels and axes
            if i==y_len-1: # bottom axis
                ax.set_xlabel(settings['label'][x], fontsize=fontsize)
            else: # other axes
                ax.set_xticks([])
            
            #ax.annotate(f'i:{i},j:{j}', xy=(.45, .45), xycoords='axes fraction').set_fontsize(20)
            color = ax.scatter(data[x], data[y], s=1, 
                              c=None if c_var is None else data[c_var], cmap=cmap)
            # Set limits
            if y in settings['limits']:
                ax.set_ylim(settings['limits'][y])
            if x in settings['limits']:
                ax.set_xlim(settings['limits'][x])
        
    
    # Add colorbar
    color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
    plt.colorbar(color, cax = color_ax).set_label(label=settings['label'][c_var],size=fontsize)
    
    if save:
        if filename is None:
            filename = "VS"
            for x in x_vars:
                filename = x+"_"+filename if x not in settings['abbrv'] else settings['abbrv'][x]+"_"+filename
            for y in y_vars:
                filename = filename+"_"+y if y not in settings['abbrv'] else filename+"_"+settings['abbrv'][y]
            filename += ".png"
        
        plt.savefig(weather_plots+filename, bbox_inches='tight')
        
    
    plt.show()
    return



def plot_lenslets(data_file, lnum, shape=None, xlim={}, ylim={}, 
                  fontsize=10, figsize=None, save=False):
    """
    Plots centroid offset of a lenslet in the data array
    lnum: integer, subaperture index from 0 to 304
    """
    data = readsav(data_file)
    
    # Check on values passed
    if type(lnum) is int:
        lnum = [lnum]
    if shape is None:
        shape = (len(lnum), 1)
    if figsize is None:
        figsize=(shape[1]*5, shape[0]*5)
    for num in lnum:
        if num not in xlim:
            xlim[num] = (-1.5, 1.5)
        if num not in ylim:
            ylim[num] = xlim[num]
    
    # subplots
    fig, axes = plt.subplots(nrows=shape[0], ncols=shape[1], squeeze=False, figsize=figsize)
    axes = axes.flatten()
    
    for i,num in enumerate(lnum):
        ax = axes[i]
        
        # Mean of x and y offset centroids
        x_offset = data.a.offsetcentroid[0][:, num*2]
        y_offset = data.a.offsetcentroid[0][:, num*2+1]
        mx = x_offset.mean()
        my = y_offset.mean()

        # Std dev of offset centroids (geometric mean of sigx and sigy)
        sigma = np.sqrt((x_offset.std())**2 + (y_offset.std())**2)

        # Convert radial coord.s to rectangular
        theta = np.linspace(0, 2 * np.pi, 50)
        x = np.cos(theta)*sigma + mx
        y = np.sin(theta)*sigma + my

        # Graph
        offset = ax.scatter(x_offset, y_offset, s = 0.5, c = 'b', label="Centroid offset")
        circle = ax.scatter(x, y, s = 5, c = 'k', label='$1\sigma$ radius')
        mean = ax.scatter(mx, my, s = 30, c = 'r', label="Mean offset")

        # Label
        ax.annotate(f'Subaperture number: {num}', xy=(0.05, 0.95), 
                     xycoords='axes fraction').set_fontsize(fontsize)
        ax.set_xlabel('X offset (arcsec)', fontsize=fontsize)
        if i%shape[0]==0:
            ax.set_ylabel('Y offset (arcsec)', fontsize=fontsize)
        
        if i==0:
            ax.legend(loc = 'best', fontsize=fontsize)

        ax.set_xlim(xlim[num])
        ax.set_ylim(ylim[num])

        ax.grid()
    
    if save:
        filename = tel_plots+"_".join(map(str, lnum))+"_centroids.png"
        plt.savefig(filename, bbox_inches='tight')
    
    plt.show()
    return

def plot_array(data_file, data_type='offset centroid', map_file=sub_ap_file, spacing=0.2,
               start=(0.1,0.1), sig_clip=None, size=100, cmap = mpl.cm.viridis, 
               figsize=(10, 10), fontsize=18, save=False, filename=None):
    """ Plots an array of lenslets with the standard deviation of their centroid offsets """
    data = readsav(data_file)
    if data_type=="offset centroid":
        data = data.a.offsetcentroid[0]
        clabel = "Offset Centroid $\sigma$"
    elif data_type=="residual wavefront":
        data = data.a.residualwavefront[0]
        clabel = "Deformable Mirror $\sigma$ [volt]"
    
    if sig_clip is not None and type(sig_clip) is float:
        sig_clip = [sig_clip]
    
    # Array of 1s and 0s for lenslet positions in a square grid
    sub_ap_map = pd.read_csv(map_file, delim_whitespace=True, header=None).to_numpy()
    len_x = sub_ap_map.shape[0]
    len_y = sub_ap_map.shape[1]
    
    # Make x and y coordinate ranges
    stop_x = start[0]+len_x*spacing
    stop_y = start[1]+len_y*spacing
    x = np.arange(start[0], stop_x, spacing)
    y = np.arange(start[1], stop_y, spacing)
    
    # Make x and y meshgrids based on coordinates and mapping
    xx, yy = np.meshgrid(x, y)
    xx = xx*sub_ap_map
    yy = yy*sub_ap_map
    # Remove zero values
    xx = xx[xx!=0]
    yy = yy[yy!=0]
    
    if data_type=='offset centroid':
        # Find standard deviation of offset centroids
        xrange = range(0, len(xx)*2, 2)
        yrange = range(1, len(yy)*2, 2)
        x_std = np.std(data[:, xrange], axis=0)
        y_std = np.std(data[:, yrange], axis=0)
        std_all = np.sqrt(x_std**2 + y_std**2)
    elif data_type=='residual wavefront':
        # Find standard deviation of residual wavefront
        std_all = np.std(data, axis=0)
        std_all = std_all[range(len(xx))]
    
    # Plot resulting lenslet array
    fig = plt.figure(figsize = figsize)
    
    # Set up different graphs
    if sig_clip is None:
        color = plt.scatter(xx, yy, s = std_all * size, c = std_all, cmap = cmap)
    else:
        sig_clip = np.sort(sig_clip)
        # Plot
        plt.scatter(xx, yy, s=std_all*size, c=good_color, label=f"points < {sig_clip[0]}$\sigma$")
        
        start = len(bad_colors)-len(sig_clip)
        for i,sig in enumerate(sig_clip):
            # Mask as integer array
            q = sigma_clip(std_all, sigma=sig).mask.astype(int)
            # Colors
            rgba_colors = np.zeros((len(std_all),4))
            rgba_colors[:,0:3] = bad_colors[start+i]
            rgba_colors = rgba_colors
            rgba_colors[:,3] = q
            # Plot
            label = f"points>{sig}$\sigma$" if i==len(sig_clip)-1 else f"points<{sig_clip[i+1]}$\sigma$"
            plt.scatter(xx, yy, s=std_all*size, c=rgba_colors, label=label)
        # Legend
        leg = plt.legend()
        [leg.legendHandles[i+1].set_color(bad_colors[start+i]) for i in range(len(bad_colors)-start)]
    
    # Add text
    textoffset = 0.1 if data_type=="offset centroid" else 4
    for i in range(len(xx)):
        plt.text(xx[i], yy[i] - textoffset, i, horizontalalignment='center')
    plt.xlabel("X Coordinate", fontsize=fontsize)
    plt.ylabel("Y Coordinate", fontsize=fontsize)
    
    if sig_clip is None:
        # Add colorbar
        color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
        plt.colorbar(color, cax = color_ax).set_label(label=clabel,
                                                  fontsize=fontsize)
    if save:
        if not filename:
            filename = data_file.split("/")
            filename = filename[5]+"_"+filename[-1].split(".")[0].split("_")[0]
            filename += "_"+data_type.split(" ")[0]+"_std"
            if sig_clip is not None:
                filename+="_sig"
                for sig in sig_clip:
                    filename+="_"+str(np.round(float(sig), 2)).replace(".", "_")
            filename+=".png"
        filename = tel_plots+filename
        plt.savefig(filename, bbox_inches='tight')