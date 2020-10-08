### data_util.py: Code for generating and saving data tables
### Author: Emily Ramey
### Date: 09/04/2020

# Preamble
import pandas as pd
import numpy as np
import sys
import os

# Important folders
data_dir = "../../../Fall_2020_Paper/tables/"

# Default section and data type
section = "Observations"
data_type = "general"

default_headers = {
    'strehl': "Strehl Ratio",
    'fwhm': 'FWHM [mas]',
    'mass': 'MASS [as]',
    'dimm': 'DIMM [as]',
    "days": "Date (UT)",
}

def setup(sec, d_type):
    """ Sets the global section and data type variables """
    global section
    global data_type
    
    path = f"{data_dir}{section}/"
    if not os.path.exists(path):
        print("making path", path)
        os.mkdir(path)
    section = sec
    data_type = d_type

def save_table(data_string, filename):
    """ Save table to a file """
    path = f"{data_dir}{section}/{data_type}_{filename}"
    print("Saving file:", path)
    with open(path, 'w') as f:
        f.write(data_string)

def save_pandas(data, cols=None, just="c", sep="|", hlines=True, headers=default_headers, 
                filename=None, save=False):
    """ Saves columns from a pandas dataframe as a latex datatable """
    # Format column titles
    if cols is not None:
        data = data[cols]
    old_cols = data.columns
    col_titles = [(col.capitalize() if col not in headers else headers[col]) for col in data.columns]
    data.columns = col_titles
    
    ncols = len(data.columns)
    
    # Format column separators
    if type(sep) is str:
        sep = [sep]*(len(data.columns)+1)
    elif len(sep)!=len(data.columns)+1:
        print("Invalid column separators:", sep)
        return
    
    # Format column justification
    if type(just) is str:
        just = [just]*len(data.columns)
    elif len(just)!=len(data.columns):
        print("Invalid number of justification arguments:", len(just), "for", ncols, "columns.")
        return
    
    # Put together column format string
    col_format = sep[0]
    for i in range(ncols):
        col_format += just[i] + sep[i+1]
    
    data_string = data.to_latex(index=False, na_rep='None',
                                column_format=col_format)
    
    # Remove toprule, midrule, bottomrule
    rules = ["\n\\toprule", "\n\\midrule", "\n\\bottomrule"]
    
    for rule in rules:
        data_string = data_string.replace(rule, "")
    
    # Positions of top, mid, bottom rule
    for i in range(len(hlines)):
        if hlines[i]=='top': hlines[i] = 0
        if hlines[i]=='mid': hlines[i] = 1
        if hlines[i]=='bottom': hlines[i] = -3
    
    # Format hlines
    if type(hlines) is not bool: # Only certain hlines
        lines = data_string.split("\n")
        for lnum in hlines:
            lines[lnum] = lines[lnum].replace("\\\\", "\\\\\\hline")
        if 0 in hlines: # Top rule won't work automatically
            lines.insert(1, "\\hline")
        data_string = "\n".join(lines)
    
    elif hlines: # All hlines
        data_string = data_string.replace("\\\\", "\\\\\\hline")
    
    # Save file
    if save:
        if not filename:
            filename = "_".join(old_cols)+".tex"
        save_table(data_string, filename)
    return data_string