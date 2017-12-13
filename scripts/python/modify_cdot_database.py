#!/usr/bin/env python

# ============================================================================== #
#                                                                                #
#   (c) Copyright, 2013 University Corporation for Atmospheric Research (UCAR).  #
#       All rights reserved.                                                     #
#                                                                                #
#       File: $RCSfile: fileheader,v $                                           #
#       Version: $Revision: 1.1 $  Dated: $Date: 2013/09/30 14:44:18 $           #
#                                                                                #
# ============================================================================== #

"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
import Tutils
from datetime import datetime
from optparse import OptionParser
import log_msg
import pandas as pd
import numpy as np


def get_fcst_tt(row, mins, df):
    """
    """
    # Example using a dictionary
    #print time.strftime("%H:%M:%S")    

    key = (row["UNIX-TIME"]+mins, row["speed:SegmentId"])
    try:
        return df[key]
    except:
        # look for the one after
        after_key = (row["UNIX-TIME"]+mins+60, row["speed:SegmentId"])
        before_key = (row["UNIX-TIME"]+mins-60, row["speed:SegmentId"])
        if after_key in df and before_key in df:
            # If there are values at the time a min before and a min after, average
            if df[after_key] > 0 and df[before_key] > 0:
                return (df[after_key] + df[before_key]) / 2
            # if the time after is greater than 0, use it
            elif df[after_key] > 0:
                return df[after_key]
            # if the time before is greater than 0, use it
            elif df[before_key] > 0:
                return df[before_key]
            else:
                return ''
        # If only the key after is in the dataframe, use it
        elif after_key in df:
            return df[after_key]
        # If only the key before is in the dataframe, use it
        elif before_key in df:
            return df[before_key]        
        else:            
            return ''
    """
    ind = np.where((df["UNIX-TIME"] == (row["UNIX-TIME"] + (mins*60))) & (df["speed:SegmentId"] == row["speed:SegmentId"]))
    if len(ind[0]) > 0:
        return ind[0][0]
    else:
        return ''
    #if key in df:
    #else:
    #    return ''
    fcst_row = df.loc[(df["UNIX-TIME"] == (row["UNIX-TIME"] + (mins*60))) & (row["speed:SegmentId"] == df["speed:SegmentId"])]
    if len(fcst_row) > 0:
        return fcst_row["speed:TravelTimeInSeconds"].values[0]
    else:
        return ''
    """                        
def calculate_julian_day(row):
    dt = datetime(row['lclYear'], row['lclMonth'], row['lclDay'])
    return dt.timetuple().tm_yday

def calculate_DOY(row):
    dt = datetime(row['lclYear'], row['lclMonth'], row['lclDay'])
    return dt.weekday()

def add_fcst_travel_time_columns(in_file, out_file, logg):
    """
    """
    # In Seconds
    #fcst_times = [10, 20, 30, 40, 50, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720]
    #fcst_times =  [900]
    #fcst_times =  [900, 1800, 2700, 3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 43200, 46800,
    #               50400, 54000, 57600, 61200, 64800, 68400, 72000, 75600, 79200, 82800, 86400, 90000, 93600, 97200, 100800, 104400, 108000]
    fcst_times = [86400, 90000, 93600, 97200, 100800, 104400, 108000]
    #fcst_times = [10]
    
    df = pd.read_csv(in_file)
    logg.write_time("Creating lookup dictionary\n")    
    df_dict = df.set_index(["UNIX-TIME", "speed:SegmentId"])["speed:TravelTimeInSeconds"].to_dict()
    
    for ft in sorted(fcst_times):
        fcst_list = []
        column_name = "FcstTravelTime%sMin" % (ft / 60)
        logg.write_time("Calling apply\n")
        df[column_name] = df.apply(lambda row: get_fcst_tt(row, ft, df_dict), axis=1)        

    logg.write_time("Writing output\n")

    write_cols = ['UNIX-TIME', 'lclYear', 'lclMonth', 'lclDay', 'lclHour', 'lclMinute', 'solarZenith', 'solarAzimuth', 'speed:SegmentId', 'speed:SegmentName', 'speed:Direction', 'speed:SpeedLimit', 'speed:Length', 'speed:StartMileMarker', 'speed:EndMileMarker', 'speed:ExpectedTravelTime-speed:Minutes', 'speed:CalculatedDate', 'speed:AverageSpeed', 'speed:AverageOccupancy', 'speed:AverageVolume', 'speed:TravelTime-speed:Minutes', 'speed:TravelTimeInSeconds', 'alert:AlertId', 'alert:Type', 'alert:Impact', 'alert:ReportedTime', 'alert:LastUpdatedDate', 'alert:ExpectedEndTime', 'alert:Direction', 'alert:DirectionType', 'alert:IsBothDirectionFlg', 'rc:IsHazardousCondition', 'rc:RoadCondition_isNo Data', 'rc:RoadCondition_isError', 'rc:RoadCondition_isDry', 'rc:RoadCondition_isScattered Showers', 'rc:RoadCondition_isRain', 'rc:RoadCondition_isWet', 'rc:RoadCondition_isSlushy', 'rc:RoadCondition_isSlide', 'rc:RoadCondition_isHigh Wind', 'rc:RoadCondition_isPoor Visibility', 'rc:RoadCondition_isSnow', 'rc:RoadCondition_isSnow Packed', 'rc:RoadCondition_isSnow Packed Icy Spots', 'rc:RoadCondition_isIcy', 'rc:RoadCondition_isIcy Spots', 'rc:RoadCondition_isClosed', 'rc:RoadCondition_isBlowing Snow', 'rc:RoadCondition_isFog', 'rc:RoadConditionCategoryCd_is0', 'rc:RoadConditionCategoryCd_is1.0', 'rc:RoadConditionCategoryCd_is3.0', 'rc:RoadConditionCategoryCd_is4.0', 'rc:RoadConditionCategoryCd_is5.0', 'rc:RoadConditionCategoryCd_is6.0', 'rc:RoadConditionCategoryCd_is7.0', 'rc:RoadConditionCategoryCd_is8.0', 'rc:RoadConditionCategoryCd_is9.0', 'rc:RoadConditionCategoryCd_is10.0', 'rc:RoadConditionCategoryCd_is11.0', 'temperature-0', 'temperature-1', 'temperature-2', 'precipRate-0', 'precipRate-1', 'precipRate-2', 'precipAccum-0', 'precipAccum-1', 'precipAccum-2', 'visibility-0', 'visibility-1', 'visibility-2', 'roadTemperature1-0', 'roadTemperature1-1', 'roadTemperature1-2', 'roadTemperature2-0', 'roadTemperature2-1', 'roadTemperature2-2', 'lclDayOfWeek', 'medianTravelTimeSeconds', 'temp_mean', 'precipRate_mean', 'precipAccum_mean', 'roadTemp1_mean', 'roadTemp2_mean']
    #for ft in sorted(fcst_times):
        #write_cols.append("FcstTravelTime%sMin" % (ft / 60))
        
    #df.to_csv(out_file, columns = write_cols, index=False)
    df.to_csv(out_file, index=False)

def determine_speed_ratio(row):

    speed_ratio = "-9999"
    
    if(pd.isnull(row["speed:TravelTimeInSeconds"]) == False and
       pd.isnull(row["medianTravelTimeSeconds"]) == False):
        speed_ratio = row["speed:TravelTimeInSeconds"] / row["medianTravelTimeSeconds"]
    else:
        speed_ratio = "-9999"
    
    return speed_ratio
    
def add_median_travel_time_columns(in_file, out_file, logg):
    """
    Calculates the median travel time and creates a new database with it added on
        Median is based off of UTC time, categorized into day of week and time of day
        Num Medians = S(numSegs) * 7(daysOfWeek) * 24(hoursOfDay) * 30(2minute periods in an hour)
    """
    df = pd.read_csv(in_file)
    grouped_df = df.groupby(["speed:SegmentId", "lclHour", "lclMinute", "lclDayOfWeek"])["speed:TravelTimeInSeconds"].median()
    logg.write_time("made dict.  applying algorithm\n")
    df["medianTravelTimeSeconds"] = df.apply(lambda row: grouped_df[(row["speed:SegmentId"],
                                                                     row["lclHour"], row["lclMinute"],
                                                                     row["lclDayOfWeek"])], axis=1)
    df.to_csv(out_file, index=False)

    
def add_julian_day_column(in_file, out_file, logg):    
    """
    """
    df = pd.read_csv(in_file)

    df["lclJulianDay"] = df.apply(lambda row: calculate_julian_day(row), axis=1)
    df.to_csv(out_file, index=False)

def add_DOY_column(in_file, out_file, logg):
    """
    """
    df = pd.read_csv(in_file)

    df["lclDayOfWeek"] = df.apply(lambda row: calculate_DOY(row), axis=1)
    df.to_csv(out_file, index=False)

def add_mean_columns(in_file, out_file, logg):
    df = pd.read_csv(in_file)
    
    df["temp_mean"] = df[["temperature-0","temperature-1","temperature-2"]].mean(axis=1)
    df["precipRate_mean"] = df[["precipRate-0","precipRate-1","precipRate-2"]].mean(axis=1)
    df["precipAccum_mean"] = df[["precipAccum-0","precipAccum-1","precipAccum-2"]].mean(axis=1)
    df["roadTemp1_mean"] = df[["roadTemperature1-0","roadTemperature1-1","roadTemperature1-2"]].mean(axis=1)
    df["roadTemp2_mean"] = df[["roadTemperature2-0","roadTemperature2-1","roadTemperature2-2"]].mean(axis=1)

    df.to_csv(out_file, index=False)

def add_speed_ratio_column(in_file, out_file, logg):
    df = pd.read_csv(in_file)
    
    df["speed_ratio"] = df.apply(lambda row: determine_speed_ratio(row), axis=1) 
    
    df.to_csv(out_file, index=False)

def replace_missing(in_file, out_file, logg):
    df = pd.read_csv(in_file)
    df["speed:TravelTimeInSeconds"].replace(-1, np.nan, inplace=True)

    fcst_times =  [900, 1800, 2700, 3600, 7200, 10800, 14400, 18000, 21600, 25200, 28800, 32400, 36000, 39600, 43200, 46800,
                   50400, 54000, 57600, 61200, 64800, 68400, 72000, 75600, 79200, 82800, 86400, 90000, 93600, 97200, 100800, 104400, 108000]
    for ft in sorted(fcst_times):
        column_name = "FcstTravelTime%sMin" % (ft / 60)
        df[column_name].replace(-1, np.nan, inplace=True)
    df.to_csv(out_file, index=False)

def main():
    usage_str = "%prog in_file output_file"
    parser = OptionParser(usage = usage_str)
    parser.add_option("-l", "--log", dest="log", help="write log messages to specified file")
        
    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        parser.print_help()
        sys.exit(2)

    if options.log:
        logg = log_msg.LogMessage(options.log)
        logg.set_suffix(".asc")
    else:
        logg = log_msg.LogMessage("")
/d1/vii/data/historical/database/testing/20160420/rt_database.fcstTT.30Hours.20151001-20160229.asc
    in_file = args[0]
    out_file = args[1]

    logg.write_starting()
    #replace_missing(in_file, out_file, logg)
    #add_julian_day_column(in_file, out_file, logg)
    #add_DOY_column(in_file, out_file, logg)
    #add_fcst_travel_time_columns(in_file, out_file, logg)
    #add_speed_ratio_column(in_file, out_file, logg)
    add_median_travel_time_columns(in_file, out_file, logg)
    #add_mean_columns(in_file, out_file, logg)
    logg.write_ending()

if __name__ == "__main__":
    main()
