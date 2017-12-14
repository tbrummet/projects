#!/usr/bin/python
# Filename: Tutils.py
#  Some useful functions, put together by Tom Brummet

# ============================================================================== #
#                                                                                #
#   (c) Copyright, 2013 University Corporation for Atmospheric Research (UCAR).  #
#       All rights reserved.                                                     #
#                                                                                #
#       File: $RCSfile: fileheader,v $Tutils.py                                  #
#       Version: $Revision: 1.0 $  Dated: $Date: 2013/10/10 14:44:18 $           #
#                                                                                #
# ============================================================================== #

from datetime import datetime
import sys
import os
import time
import calendar

def mod_date(date, offSet):
    """
    Parameters
    ----------
    date : str
        String corresponding to date (YYYYmmDDHH)
    offSet : int
        integer corresponding to time offSet (in hours)

    Returns
    -------
    new_date : str
        String corresponding to last date (YYYYmmDDHH - offSet)
    """
    (year, mon, day, hr) = (date[0:4], date[4:6], date[6:8], date[8:10])
    try:
        tm = datetime(int(year), int(mon), int(day), int(hr),0,0)
    except:
        sys.exit()
    TTUP = tm.timetuple()
    unixT = calendar.timegm(TTUP)
    prevT = unixT+(3600*offSet)
    new_date = time.strftime("%Y%m%d%H", time.gmtime(prevT))
    return new_date


def get_most_recent_file(in_dir, logg):
    """
    Parameters
    ----------
    in_dir : string
        a directory to get the most recent file from
    logg : log_base
        Log base for writing output
    
    Returns
    --------
    curr_file : string
        A path to the file in 'in_dir' whose name matches curr_date
    """
    listing = sorted(os.listdir(in_dir))
    date = ''
    for f in listing:
        # Only look for date dirs, skip files that aren't all digits
        if not f.isdigit():
            continue
        # if date hasn't been set, set it
        if date == '':
            date = f
            continue
        # Set date_dir to largest (most recent) date in file
        elif float(f) > float(date):
            date = f
            date_dir = "%s/%s" % (in_dir, date)

    curr_file = sorted(os.listdir(date_dir))[-1]
    return curr_file


def tme2epoch(time_str, frmt_str):
    """
    Parameters
    ----------
    time_str : string
        a time string which matches the frmt_str
    frmt_str : string
        a format string which matches the time (ie. %Y-%m-%d %H:%M%S)

    Returns
    -------
        an integer corresponding to the epoch time
    """
    ts = time.strptime(time_str, frmt_str)
    return calendar.timegm(ts)

def epoch2tme(epoch, frmt_str):
    """
    Parameters
    ----------
    epoch : string
        an integer corresponding to an epoch time
    frmt_str : string
        the output time format that you want

    Returns
    -------
       a string corresponding to the epoch time
    """
    return time.strftime(frmt_str, time.gmtime(epoch))

def gen_epoch_time_range(start_epoch, end_epoch, increment):
    """
    Parameters
    ----------
    start_epoch : int
        int corresponding to beginning date
    end_epoch : int
        int corresponding to ending date
    increment : int
        int to increment time by
    """
    time_list = []
    epoch_itr = start_epoch
    while (epoch_itr <= end_epoch):
        time_list.append(epoch_itr)
        epoch_itr = epoch_itr + increment
    return time_list
                                    
def gen_time_range(start_time, end_time, frmt_str, increment):
    """
    Parameters
    ----------
    start_epoch : str
        str corresponding to beginning date
    end_epoch : str
        str corresponding to ending date
    frmt_str : str
        str corresponding to format of input AND output times
    increment : int
        int to increment time by in seconds
    """
    start_epoch = tme2epoch(start_time, frmt_str)
    end_epoch = tme2epoch(end_time, frmt_str)
    epoch_itr = start_epoch
    time_list = []
    while (epoch_itr <= end_epoch):
        time_list.append(epoch2tme(epoch_itr, frmt_str))
        epoch_itr += increment
    return time_list
    

def read_csv_file(file_str, split_str):
    """
    Parameters
    ----------
    file_str : string
          a string corresponding to the full path of a csv file to read
    split_str : string
          a string to split the lines by

    Returns
    ------
    data : list of lists
        a list of lists (1 per line) separated by 'split_str'
    """
    inF = open(file_str, "r")
    data = []
    for line in inF:
        fields = line.split(split_str)
        data.append(line.strip("\r\n").split(split_str))
    inF.close()
    return data



def read_siteList_file(site_list):
    """
    Parameters
    ----------
    site_list : str
        str to path of site list file
        
    Returns
    -------
    sites : list
        list of dicast id's (strs)
    """
    inF = open(site_list, 'r')
    sites = []
    for line in inF:
        fields = line.strip("\r\n").split(';')
        sites.append(fields)
    inF.close()
    return sites

def reformat_time_stamp(in_time, in_format, out_format):
    """
    Parameters
    ---------
    in_time : str
        str that matches in_format
    in_format : str
        str for format of in_time
    out_format : str
        format for output time

    Returns
    -------
    out_time : str
        str of time that matches out_format
    """
    in_tme_epoch = tme2epoch(in_time, in_format)
    out_tme_str = epoch2tme(in_tme_epoch, out_format)
    return out_tme_str
# End of Tutils.py
