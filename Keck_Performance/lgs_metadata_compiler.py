import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import datetime
import pytz
import time
import glob
import urllib
from astropy.table import Table
from astropy.time import Time, TimezoneInfo
from astropy import units as u, constants as c
from datetime import datetime, timezone
from astropy.io import fits


root_directory = '/g/lu/data/gc/'

verbosity = False


def vprint(string):
    if verbosity == True:
        print(string)

# Functions for time and date conversions
def convert_dates(df):
    dates = []
    for i, row in df.iterrows():
        if int(row[3] + 10 < 23):
            datestring = str(int(row[0])) + '-' + str(int(row[1])) + '-' + str(int(row[2])) + 'T' + str(int(row[3]) + 10) + ':' + str(int(row[4])) + ':' + str(int(row[5]))
        else:
            datestring = str(int(row[0])) + '-' + str(int(row[1])) + '-' + str(int(row[2]) + 1) + 'T' + str(int(row[3]) - 14) + ':' + str(int(row[4])) + ':' + str(int(row[5]))
        dt = Time(datestring,format='isot')
        dates.append(dt.mjd)

    return dates


def month_number(month):
    if month == 'mar':
        return '03'
    elif month == 'apr':
        return '04'
    elif month == 'may':
        return '05'
    elif month == 'jun':
        return '06'
    elif month == 'jul':
        return '07'
    elif month == 'aug':
        return '08'
    elif month == 'sep':
        return '09'


def hst_to_utc(date):
    tz = pytz.timezone('US/Hawaii')
    
    return tz.normalize(tz.localize(date)).astimezone(pytz.utc)


def hst_to_mjd(daterow):
    row = [int(num) for num in daterow]
    if len(daterow) == 6:
        dt = datetime(row[0], row[1], row[2], row[3], row[4], row[5])
    else:
        dt = datetime(row[0], row[1], row[2], row[3], row[4])
    t = Time(hst_to_utc(dt))
    
    return t.mjd


# Functions
def find_nearest(array, value):
    i = (np.abs(array-value.value)).argmin()
    
    return i, array[i]


def get_massdimm(dateString):
    '''
    Pass in a datestring and this checks if the files have already been retrieved,
    and saves three files (mass seeing, dimm seeing, mass Cn2 profile) to subfolders
    by year and month in the current directory if they have not.
    '''

    urlRoot = 'http://mkwc.ifa.hawaii.edu/current/seeing/'
    seeing_directory = root_directory + 'seeing_data/'
    destination = seeing_directory + dateString[:6] + '/'
    
    if os.path.exists(seeing_directory) == False:
        os.makedirs(seeing_directory)
#         print('Created new seeing directory')
    if os.path.exists(destination) == False:
        os.makedirs(destination)
#         print('Created new folder: ' + destination)
        
    fileMASS = dateString + '.mass.dat'
    fileDIMM = dateString + '.dimm.dat'
    filePROF = dateString + '.masspro.dat'

    if os.path.isfile(destination + fileMASS):
#         print('File already exists')
        return

    urlMASS = urlRoot + 'mass/' + fileMASS
    urlDIMM = urlRoot + 'dimm/' + fileDIMM
    urlPROF = urlRoot + 'masspro/' + filePROF

#     print(urlMASS)
#     print(destination + fileMASS)
    
    try:
        request = urllib.request.urlretrieve(urlMASS, destination + fileMASS)
        request = urllib.request.urlretrieve(urlDIMM, destination + fileDIMM)
        request = urllib.request.urlretrieve(urlPROF, destination + filePROF)
    except:
#         print('Could not retrieve files')
        return
    
    
def populate_df(datestring, verbose=False):
    '''
    This takes in an lgs datestring (two digit year, first three letters of month,
    lgs, and a number if there were multiple days, ie. 04jullgs1), looks for and
    downloads all associated cfht and seeing data, and returns the df to be
    appended to a master table
    '''   

    print(datestring)

    path = root_directory + 'lgs_data/%s/clean/kp/' % datestring
    
    if os.path.isfile(path + 'strehl_source.txt') == True:
        df = pd.read_csv(path + 'strehl_source.txt', delim_whitespace = True, header = None, skiprows = 1)
    elif os.path.isfile(path + 'irs33N.strehl') == True:
        df = pd.read_csv(path + 'irs33N.strehl', delim_whitespace = True, header = None, skiprows = 1)
    else:
#         unused_data.append(datestring)
        return
        
    df.columns = ['file', 'strehl', 'rms_err', 'fwhm', 'mjd']
    
    df['epoch'] = datestring

    mjd_list = Time(df['mjd'], format = 'mjd')

    
    # Add all metadata from fitsfile

    airmass = []
    itime = []
    coadds = []
    band = []
    az = []
    dmgain = []
    dtgain = []
    aolbfwhm = []
    wsfrrt = []
    lsamppwr = []
    lgrmswf = []
    xref = []
    yref = []
    xstrehl = []
    ystrehl = []
    
    for i in range(len(df['file'])):
        # Get header info
        fitsfile = path + df['file'][i]
        with fits.open(fitsfile) as file:
            hdr = file[0].header
        airmass.append(float(hdr['AIRMASS']))
        itime.append(float(hdr['ITIME']))
        coadds.append(hdr['COADDS'])
        band.append(hdr['FWINAME'])
        az.append(float(hdr['AZ']))
        dmgain.append(float(hdr['DMGAIN']))
        dtgain.append(float(hdr['DTGAIN']))
        xref.append(float(hdr['XREF']))
        yref.append(float(hdr['YREF']))
        xstrehl.append(float(hdr['XSTREHL']))
        ystrehl.append(float(hdr['YSTREHL']))
        try:
            wsfrrt.append(float(hdr['WSFRRT']))
        except:
            wsfrrt.append(np.nan)
        try:
            aolbfwhm.append(float(hdr['AOLBFWHM']))
        except:
            aolbfwhm.append(np.nan)
        try:
            lsamppwr.append(float(hdr['LSAMPPWR']))
        except:
            lsamppwr.append(np.nan)
        try:
            lgrmswf.append(float(hdr['LGRMSWF']))
        except:
            lgrmswf.append(np.nan)
            
    df['airmass'] = airmass
    df['itime'] = itime
    df['coadds'] = coadds
    df['band'] = band
    df['az'] = az
    df['dmgain'] = dmgain
    df['dtgain'] = dtgain
    df['wsfrrt'] = wsfrrt
    df['aolbfwhm'] = aolbfwhm
    df['lsamppwr'] = lsamppwr
    df['lgrmswf'] = lgrmswf
    df['xref'] = xref
    df['yref'] = yref
    df['xstrehl'] = xstrehl
    df['ystrehl'] = ystrehl


    # Add DIMM, MASS, MASSPRO

#     for mjd in df['mjd']:
    for mjd in mjd_list:
        yrmon = mjd.iso.replace('-', '')[:6]
        date = Time(mjd.value + 1, format = 'mjd')
        obs_date_1 = date.iso.replace('-', '')[:8]
        get_massdimm(str(mjd.iso.replace('-', '')[:8]))
        get_massdimm(str(obs_date_1))
        
    mass_dates = []
    mass_vals = []
    dimm_dates = []
    dimm_vals = []
    masspro_dates = []
    masspro_vals = []
    masspro_int = []
        
    seeing_directory = root_directory + 'seeing_data/'
    if os.path.isfile(seeing_directory + yrmon + '/' + obs_date_1 + '.mass.dat'):
        for file in glob.glob(seeing_directory + yrmon + '/*.mass.dat'):
            df_mass = pd.read_csv(file, delim_whitespace = True, header=None) 
            for i, row in df_mass.iterrows():
                dt = hst_to_mjd(row[:6])
                mass_dates.append(dt)
                mass_vals.append(df_mass[6][i])
                
        for file in glob.glob(seeing_directory + yrmon + '/*.dimm.dat'):
            df_dimm = pd.read_csv(file, delim_whitespace = True, header=None) 
            for i, row in df_dimm.iterrows():
                dt = hst_to_mjd(row[:6])
                dimm_dates.append(dt)
                dimm_vals.append(df_dimm[6][i])
                
        for file in glob.glob(seeing_directory + yrmon + '/*.masspro.dat'):
            df_masspro = pd.read_csv(file, delim_whitespace = True, header=None) 
            for i, row in df_masspro.iterrows():
                dt = hst_to_mjd(row[:6])
                masspro_dates.append(dt)
                temp = row[6:12]
                masspro_vals.append(temp)
                masspro_int.append(row[12])

        DIMM = []
        DIMM_mjd = []
        MASS = []
        MASS_mjd = []
        MASSPRO_half = []
        MASSPRO_1 = []
        MASSPRO_2 = []
        MASSPRO_4 = []
        MASSPRO_8 = []
        MASSPRO_16 = []
        MASSPRO = []
        MASSPRO_mjd = []
#         for mjd in df['mjd']:
        for mjd in mjd_list:
            i_mass, mjd_mass = find_nearest(np.array(mass_dates), mjd)
            i_dimm, mjd_dimm = find_nearest(np.array(dimm_dates), mjd)
            i_masspro, mjd_masspro = find_nearest(np.array(masspro_dates), mjd)
            MASS.append(mass_vals[i_mass])
            MASS_mjd.append(mjd_mass)
            MASSPRO_half.append(masspro_vals[i_masspro][6])
            MASSPRO_1.append(masspro_vals[i_masspro][7])
            MASSPRO_2.append(masspro_vals[i_masspro][8])
            MASSPRO_4.append(masspro_vals[i_masspro][9])
            MASSPRO_8.append(masspro_vals[i_masspro][10])
            MASSPRO_16.append(masspro_vals[i_masspro][11])
            MASSPRO.append(masspro_int[i_masspro])
            MASSPRO_mjd.append(mjd_masspro)
            DIMM.append(dimm_vals[i_dimm])
            DIMM_mjd.append(mjd_dimm)
        df['MASS'] = MASS
        df['MASS_mjd'] = MASS_mjd
        df['MASS_delta_t'] = np.subtract(df['mjd'], df['MASS_mjd'])
        df['DIMM'] = DIMM    
        df['DIMM_mjd'] = DIMM_mjd
        df['DIMM_delta_t'] = np.subtract(df['mjd'], df['DIMM_mjd'])
        df['MASSPRO_half'] = MASSPRO_half
        df['MASSPRO_1 '] = MASSPRO_1
        df['MASSPRO_2 '] = MASSPRO_2
        df['MASSPRO_4 '] = MASSPRO_4
        df['MASSPRO_8 '] = MASSPRO_8
        df['MASSPRO_16'] = MASSPRO_16
        df['MASSPRO'] = MASSPRO
        df['MASSPRO_mjd'] = MASSPRO_mjd
        df['MASSPRO_delta_t'] = np.subtract(df['mjd'], df['MASSPRO_mjd'])
    else:
        df['MASS'] = np.nan
        df['MASS_mjd'] = np.nan
        df['MASS_delta_t'] = np.nan
        df['DIMM'] = np.nan
        df['DIMM_mjd'] = np.nan
        df['DIMM_delta_t'] = np.nan
        df['MASSPRO_half'] = np.nan
        df['MASSPRO_1 '] = np.nan
        df['MASSPRO_2 '] = np.nan
        df['MASSPRO_4 '] = np.nan
        df['MASSPRO_8 '] = np.nan
        df['MASSPRO_16'] = np.nan
        df['MASSPRO'] = np.nan
        df['MASSPRO_mjd'] = np.nan
        df['MASSPRO_delta_t'] = np.nan
        
    
    # Add CFHT weather data
    
    year = '20' + datestring[0:2]
    yr_month = year + '_' + month_number(datestring[2:5])
    cfht_file = 'cfht_data/' + year + '/' + yr_month + '.dat'
    cfht_columns = 'year', 'month', 'day', 'hour', 'minute', 'wind_speed', 'wind_direction', 'temperature', 'relative_humidity', 'pressure'
    df_cfht = pd.read_csv(cfht_file, delim_whitespace = True, header=None)

    cfht_mjds =[]
    for i, row in df_cfht.iterrows():
        dt = hst_to_mjd(row[:5])
        cfht_mjds.append(dt)
    df_cfht.columns = cfht_columns
    df_cfht['mjd'] = cfht_mjds

    speed = []
    direction = []
    temp = []
    rel_hum = []
    pres = []
    cfht_mjd_list = []
#     for mjd in df['mjd']:
    for mjd in mjd_list:
        i_cfht, cfht_mjd = find_nearest(np.array(df_cfht['mjd']), mjd)
        speed.append(df_cfht['wind_speed'][i_cfht])
        direction.append(df_cfht['wind_direction'][i_cfht])
        temp.append(df_cfht['temperature'][i_cfht])
        rel_hum.append(df_cfht['relative_humidity'][i_cfht])
        pres.append(df_cfht['pressure'][i_cfht])
        cfht_mjd_list.append(cfht_mjd)

#     u.kts = u.def_unit('knots')
    df['wind_speed[kts]'] = speed #* u.kts
    df['wind_speed'] = (df['wind_speed[kts]'] * 0.514444444) * (u.m / u.s)
    df['wind_direction'] = direction #dec
    df['temperature'] = temp
    df['relative_humidity'] = rel_hum
#     u.mb = u.def_unit('millibar')
    df['pressure[mb]'] = pres # * u.mb
    df['pressure'] = (df['pressure[mb]'] / 1000) * u.bar
    df['cfht_mjd'] = cfht_mjd_list
    df['cfht_delta_t'] = np.subtract(df['mjd'], df['cfht_mjd'])

    return df


# Load in data, call the populate_datatable function to add new data

def update():
    '''
    Calling this function will backup the old file, automatically seek out new lgs data
    and append the existing datatable.
    '''
    unused_data = []
    used_data = []
    data_file = root_directory + 'lgs_metadata.fits'
    backup_directory = root_directory + 'backup/'
    if os.path.exists(backup_directory) == False:
        os.mkdir(backup_directory)
        vprint('Created backup directory')
    if os.path.isfile(data_file):
        master_table = Table.read(data_file, format = 'fits')
        now = datetime.now()
        backup_file = backup_directory + now.strftime("%Y%m%d") + '_lgs_metadata.fits'
        master_table.write(backup_file, format = 'fits')
        vprint('Old datatable backed up as ' + backup_file)

        Master_df = master_table.to_pandas()
        epochs = Master_df['epoch'].unique()
    else:
        Master_df = pd.DataFrame()
        epochs = []

    for file in os.listdir(root_directory + 'lgs_data/'):
        if file == '.ipynb_checkpoints':
            continue
        if len(file) < 10 and file not in epochs:
            Master_df = Master_df.append(populate_df(file))
            used_data.append(file)
        else:
            unused_data.append(file)

    new_table = Table.from_pandas(Master_df)
    
    new_table.write(data_file, format = 'fits')