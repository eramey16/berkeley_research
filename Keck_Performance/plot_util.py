### plot_util.py - Contains useful plotting functions for papers
### Author: Emily Ramey
### Date: 06/26/20

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plot_dir = "/u/emily_ramey/work/Keck_Performance/plots/data_on_data/"

default_settings = {
    'wind_speed': {
        'label': 'Wind Speed [kts]',
        'abbrv': 'wspeed'
    },
    'temperature': {
        'label': 'Temperature [C]',
        'abbrv': 'tmp'
    },
    'pressure': {
        'label': 'Pressure [mb]',
        'abbrv': 'P'
    },
    'strehl': {
        'label': 'Strehl Ratio',
        'abbrv': 'str',
        'lim': (0,.6)
    },
    'fwhm': {
        'label': 'FWHM [mas]',
        'lim': (45, 125),
    },
    'mjd': {
        'label': 'MJD'
    },
    'az': {
        'label': 'Azimuth'
    },
    'relative_humidity': {
        'label': 'Relative Humidity',
        'abbrv': 'hum'
    },
    'airmass': {
        'label': 'Airmass',
        'abbrv': 'am'
    },
    'wind_direction': {
        'label': 'Wind Direction',
        'abbrv': 'wdir'
    },
    'lgrmswf': {
        'label': 'RMS WF Residual [nm]',
        'abbrv': 'rms-resid'
    },
    'aolbfwhm': {
        'label': 'LB-FWHM [as]',
        'abbrv': 'lbfw'
    },
    'lsamppwr': {
        'label': 'Laser Power [W]',
        'abbrv': 'lpow'
    },
    'aoaomed': {
        'label': 'AO Camera Light [counts]',
        'abbrv': 'aocam'
    },
    'wsfrrt': {
        'label': 'WFS Frame Rate'
    },
    'dmgain': {
        'label': 'Target CB gain'
    },
    'dtgain': {
        'label': 'Tip-Tilt Loop Gain'
    },
    'tubetemp': {
        'label': 'Tube Temperature [C]'
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
        if var not in settings:
            settings[var] = {'label':var}
            
    for i,y in enumerate(y_vars):
        for j,x in enumerate(x_vars):
            if x_len==1 and y_len==1:
                ax = axes
            else:
                ax = axes[i, j]
            
            # Y labels and axes
            if j==0: # left axis
                ax.set_ylabel(settings[y]['label'], fontsize=fontsize)
            if j!=0: # other axes
                ax.set_yticks([])
            
            # X labels and axes
            if i==y_len-1: # bottom axis
                ax.set_xlabel(settings[x]['label'], fontsize=fontsize)
            else: # other axes
                ax.set_xticks([])
            
            #ax.annotate(f'i:{i},j:{j}', xy=(.45, .45), xycoords='axes fraction').set_fontsize(20)
            color = ax.scatter(data[x], data[y], s=1, 
                              c=None if c_var is None else data[c_var], cmap=cmap)
            # Set limits
            if 'lim' in settings[y]:
                ax.set_ylim(settings[y]['lim'])
            if 'lim' in settings[x]:
                ax.set_xlim(settings[x]['lim'])
        
    
    # Add colorbar
    color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
    plt.colorbar(color, cax = color_ax).set_label(label=settings[c_var]['label'],size=fontsize)
    
    if save:
        if savefile is None:
            savefile = "VS"
            for x in x_vars:
                savefile = x+"_"+savefile if 'abbrv' not in settings[x] else settings[x]['abbrv']+"_"+savefile
            for y in y_vars:
                savefile = savefile+"_"+y if 'abbrv' not in settings[y] else savefile+"_"+settings[y]['abbrv']
            savefile += ".png"
        
        plt.savefig(plot_dir+savefile, bbox_inches='tight')
        
    
    plt.show()