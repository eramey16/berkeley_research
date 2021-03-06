### plot_util.py - Contains useful plotting functions for papers
### Author: Emily Ramey
### Date: 06/26/20

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm
from scipy.io import readsav
from astropy.stats import sigma_clip
import os
import copy

plot_dir = "../../../Fall_2020_Paper/figures/"
sub_ap_file = "../ao_telemetry/sub_ap_map.txt"

section = "Observations"
plot_type = "telemetry"

good_color = 'blue'
bad_colors = [(1,1,0), (1,128/255.0,0), (1,0,0)]
m1_3 = r'[$m^{\frac{1}{3}}$]'

default_settings = {
    'label': {
        'mass': 'MASS [as]',
        'dimm': 'DIMM [as]',
        'masspro': 'MASSPRO [as]',
        'masspro_half': 'MASSPRO 0.5km '+m1_3,
        'masspro_1': 'MASSPRO 1km '+m1_3,
        'masspro_2': 'MASSPRO 2km '+m1_3,
        'masspro_4': 'MASSPRO 4km '+m1_3,
        'masspro_8': 'MASSPRO 8km '+m1_3,
        'masspro_16': 'MASSPRO 16km'+m1_3,
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
        'tubetemp': 'Tube Temperature [C]',
        'dec_year': 'Decimal Year',
        'rms_err': 'RMS WF Resid (strehl) [nm]',
        'residual_rms': 'RMSWF (Telemetry) [nm]',
        'residual_rms_std': '$\sigma_{rms}$ (Telemetry) [nm]',
    },
    'abbrv': {
        'wind_speed': 'wspeed',
        'temperature': 'tmp',
        'pressure': 'P',
        'strehl': 'str',
        'relative_humidity': 'hum',
        'airmass': 'am',
        'wind_direction': 'wdir',
        'lgrmswf': 'wf-sci',
        'aolbfwhm': 'lbfw',
        'lsamppwr': 'lpow',
        'aoaomed': 'aocam',
        'dec_year': 'yr',
        'residual_rms': 'tel-rms',
    },
    'limits': {
        'strehl': [0, 0.5],
        'fwhm': [40, 140],
        'residual_rms': [0, 600],
        'rms_err': [0, 600],
        'lgrmswf': [0, 600],
        'residual_rms_std': [0, 40],
    }
}

# telem_settings = {
#     'label': default_settings['label'].copy(),
#     'abbrv': default_settings['abbrv'].copy(),
#     'limits': default_settings['limits'].copy(),
# }
telem_settings = copy.deepcopy(default_settings)
telem_settings['label'].update({
    'lgrmswf': 'RMSWF \n(N2 Hdr)',
    'rms_err': 'RMSWF \n(N2 Strehl)',
    'residual_rms': 'RMSWF \n(Telem)',
    'residual_rms_std': '$\sigma_{rms}$ \n(Telem)',
})

default_figsize = (15, 7.5)
default_fontsize = 12
default_fonts = {
    'labels': default_fontsize,
    'legend': default_fontsize,
    'ticks': default_fontsize,
}

def setup(sec, p_type):
    """ Sets the global section variable """
    global section
    global plot_type
    
    path = f"{plot_dir}{section}/"
    if not os.path.exists(path):
        print("making path", path)
        os.mkdir(path)
    section = sec
    plot_type = p_type

def savefig(fig, filename):
    path = f"{plot_dir}{section}/{plot_type}_{filename}"
    plt.savefig(path, bbox_inches='tight')

def get_labels(var_names, settings=default_settings, units=True):
    """ Gets plot labels for variable names """
    single = isinstance(var_names, str)
    if single:
        var_names = [var_names]
    
    labels = []
    for var_name in var_names:
        label = var_name if var_name not in settings['label'] else settings['label'][var_name]
        if not units:
            label = label.split("[")[0].strip()
        labels.append(label)
    
    return labels[0] if single else labels

### Grid plotting function
def plot_vars(data, x_vars, y_vars=None, x_err=None, y_err=None, c_var=None, 
              settings=default_settings, figsize=default_figsize, fontsize=default_fontsize, 
              cmap='viridis', fmt='grid', diag=False, save=False, filename=None):
    """
    Plots each x-variable against each y-variable in a grid
    c_var is a variable that describes the colorbar, if specified
    labels are specified in a label dictionary, or the default above is used
    """
    if fmt=='corner': # All labels passed at once
        y_vars = x_vars[1:]
        x_vars = x_vars[:-1]
    elif y_vars is None:
        print("No y-variables specified")
        return
    
    if fmt=='box':
        bg_color = 'w'
        pt_color = 'k'
        pt_size = 20
    else:
        bg_color = 'w'
        pt_color = 'k'
        pt_size = 2
    
    x_len = len(x_vars)
    y_len = len(y_vars)
    
    if diag is True:
        diag_x = [True]*x_len
        diag_y = [True]*y_len
    elif diag is False:
        diag_x = [False]*x_len
        diag_y = [False]*y_len
    else: # Separate x and y diagonals
        diag_x = diag[:-1]
        diag_y = diag[1:]
    
    # Figure setup
    fig, axes = plt.subplots(y_len, x_len, figsize=figsize, squeeze=False)
    plt.subplots_adjust(hspace = 0.04, wspace = 0.03)
    
    # Set labels to variables if not passed
    settings = settings.copy()
    for var in x_vars+y_vars+[c_var]:
        if var not in settings['label']:
            settings['label'].update({var: var})
    
    # Set color limits
    c_lim = [None,None] if c_var not in settings['limits'] else settings['limits'][c_var]
    vmin, vmax = c_lim
            
    for i,y in enumerate(y_vars):
        for j,x in enumerate(x_vars):
            # Plot axis
            ax = axes[i, j]
            # Background color
            ax.set_facecolor(bg_color)
            
            if fmt=='corner' and j>i: # Above diagonal
                ax.axis('off')
                continue
            elif fmt=='box': # Grid
                ax.xaxis.grid(True, which='major')
            
            # Y labels and axes
            if j==0: # left axis
                ax.set_ylabel(settings['label'][y], fontsize=fontsize)
            if j!=0: # other axes
                ax.set_yticks([])
            
            
            # X labels and axes
            if i==y_len-1: # bottom axis
                ax.set_xlabel(settings['label'][x], fontsize=fontsize)
            else: # other axes
                ax.set_xticklabels([])
            
#             ax.annotate(f'i:{i},j:{j}', xy=(.45, .45), xycoords='axes fraction').set_fontsize(20)
            
            # Plot errorbars (if any)
            if x_err is not None:
                err_data = data[x_err[j]]
                ax.errorbar(data[x], data[y], xerr=err_data, ecolor=pt_color, 
                            fmt='none', capsize=2, elinewidth = 0.5, zorder=0)
            if y_err is not None:
                err_data = data[y_err[i]]
                ax.errorbar(data[x], data[y], yerr=err_data, ecolor=pt_color, 
                            fmt='none', capsize=2, elinewidth = 1, zorder=0)
            
            # Plot data
            color = ax.scatter(data[x], data[y], s=pt_size, c=pt_color if c_var is None else data[c_var],
                               cmap=cmap, vmin=vmin, vmax=vmax, alpha=1, zorder=1)
            # NaN data in red
            if c_var is not None and np.isnan(data[c_var]).any():
                nan_data = data[np.isnan(data[c_var])]
                ax.scatter(nan_data[x], nan_data[y], s=pt_size, c='gray', alpha=1, zorder=2)
            
            # Set limits
            if x in settings['limits']:
                ax.set_xlim(settings['limits'][x])
            if y in settings['limits']:
                ax.set_ylim(settings['limits'][y])
            
            # Set diagonals
            if diag_y[i] and diag_x[j]:
                x1, x2 = ax.get_xlim()
                diag = np.linspace(x1,x2,1000)
                ax.plot(diag, diag, 'k--')
        
    
    if c_var is not None:# Add colorbar
        color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
        plt.colorbar(color, cax = color_ax).set_label(label=settings['label'][c_var],size=fontsize)
    
    if save:
        if filename is None:
            x_names = [x if x not in settings['abbrv'] else settings['abbrv'][x] for x in x_vars]
            y_names = [y if y not in settings['abbrv'] else settings['abbrv'][y] for y in y_vars]
            if fmt=='corner':
                filename = "corner_"+"_".join([x_names[0]]+y_names)
            else:
                filename = "_".join(x_names)+"_VS_"+"_".join(y_names)
            filename += ".png"
        
        savefig(fig, filename)
        
    plt.show()



def plot_lenslets(data_file, lnum, shape=None, xlim={}, ylim={}, 
                  fontsize=default_fonts, figsize=None, save=False):
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
    
    # Update font size
    fonts = default_fonts.copy()
    if type(fontsize) is int:
        fonts = {key: fontsize for key in fonts}
    else:
        fonts.update(fontsize)
    
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
                     xycoords='axes fraction').set_fontsize(default_fontsize)
        ax.set_xlabel('X offset (arcsec)', fontsize=fonts['labels'])
        if i%shape[0]==0:
            ax.set_ylabel('Y offset (arcsec)', fontsize=fonts['labels'])
        
        if i==0:
            ax.legend(loc = 'best', fontsize=fonts['legend'])

        ax.set_xlim(xlim[num])
        ax.set_ylim(ylim[num])

        ax.grid()
        plt.tight_layout()
    
    if save:
        filename = "_".join(map(str, lnum))+"_centroids.png"
        savefig(fig, filename)
    
    plt.show()

def plot_array(data_file, data_type='offset centroid', map_file=sub_ap_file,
               start=(0.1,0.1), sig_clip=None, size=200, cmap = cm.viridis, 
               figsize=(10, 10), fontsize=18, save=False, filename=None):
    """ Plots an array of lenslets with the standard deviation of their centroid offsets """
    data = readsav(data_file)
    if data_type=="offset centroid":
        data = data.a.offsetcentroid[0]
        clabel = "Offset Centroid $\sigma$"
        spacing = 0.2
    elif data_type=="residual wavefront":
        data = data.a.residualwavefront[0]
        clabel = "Deformable Mirror $\sigma$ [volt]"
        spacing = 7
    else:
        print("Unrecognized lenslet array")
        return
    
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
        plt.scatter(xx, yy, s=std_all*size, c=good_color, label=f"< {sig_clip[0]}$\sigma$")
        
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
            label = f"> {sig}$\sigma$" if i==len(sig_clip)-1 else f"< {sig_clip[i+1]}$\sigma$"
            plt.scatter(xx, yy, s=std_all*size, c=rgba_colors, label=label)
        # Legend
        leg = plt.legend()
        [leg.legendHandles[i+1].set_color(bad_colors[start+i]) for i in range(len(bad_colors)-start)]
    
    # Add overall mean & std
    # Is this an ok way to calculate the mean & std? What exactly do we want?
    mean = np.mean(data)
    std = np.std(data)
    plt.annotate(f"Mean={np.format_float_scientific(mean, precision=3)}\n$\sigma$={np.format_float_scientific(std, precision=2)}",
                 xy=(.05,.05), xycoords='axes fraction')
    
    # Add lenslet labels
    textoffset = 0.12 if data_type=="offset centroid" else 4
    for i in range(len(xx)):
        plt.text(xx[i], yy[i] - textoffset, i, horizontalalignment='center')
    plt.xlabel("X Coordinate [mm]", fontsize=fontsize)
    plt.ylabel("Y Coordinate [mm]", fontsize=fontsize)
    file_list = data_file.split("/")
    file_date = file_list[5]
    title = " ".join([x.capitalize() for x in data_type.split(" ")])+"s for "
    title += file_date[4:6]+"/"+file_date[6:]+"/"+file_date[:4]
    plt.title(title, fontsize=fontsize)
    
    if sig_clip is None:
        # Add colorbar
        color_ax = fig.add_axes([.91, .125, 0.02, 0.755])
        plt.colorbar(color, cax = color_ax).set_label(label=clabel,
                                                  fontsize=fontsize)
    if save:
        if not filename:
            filename = file_list[5]+"_"+file_list[-1].split(".")[0].split("_")[0]
            filename += "_"+data_type.split(" ")[0]+"_std"
            if sig_clip is not None:
                filename+="_sig"
                for sig in sig_clip:
                    filename+="_"+str(np.round(float(sig), 2)).replace(".", "_")
            filename+=".png"
        savefig(fig, filename)
    plt.show()

def correlation_matrix(data, var_names=None, corr_type='pearson', figsize=(10,10), cmap=cm.coolwarm, 
                       fontsize=12, cax=[.91, .125, 0.02, 0.755], flatten=False, settings=default_settings,
                       save=False, filename=None):
    fig, ax = plt.subplots(figsize=figsize)
    if var_names is None:
        var_names = data.columns
    
    corr_data = data[var_names]
    
    corr = corr_data.corr(method=corr_type)
    
    # Plot
    if flatten: # 1D plot
        corr_strength = np.abs(corr[flatten])
        corr_strength = corr_strength[var_names]
        
        # Sort by corr. strength
        corr_strength = corr_strength.sort_values(ascending=False)
        
        # Remove self-reference
        corr_strength = corr_strength[corr_strength.index!=flatten]
        
        ticks = np.arange(len(corr_strength))
        labels = get_labels(corr_strength.index)
        ax.bar(ticks, corr_strength)
        
        # Center line
        ax.plot([-2, len(corr_strength)+1], [0, 0], "k-")
        ax.set_xlim([-2, len(corr_strength)+1])
        
    else: # 2D plot
        labels = get_labels(var_names, settings, units=False)
        ticks = np.arange(len(labels))
        color = ax.imshow(corr, interpolation="nearest", cmap=cmap, vmin = -1)
        ax.grid(True)
        ax.set_yticks(ticks)
        ax.set_yticklabels(labels,fontsize=fontsize)
        
        # Add colorbar
        color_ax = fig.add_axes(cax)
        plt.colorbar(color, cax = color_ax).set_label("Correlation strength",fontsize=fontsize)
    
    # Finish plot
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels,fontsize=fontsize,rotation=50, ha='right')
    
    if save:
        if filename is None:
            print("No filename specified")
        else:
            savefig(fig, filename)
    plt.show()