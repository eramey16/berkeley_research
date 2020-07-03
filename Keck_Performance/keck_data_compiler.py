### keck_data_compiler.py
### Compiles important metadata for Keck II Performance Analysis and Prediction
### Pulls NIRC2, Telemetry, CFHT, and Weather data from the lab computers and from MKWC websites
### Author: Emily Ramey
### Date: 06/19/20

import pandas as pd
import numpy as np
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

MAX_LEN = 10 # Maximum length of a file
time_limit = 100 # Minutes between nirc2 and secondaries

root_dir = '/g/lu/data/gc/lgs_data/' # Main data directory
data_dir = '/u/emily_ramey/work/Keck_Performance/data/' # the directory I need to save things to because I don't have write access
seeing_dir = data_dir+'seeing_data/' # seeing directory
weather_dir = data_dir+'weather_data/' # weather directory
seeing_url = 'http://mkwc.ifa.hawaii.edu/current/seeing/'
weather_url = 'http://mkwc.ifa.hawaii.edu/archive/wx/cfht/'
verbose = True

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
strehl_cols = ['file', 'strehl', 'rms_err', 'fwhm', 'mjd']
nirc2_fields = ['AIRMASS', 'ITIME', 'COADDS', 'FWINAME', 'AZ', 'DMGAIN', 'DTGAIN', 'XREF', 'YREF', 
               'XSTREHL', 'YSTREHL', 'WSFRRT', 'AOLBFWHM', 'LSAMPPWR', 'LGRMSWF', 'AOAOAMED', 'TUBETEMP']
### Types of seeing files
s_types = ['mass', 'dimm', 'masspro']
### Seeing file headers
date_cols = ['year', 'month', 'day', 'hour', 'minute', 'second']
seeing_cols = {s_types[1]: ['dimm'],
               s_types[0]: ['mass'],
               s_types[2]: ['masspro_half', 'masspro_1', 'masspro_2', 'masspro_4', 'masspro_8',
                            'masspro_16', 'masspro']
              }
### Weather file headers
weather_cols = ['wind_speed', 'wind_direction',
                'temperature', 'relative_humidity', 'pressure']
n_weather_cols = 10
### Files that cannot be read in
bad_files_known = data_dir+"keck_bad_files.dat"
bad_files_list = []


### Read in invalid values
#pd.read_csv(bad_files)

### Time/date conversion functions:

def vprint(msg):
    """
    Prints a message to the console if in verbose mode.
    """
    if verbose:
        print(msg)


def month_atoi(month, asInt=True):
    """
    Converts a calendar month's name into an integer
    """
    if month in months:
        idx = months.index(month)+1
    else:
        print("Error: month string not found - "+month)
        return -1
    
    if asInt: return idx
    
    return "0"+str(idx) if idx<10 else str(idx)

def mjd_to_ds(mjd_list):
    """
    Converts a list of Modified Julian Dates to formatted date strings
    dateString = {year}{month}{day} e.g. 20060718
    """
    datetimes = Time(mjd_list, format='mjd').datetime
    dates = [dt.date() for dt in datetimes]
    fmt = lambda s: '0'+str(s) if s<10 else s # To format month and day
    dateStrings = [f"{d.year}{fmt(d.month)}{fmt(d.day)}" for d in dates]
    return dateStrings


def hst_to_utc(date):
    """
    Returns the Universal Coordinated Time calculated from Hawaii Standard Time
    """
    tz = pytz.timezone('US/Hawaii')
    return tz.normalize(tz.localize(date)).astimezone(pytz.utc)


def hst_to_mjd(daterow):
    """
    Returns the Modified Julian Time calculated from HST
    """
    row = [int(num) for num in daterow]
    if len(daterow) == 6:
        dt = datetime(row[0], row[1], row[2], row[3], row[4], row[5])
    else:
        dt = datetime(row[0], row[1], row[2], row[3], row[4])
    t = Time(hst_to_utc(dt))
    
    return t.mjd


### Program functions:

def nearest_mjd(mjd, data):
    """
    Returns the index of the mjd closest to the input in the 'mjd' column of a seeing array
    mjd: float - the date to match
    data: a dataframe containing available seeing or weather data, must have an 'mjd' column
    """
    ### Check for bad dates
    if data is None:
        return
    
    data_clean = data.dropna()
    
    ### Time limit
    dt = np.abs(data_clean.mjd-mjd)
    idx = dt.idxmin()
    if dt[idx]*24*60 > time_limit: # Compare in minutes
        return
    
    ### Return index of closest mjd
    return idx

def convert_to_mjd(dates):
    """
    Converts time data in a dataframe (HST) into MJD values
    df: a pandas dataframe, must contain the columns listed in the date_cols array
    Returns an astropy.Time object with a list of MJDs
    """
    ### Convert HST to MJD
    times = []
    # Input timezone
    hst = pytz.timezone('US/Hawaii')
    # Loop over times
    for i in range(len(dates)):
        year = int(dates.year[i])
        
        # For that one stupid typo in 2013
        if year == 202013:
            year = 2013
        
        dt = datetime(year, int(dates.month[i]), int(dates.day[i]),
                      int(dates.hour[i]), int(dates.minute[i]), int(dates.second[i]))
        dt = hst.normalize(hst.localize(dt)).astimezone(pytz.utc)
        times.append(dt)
    # Convert to astropy.Time
    times = Time(times)
    # Return array of mjds
    return times.mjd
            
            
def load_nirc2(nirc2_epoch):
    """
    Loads NIRC2 data from a given observing night as a pandas dataframe
    """
    nirc2_dir = f'{root_dir}{nirc2_epoch}/clean/kp/'
    vprint("Message: NIRC2 file found: "+nirc2_dir)
    
    ### Check for Strehl file
    if os.path.isfile(nirc2_dir + 'strehl_source.txt') == True: # Two possible filenames
        strehl_src = pd.read_csv(nirc2_dir + 'strehl_source.txt', delim_whitespace = True, header = None, skiprows = 1)
    elif os.path.isfile(nirc2_dir + 'irs33N.strehl') == True:
        strehl_src = pd.read_csv(nirc2_dir + 'irs33N.strehl', delim_whitespace = True, header = None, skiprows = 1)
    else: # Exit if not found
        vprint("Error: No Strehl file found for epoch "+nirc2_epoch+". Exiting.")
        return
    
    ### Correct column names
    strehl_src.columns = strehl_cols
    strehl_src['epoch'] = nirc2_epoch
    # Convert mjds to dateime objects
    mjd_list = Time(strehl_src['mjd'], format = 'mjd')
    
    ### Set up new dataframe
    nirc2_data = {field:[] for field in nirc2_fields}
    
    ### Loop through fits files
    for fname in strehl_src['file']:
        nirc2_file = nirc2_dir+fname
        with fits.open(nirc2_file) as file:
            nirc2_hdr = file[0].header
        for field in nirc2_fields:
            nirc2_data[field].append(nirc2_hdr.get(field, np.nan))
    
    ### Merge new data with old
    nirc2_data = pd.DataFrame.from_dict(nirc2_data)
    nirc2_data = strehl_src.join(nirc2_data)
    
    ### Return final dataframe
    return nirc2_data

def load_seeing(obs_date, s):
    """
    Loads seeing file of type s from a given observation date
    obs_date: string formated as YYMMDD
    s: Type of seeing file - mass, dimm, or masspro
    """
    ### TODO: Make a check for if MASS/DIMM was operational based on date
    
    ### Set destination seeing files
    date_file = seeing_dir + obs_date[:6] + '/'
    filename = date_file+obs_date+'.'+s+'.dat'
        
    ### Check if previous data exists
    if os.path.isfile(filename): # seeing files
        seeing = pd.read_csv(filename, memory_map=True)
        return seeing
        
    ### Otherwise, load the data from the MKWC website
    url = seeing_url + s + '/' + obs_date + '.' + s + '.dat'
    
    try:
        seeing = pd.read_csv(url, delim_whitespace = True, header=None)
    except:
        return
    
    vprint('\tMessage: Downloaded data from '+url)
    
    ### Format columns
    seeing.columns = date_cols+seeing_cols[s]
    
    ### Update and save file
    seeing['mjd'] = convert_to_mjd(seeing[date_cols])
    # Drop old date columns
    seeing = seeing.drop(columns=date_cols)
    # Make destination file
    if not os.path.exists(date_file):
        os.makedirs(date_file)
    # Save seeing data as csv
    seeing.to_csv(filename, index=False)
    
    # Return final seeing dataframe
    return seeing
    

def load_all_seeing(mjd_list):
    """
    Loads all seeing data from dates given in MJD format
    Returns: dictionary of dataframes as {mass: mass_df, dimm: dimm_df, masspro: masspro_df}
    """
    ### Format dates
    datestrings = mjd_to_ds(mjd_list)
    # Initialize seeing list
    all_seeing = {}
    
    warn_dates = []
    
    # Loop through dimm, mass, masspro
    for s in s_types:
        # Initialize dataframe
        seeing =  pd.DataFrame()
        
        # Loop through observation dates
        for obs_date in datestrings:
            data = load_seeing(obs_date, s)
            if data is not None:
                seeing = seeing.append(data, ignore_index=True)
            else:
                if obs_date not in warn_dates:
                    warn_dates.append(obs_date)
        
        # Save result in list
        all_seeing[s] = seeing if not seeing.empty else None
    
    if warn_dates != []:
        vprint(f'\tWarning: Could not retrieve seeing data for dates: {warn_dates}')
    else:
        vprint(f'\tMessage: Retrieved seeing data for all files')
    
    # Return seeing data as [mass, dimm, masspro]
    return all_seeing


def load_weather(obs_date):
    """
    Loads weather from a single observation date as a pandas dataframe
    """
    ### Set destination weather files
    yr = obs_date[:4]
    month = obs_date[4:6]
    day = obs_date[6:]
    filename = weather_dir + 'cfht-wx.' + obs_date + '.dat'
        
    ### Check if previous data exists
    if os.path.isfile(filename): # seeing files
        weather = pd.read_csv(filename, memory_map=True)
        return weather
    
    ### Download data from web, if not
    url = weather_url + 'cfht-wx.' + yr + '.dat'
    try:
        weather = pd.read_csv(url, delim_whitespace = True, header=None,
                             usecols=range(n_weather_cols))
    except:
        print(url)
        return
    vprint('\tMessage: Downloaded data from '+url)
    
    ### Format columns
    weather.columns = date_cols[:-1]+weather_cols # Missing seconds
    weather = weather[weather.month==int(month)]
    weather = weather[weather.day==int(day)].reset_index(drop=True) # only keep 1 day's data
    weather['second'] = 0 # add seconds
    weather['mjd'] = convert_to_mjd(weather[date_cols])
    
    ### Save to file
    weather = weather.drop(columns=date_cols)
    if not os.path.exists(weather_dir):
        os.makedirs(weather_dir)
    weather.to_csv(filename, index=False)
    
    ### Return dataframe
    return weather if not weather.empty else None
    


def load_all_weather(mjd_list):
    """
    Loads all weather data from cfht files with dates given in MJD format
    Returns: pandas dataframe with weather keywords
    """
    ### No data before 1996
    warn_dates = []
    # format dates
    datestrings = mjd_to_ds(mjd_list)
    # Initialize dataframe
    all_weather = pd.DataFrame()
    
    ### Loop through dates
    for obs_date in datestrings:
        data = load_weather(obs_date)
        
        if data is not None:
            all_weather = all_weather.append(data, ignore_index=True)
        else:
            if obs_date not in warn_dates:
                warn_dates.append(obs_date)
    
    if warn_dates != []:
        vprint(f'\tWarning: Could not retrieve weather data for dates: {warn_dates}')
    else:
        vprint(f'\tMessage: Retrieved weather data for all files')
    
    return all_weather if not all_weather.empty else None
    
            

def populate_df(nirc2_epoch):
    '''
    This takes in a nirc2 epoch (two digit year, first three letters of month,
    lgs, and a number if there were multiple days, ie. 04jullgs1), looks for and
    downloads all associated cfht and seeing data, and returns the df to be
    appended to a master table
    '''
    ### Load NIRC2 data from a file
    nirc2_data = load_nirc2(nirc2_epoch)
    if nirc2_data is None:
        vprint("Warning: Failed to populate dataframe for "+nirc2_epoch)
        return
    
    ### Load seeing data from Mauna Kea website
    # Find unique days in observation, +/- 1 day for padding
    unique_mjds = np.unique(np.floor(list(nirc2_data.mjd-1)+list(nirc2_data.mjd)+list(nirc2_data.mjd+1)))
    
    ### Pull seeing and weather data from relevant dates
    seeing_data = load_all_seeing(unique_mjds)
    weather_data = load_all_weather(unique_mjds)
    
    ### Match NIRC2 dates with seeing information
    # Initialize dictionary
    closest_data = {s+"_mjd":[] for s in s_types}
    closest_data.update({'cfht_mjd':[]})
    for s in s_types:
        closest_data.update({s_col:[] for s_col in seeing_cols[s]})
    closest_data.update({w_col:[] for w_col in weather_cols})
    
    # Loop through NIRC2 dates
    # Could probably make this shorter if time
    for nirc2_mjd in nirc2_data.mjd:
        # Find closest seeing data
        for s in s_types:
            seeing = seeing_data[s]
            # Find closest measurement to NIRC2 observation
            idx = nearest_mjd(nirc2_mjd, seeing)
            # Save closest measurements to dictionary
            closest_data[s+"_mjd"].append(np.nan if idx is None else seeing.iloc[idx]['mjd'])
            for s_col in seeing_cols[s]:
                closest_data[s_col].append(np.nan if idx is None else seeing.iloc[idx][s_col])
        # Find closest weather data
        idx = nearest_mjd(nirc2_mjd, weather_data)
        closest_data['cfht_mjd'].append(np.nan if idx is None else weather_data.iloc[idx]['mjd'])
        for w_col in weather_cols:
            closest_data[w_col].append(np.nan if idx is None else weather_data.iloc[idx][w_col])
    
    ### Add to NIRC2 data
    closest_data = pd.DataFrame.from_dict(closest_data)
    all_data = nirc2_data.join(closest_data)
    return all_data

def update():
    """
    Calling this function will backup the old file, automatically seek out new lgs data,
    and save an updated datatable
    """
    ### If file already exists
    data_file = data_dir + 'keck_metadata.dat'
    if os.path.isfile(data_file):
        # Read in previous file
        all_data = pd.read_csv(data_file)
        # Back up past file
        now = datetime.now()
        backup_file = data_dir + 'keck_metadata_backup_' + now.strftime("%Y%m%d") + '.dat'
        all_data.to_csv(backup_file, index=False)
        vprint('Previous data backed up as ' + backup_file)
        
        epochs = np.unique(all_data['epoch'])
    else: # Initialize new dataframe
        all_data = pd.DataFrame()
        epochs = []
    
    ### Add new files
    for file in os.listdir(root_dir):
        if len(file) >= MAX_LEN or file in epochs:
            continue
        else:
            data = populate_df(file)
            if data is None:
                continue
            all_data = all_data.append(data)
            
    ### Write dataframe to file
    all_data.to_csv(data_file, index=False)
    