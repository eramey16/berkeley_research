import numpy as np
import glob
from astropy.io import fits
from scipy import optimize
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib import colors
from collections import defaultdict

     
#define all of the gaussian fitting functions
def gauss(height, x0, y0, sigmax, sigmay, theta):
    a = (np.cos(theta)**2) / (2*sigmax**2) + (np.sin(theta)**2) / (2*sigmay**2)
    b = (np.sin(2*theta)) / (2*sigmax**2) - (np.sin(2*theta)) / (2*sigmay**2)
    c = (np.sin(theta)**2) / (2*sigmax**2) + (np.cos(theta)**2) / (2*sigmay**2)
    return lambda x, y: height * np.exp((-a*(x-x0)**2)-(b*(x-x0)*(y-y0))-(c*(y-y0)**2))

def gauss_params(data):
   total = data.sum()
   x1, y1 = np.indices(data.shape)
   x2 = (x1 * data).sum() / total
   y2 = (y1 * data).sum() / total
   col = data[:, int(y2)]
   row = data[int(x2), :]
   sigmax = np.sqrt(abs(((np.arange(col.size) - y2) ** 2) * col).sum() /
                    col.sum())
   sigmay = np.sqrt(abs(((np.arange(row.size) - x2) ** 2) * row).sum() /
                    row.sum())
   height = data.max()
   theta = 0
   return height, x2, y2, sigmax, sigmay, theta

def gauss_fit(data):
   params = gauss_params(data)
   errorfunction = lambda p: np.ravel(gauss(*p)(*np.indices(data.shape)) -
                                      data)
   p, success = optimize.leastsq(errorfunction, params)
   return p

def ee(psf, r, size = 100): #finds the encircled energy of a psf (fits file data) within a raidus r
    x = range(0, size)
    y = range(0, size)
    X,Y = np.meshgrid(x,y)
    X -= size // 2 #puts the center at corrdinate 0
    Y -= size // 2
    dist = np.hypot(X, Y) #Makes the X, Y array where each value is it's distance to the center
    x_index, y_index = np.where(dist <= r) 
    return np.sum(psf[x_index, y_index]) # adds up all the values of the pixels within a radius r

#function that loads in the fits file output by the simulation
#inputs: N: int, dimension of the grid, Min:minimum position, Max:max postion, wvls: list of names of wavelength bands
#outputs: a dictionary with keys the name of the bands, and value a list of the psfs in that band
def load_files(N, Min, Max, wvls, path):
    pix_scale = 0.0200549563786008 #number of arcseconds per pixel
    tot_intensity = 7.16935519227643 #sum of all pixels, obtained from header


    x = np.linspace(Max, Min, N) #arrays of all the x and y positions
    y = np.linspace(Max, Min, N)
    X,Y = np.meshgrid(x, y) #arrays of all the x and y coordinates
    X = X.flatten()
    Y = Y.flatten()

    X_fixed = [] # fixes the numbers so integers don't have decimal points
    Y_fixed = []

    #loops convert whole numbers to integers
    for i in range(len(X)):
        val = X[i]
        if val % 1 == 0:
            X_fixed.append(int(val))
        else:
            X_fixed.append(val)

    for i in range(len(Y)):
        val = Y[i]
        if val % 1 == 0:
            Y_fixed.append(int(val))
        else:
            Y_fixed.append(val)


    files = [] #will append all of the filenames here
    for i in range(X.size):
        pre = "evlpsfcl_1_"
        filename = path + pre + "x" + str(X_fixed[i]) + "_y" + str(Y_fixed[i]) + ".fits"
        files.append(filename)
    
    psfs = {}
    
    for wvl in wvls:
        psfs[wvl] = []
    
    for i in range(len(wvls)):
        for file in files:
            data = fits.getdata(file, i, memmap = False)
            psfs[wvls[i]].append(data)
            
    return psfs


#function that finds the parameters, such as strehl and FWHM, of each psf
#input psfs:output of load_files, size: dimension of PSF (usually 100)
#output: a dictionary of dictionary, of the format {'K': {"strehl:[], "FWHM":[]...
def find_parameters(psfs, size):
    pix_scale = 0.0200549563786008
    tot_intensity = 7.16935519227643
    parameters = {}
    for wvl in psfs:
        parameters[wvl] = defaultdict(list)
    
    for wvl in psfs:
        for i in range(len(psfs[wvl])):
            psf = psfs[wvl][i]
            strehl = np.max(psf)
            parameters[wvl]["strehl"].append(strehl)
            params = gauss_fit(psf)
            sigmax = params[3]
            sigmay = params[4]
            FWHMx = 2 * np.sqrt(2*np.log(2)) * sigmax # converts sigma to FWHM
            FWHMy = 2 * np.sqrt(2*np.log(2)) * sigmay
            FWHMavg = ((FWHMx + FWHMy) / 2) * pix_scale * 1000 #converts from pixels to mas
            parameters[wvl]["FWHMx"].append(FWHMx)
            parameters[wvl]["FWHMy"].append(FWHMy)
            parameters[wvl]["FWHMavg"].append(FWHMavg)
            normalized = (1 / tot_intensity) * psf # normalizes the data in order to find ee50
            radii = np.arange(0, int(size / 2),0.1)
            ee_list = [] #list of encircled energies for all possible radii
            for radius in radii:
                ee_list.append(ee(normalized, radius, size))
            dist_from_50 = abs(np.array(ee_list) - 0.5) #find the energy that's closest to 0.5
            ee50_index = list(dist_from_50).index(min(dist_from_50))
            ee50 = radii[ee50_index] * pix_scale #find radius that corresponds to ee closest to 0.5
            parameters[wvl]["ee50"].append(ee50)
            ellipticity = 0 #calculates ellipticity
            if FWHMx > FWHMy:
                ellipticity = 1 - (FWHMy / FWHMx)
            else:
                ellipticity = 1 - (FWHMx / FWHMy)
            parameters[wvl]['ellipticity'].append(ellipticity)
            x0 = params[1]
            y0 = params[2]
            parameters[wvl]['x0'].append(x0)
            parameters[wvl]['y0'].append(y0)
            theta = params[5]
            parameters[wvl]['theta'].append(theta)
            
    return parameters

#function that plots the grids of psfs
#input: psfs: output of load_files, parameters: output of find_parameters, wvl:name of wvl band, N: dimension of grid
#output: plot of psf grid with over plotted FWHM and other parameters
def grid(psfs, parameters, wvl, N):
    #title = AO_type + " NGS at " + str(position)
    #name = AO_type + "_"+str(position[0])+"_"+str(position[1])+"_grid.png"
    fig  = plt.figure(1, figsize = (15,15))
    #plt.title(title)
    middle_index = int(((N**2) - 1) / 2)
    plot_max = np.max(psfs[wvl][middle_index])
    for i in range(len(psfs[wvl])):
        ax = fig.add_subplot(N,N, i+1)
        data = psfs[wvl][i]
        ax.imshow(data, norm=colors.LogNorm(vmin=0.001, vmax=plot_max), origin = "lower")
        strehl = parameters[wvl]["strehl"][i]
        x0 = parameters[wvl]["x0"][i]
        y0 = parameters[wvl]["y0"][i]
        theta = parameters[wvl]["theta"][i]
        FWHMx = parameters[wvl]["FWHMx"][i]
        FWHMy = parameters[wvl]["FWHMy"][i]
        FWHMavg = parameters[wvl]["FWHMavg"][i]
        xy  = (x0,y0) #defines center of ellipse
        e1 = patches.Ellipse(xy, FWHMy, FWHMx, angle =360 - np.degrees(theta), fill = False)
        ee50 = parameters[wvl]["ee50"][i]
        ellipticity = parameters[wvl]["ellipticity"][i]
        ax.add_patch(e1)
        ax.set_xticklabels(["0.25", "0", "-0.25"])
        ax.set_xticks([62.5 ,50, 37.5])
        ax.set_yticklabels(["-0.25", "0", "0.25"])
        ax.set_yticks([37.5 ,50, 62.5])
        ax.text(70, 70, 'Strehl = ' +'%.3f'%(strehl), color = "white")
        ax.text(70,65, 'FWHM = ' + '%.3f'%(FWHMavg) + " mas", color = "white")
        ax.text(70,27, 'Ellipticity = ' + '%.3f'%(ellipticity), color = "white")
        ax.text(70,32, 'EE50 = ' + '%.3f'%(ee50), color = "white")
        plt.xlim(75,25)
        plt.ylim(25,75)  
    plt.show()
    
#function that plots the average FWHM of each PSF
#inputs: parameters: output of find_parameters, wvl: name of wvl band, size: dimension of grid
#output: plot of the avg FWHM of each PSF in the grid
def plot_FWHM(parameters, wvl, size):
    #title = AO_type + " NGS at " + str(position)
    #name = AO_type + "_"+str(position[0])+"_"+str(position[1])+"_FWHM.png"
    FWHM_list = parameters[wvl]["FWHMavg"]
    FWHM = np.array(FWHM_list).reshape(size,size) #turns the list of FWHM's into a 5x5 array
    fig = plt.figure(figsize = (6,6))
    plt.imshow(FWHM)
    plt.colorbar(label = "FWHM [mas]")
    #plt.xticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.yticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.title(title)
    plt.show()
    
#same function as plot_FWHM but plots strehl instead
def plot_strehl(parameters, wvl, size):
    #title = AO_type + " NGS at " + str(position)
    #name = AO_type + "_"+str(position[0])+"_"+str(position[1])+"_FWHM.png"
    strehl_list = parameters[wvl]["strehl"]
    strehl = np.array(strehl_list).reshape(size,size) #turns the list of FWHM's into a 5x5 array
    fig = plt.figure(figsize = (6,6))
    plt.imshow(strehl)
    plt.colorbar(label = "strehl")
   #plt.xticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.yticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.title(title)
    plt.show()
    
#function that plots ee50 radius for each PSF    
def plot_ee50(parameters, wvl, size):
    #title = AO_type + " NGS at " + str(position)
    #name = AO_type + "_"+str(position[0])+"_"+str(position[1])+"_FWHM.png"
    ee50_list = parameters[wvl]["ee50"]
    ee50 = np.array(ee50_list).reshape(size,size) #turns the list of FWHM's into a 5x5 array
    fig = plt.figure(figsize = (6,6))
    plt.imshow(ee50)
    plt.colorbar(label = "ee550 [mas]")
   #plt.xticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.yticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.title(title)
    plt.show()
    
#function that plots the ellipticity of each PSF
def plot_ellipticity(parameters, wvl, size):
    #title = AO_type + " NGS at " + str(position)
    #name = AO_type + "_"+str(position[0])+"_"+str(position[1])+"_FWHM.png"
    ellipticity_list = parameters[wvl]["ellipticity"]
    ellipticity = np.array(ellipticity_list).reshape(size,size) #turns the list of FWHM's into a 5x5 array
    fig = plt.figure(figsize = (6,6))
    plt.imshow(ellipticity)
    plt.colorbar(label = "ellipticity")
   #plt.xticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.yticks(np.arange(7), ('15', '7.5', '0', '-7.5', '-15'))
    #plt.title(title)
    plt.show()
    
def analysis(N, Min, Max, wvls, path, size):
    psfs = load_files(N, Min, Max, wvls, path)
    parameters = find_parameters(psfs, size)
    for wvl in wvls:
        grid(psfs, parameters, wvl, N)
        plot_FWHM(parameters, wvl, N)
        plot_strehl(parameters, wvl, N)
        plot_ee50(parameters, wvl, N)
        plot_ellipticity(parameters, wvl, N)