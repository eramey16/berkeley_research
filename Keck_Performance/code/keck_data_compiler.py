### keck_data_compiler.py
### Compiles important metadata for Keck II Performance Analysis and Prediction
### Pulls NIRC2, Telemetry, CFHT, and Weather data from the lab computers and from MKWC websites
### Author: Emily Ramey
### Date: 06/19/20

import pandas as pd
import numpy as np
import os
import re
import datetime
import pytz
import time
import glob
import urllib
import yaml
from astropy.table import Table
from astropy.time import Time, TimezoneInfo
from astropy import units as u, constants as c
from datetime import datetime, timezone
from astropy.io import fits
from scipy.io import readsav

MAX_LEN = 10 # Maximum length of a file
time_limit = 100 # Minutes between nirc2 and secondaries

root_dir = '/g/lu/data/gc/lgs_data/' # Main data directory
data_dir = '/u/emily_ramey/work/Keck_Performance/data/' # Data directory
save_dir = data_dir+"combined_data/"
seeing_dir = data_dir+'seeing_data/' # seeing directory
weather_dir = data_dir+'weather_data/' # weather directory
telem_dir = "/g/lu/data/keck_telemetry/"
seeing_url = 'http://mkwc.ifa.hawaii.edu/current/seeing/'
weather_url = 'http://mkwc.ifa.hawaii.edu/archive/wx/cfht/'
telem_filenum_match = "c(\d+).fits"

savefile = save_dir+'keck_metadata_all.dat'
logfile = save_dir+'keck_metadata_all.log'
bad_files = save_dir+"keck_bad_files.yaml"
logstring = ''

verbose = True

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
strehl_cols = ['file', 'strehl', 'rms_err', 'fwhm', 'mjd']
telem_cols = ['telem_file', 'telem_mjd', 'rms_mean', 'rms_std']
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

### Log/output
def vprint(msg):
    """
    Prints a message to the console if in verbose mode.
    """
    global logstring
    if verbose:
        print(msg)
    
    logstring+=msg+"\n"

### Time/date conversion functions:
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
    single = isinstance(mjd_list, float)
    if single:
        mjd_list = [mjd_list]
    
    datetimes = Time(mjd_list, format='mjd').datetime
    dates = [dt.date() for dt in datetimes]
    fmt = lambda s: '0'+str(s) if s<10 else s # To format month and day
    dateStrings = [f"{d.year}{fmt(d.month)}{fmt(d.day)}" for d in dates]
    return dateStrings if not single else dateStrings[0]

def hst_to_utc(date):
    """
    Returns the Universal Coordinated Time calculated from Hawaii Standard Time
    """
    tz = pytz.timezone('US/Hawaii')
    return tz.normalize(tz.localize(date)).astimezone(pytz.utc)


def hst_to_mjd(daterow):
    """
    Returns the Modified Julian Date calculated from HST
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
        vprint("\tError: No Strehl file found for epoch "+nirc2_epoch+". Exiting.")
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
    

def load_all_seeing(mjd_list, bad_data):
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
            savestring = s+"_"+obs_date
            
            if savestring in bad_data['seeing']:
                continue
            
            # Load seeing data
            data = load_seeing(obs_date, s)
            if data is not None:
                seeing = seeing.append(data, ignore_index=True)
            else:
                bad_data['seeing'].append(savestring)
                if obs_date not in warn_dates:
                    warn_dates.append(obs_date)
        
        # Save result in list
        all_seeing[s] = seeing if not seeing.empty else None
    
    if warn_dates==datestrings:
        vprint(f'\tWarning: Could not retrieve seeing')
    elif len(warn_dates) != 0:
        warn_dates = ", ".join(warn_dates)
        vprint(f'\tWarning: Could not retrieve seeing for dates: {warn_dates}')
    else:
        vprint(f'\tMessage: Retrieved seeing for all files')
    
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
    

def load_all_weather(mjd_list, bad_data):
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
        if obs_date in bad_data['weather']:
            continue
        data = load_weather(obs_date)
        
        if data is not None:
            all_weather = all_weather.append(data, ignore_index=True)
        else:
            bad_data['weather'].append(obs_date)
            if obs_date not in warn_dates:
                warn_dates.append(obs_date)
    
    if warn_dates==datestrings:
        vprint(f'\tWarning: Could not retrieve weather data')
    elif len(warn_dates) != 0:
        warn_dates = ", ".join(warn_dates)
        vprint(f'\tWarning: Could not retrieve weather data for dates: {warn_dates}')
    else:
        vprint(f'\tMessage: Retrieved weather data for all files')
    
    return all_weather if not all_weather.empty else None

def get_telem_mjd(telem):
    """ Extracts the Modified Julian Date from the given telemetry data """
    # Get MJD from telemetry
    if 'header' in telem.keys():
        mjd_idx = [i for i in range(len(telem.header)) if 'MJD-OBS' in telem.header[i].decode('utf-8')]
        if len(mjd_idx)!=1: # No MJD field in header or more than one
            print(f"Error in file {i} ({filenames[i]}) header: could not retrieve MJD")
        else: # Save MJD to dataframe
            mjd_idx = mjd_idx[0]
            mjd = float(re.findall("\d+\.\d+", telem.header[mjd_idx].decode('utf-8'))[0])
    elif 'tstamp_str_start' in telem.keys():
        timestring = telem.tstamp_str_start.decode('utf-8')
        fmt = "%Y-%m-%dT%H:%M:%S.%f"
        dt = datetime.strptime(timestring, fmt)
        t = Time(dt, format='datetime', scale='utc')
        mjd = t.mjd
    else:
        print(f"File {i} ({filenames[i]}) has no header")
        return
    
    return mjd

### Load telemetry for one NIRC2 file
def load_telem(datestring, filenum, nirc2_mjd):
    """ Loads and aggregates telemetry info from one file """
    acceptable_dt = .0001 # precision of mjd match (~10 seconds or so)
    
    # Telemetry file will match:
    telem_pattern = f"/g/lu/data/keck_telemetry/{datestring}*/**/n?{filenum}_*.sav"
    
    # Get all matching files
    telem_files = glob.glob(telem_pattern, recursive=True)
    if len(telem_files) == 0: # No matches
        return
    
    for telem_file in telem_files:
        # Read telemetry file
        telem = readsav(telem_file)
        
        # Get mjd
        telem_mjd = get_telem_mjd(telem)
        
        if np.abs(telem_mjd-nirc2_mjd) < acceptable_dt:
            # Get mean and std of rms residuals
            rms_mean = np.mean(telem.a.residualrms[0][0])
            rms_std = np.std(telem.a.residualrms[0][0])
            return telem_file, telem_mjd, rms_mean, rms_std
            
        del telem
    
    return None
    

### Load all telemetry for one epoch
def load_all_telem(files, mjds, bad_data):
    """ Loads all telemetry info for files in nirc2_data """
    N = len(files)
    data = pd.DataFrame(index=range(N), columns=telem_cols)
    
    warn_files = []
    for i in range(len(files)):
        file, mjd = files[i], mjds[i]
        datestring = mjd_to_ds(mjd)
        savestring = datestring+"_"+file
        
        # Skip bad data
        if savestring in bad_data['telemetry']:
            continue
        
        # Get file number
        filenum = re.search(telem_filenum_match, file)
        filenum = filenum[1:]
        if not filenum:
            bad_data['telemetry'].append(savestring)
            vprint(f"\tWarning: Couldn't find file number in {datestring}, {file}")
            warn_files.append(file)
            continue
        
        filenum = filenum[1]
        
        # Load telemetry for file pattern
        results = load_telem(datestring, filenum, mjd)
        if results is None:
            bad_data['telemetry'].append(savestring)
            vprint(f"\tWarning: No time matches for {datestring}, {file}")
            warn_files.append(file)
        data.loc[i] = results
    
    # Warn about bad data
    nans = data.isna().any(axis=1)
    if not any(nans): # No rows have nans
        vprint(f'\tMessage: Retrieved telemetry for all files')
        return data
    elif all(nans): # All rows have nans
        vprint(f"\tWarning: Could not retrieve telemetry")
    elif len(warn_files)!=0:
        vprint(f"\tWarning: Could not retrieve telemetry for files {', '.join(warn_files)}")
    
    return data

def populate_df(nirc2_epoch, bad_data):
    '''
    This takes in a nirc2 epoch (two digit year, first three letters of month,
    lgs, and a number if there were multiple days, ie. 04jullgs1), looks for and
    downloads all associated cfht and seeing data, and returns the df to be
    appended to a master table
    '''
    ### Load NIRC2 data from a file
    nirc2_data = load_nirc2(nirc2_epoch)
    if nirc2_data is None:
        vprint("\tWarning: Failed to populate dataframe for "+nirc2_epoch)
        return
    
    ### Load telemetry data from servers
    telem_data = load_all_telem(nirc2_data.file, nirc2_data.mjd, bad_data)
    nirc2_data = nirc2_data.join(telem_data)
    
    ### Load seeing data from Mauna Kea website
    # Find unique days in observation, +/- 1 day for padding
    unique_mjds = np.unique(np.floor(list(nirc2_data.mjd-1)+list(nirc2_data.mjd)+list(nirc2_data.mjd+1)))
    
    ### Pull seeing and weather data from relevant dates
    seeing_data = load_all_seeing(unique_mjds, bad_data)
    weather_data = load_all_weather(unique_mjds, bad_data)
    
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

def update(savefile=savefile, logfile=logfile, bad_files=bad_files):
    """
    Calling this function will backup the old file, automatically seek out new lgs data,
    and save an updated datatable
    """
    ### Set up bad files
    if os.path.isfile(bad_files):
        with open(bad_files) as f:
            bad_data = yaml.load(f, Loader=yaml.FullLoader)
    else: bad_data = {'nirc2': [], 'weather': [], 'seeing': [], 'telemetry': []}
    
    ### If file already exists
    if os.path.isfile(savefile):
        # Read in previous file
        all_data = pd.read_csv(savefile)
        
        # Get backup filename
        now = datetime.now()
        filename = os.path.basename(savefile)
        filestub, ext = filename.split('.')[-2:]
        
        # Back up past file
        backup_file = f"{data_dir}{filestub}_backup_{now.strftime('%Y%m%d')}.{ext}"
        all_data.to_csv(backup_file, index=False)
        vprint('Previous data backed up as ' + backup_file)
        
        epochs = np.unique(all_data['epochs'])
    
    else: # Initialize new dataframe
        all_data = pd.DataFrame()
        epochs = []
    
    with open(logfile, 'w') as _:
            pass # Clear the file
    
    global logstring
    ### Add new files
    for file in os.listdir(root_dir):
        if file in bad_data['nirc2'] or file in epochs:
            continue
        elif len(file) >= MAX_LEN:
            bad_data['nirc2'].append(file)
            vprint(f"Message: Skipping invalid file: {file}")
            continue
        else:
            data = populate_df(file, bad_data)
            if data is None:
                bad_data['nirc2'].append(file)
                continue
            all_data = all_data.append(data)
        ### Write log
        with open(logfile, 'a') as log:
            log.write(logstring)
            logstring = ''
    
    print(bad_data)
            
    ### Write dataframe to file
    all_data.to_csv(savefile, index=False)
    
    print(f"data saved to {savefile}")
    
    with open(bad_files, 'w') as file:
        yaml.dump(bad_data, file)
    