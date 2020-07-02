### plot_util.py - Contains useful plotting functions for papers
### Author: Emily Ramey
### Date: 06/26/20

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plot_dir = "plots/"

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
        'relative_humidity': 'Relative Humidity',
        'airmass': 'Airmass',
        'lgrmswf': 'RMS WF Residual [nm]',
        'aolbfwhm': 'LB-FWHM [as]',
        'lsamppwr': 'Laser Power [W]',
        'aoaomed': 'AO Camera Light [counts]',
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
              save=False, savefile=None
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
        if savefile is None:
            savefile = "VS"
            for x in x_vars:
                savefile = x+"_"+savefile if x not in settings['abbrv'] else settings['abbrv'][x]+"_"+savefile
            for y in y_vars:
                savefile = savefile+"_"+y if y not in settings['abbrv'] else savefile+"_"+settings['abbrv'][y]
            savefile += ".png"
        
        plt.savefig(plot_dir+"data_on_data/"+savefile, bbox_inches='tight')
        
    
    plt.show()