#!/usr/bin/env python

"""Group data for a site by lane. Next find hourly sequences  """

# ============================================================================== #
#                                                                                #
#   (c) Copyright, 2017 University Corporation for Atmospheric Research (UCAR).  #
#       All rights reserved.                                                     #
#                                                                                #
#       File: $RCSfile: fileheader,v $                                           #
#       Version: $Revision: 1.1 $  Dated: $Date: 2010/10/04 14:44:18 $           #
#                                                                                #
# ============================================================================== #

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
import seaborn.apionly as sns

import itertools

import pandas as pd
import os
import sys
from optparse import OptionParser
import time
import log_msg

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,box_select,undo,redo,crosshair"
#COLORS = ["blue", "green", "red", "black", "orange"]
# define the color palette
ncolors = 5
palette = sns.palettes.color_palette('bright', ncolors)
# as hex is necessary for bokeh to render the colors properly.
COLORS = itertools.cycle(palette.as_hex())


def process(x_field_name, y_field_names, in_file, out_file, options, logg):
    """ Group by lane number 
    Parameters
    ----------
    x_field_name : string
        string that should match something in the header
    y_field_names : list[strings]
        list of string that should match something in the header
    in_file : string
        Input file
    out_file : string
        Output file

    Returns
    -------
    0 on success, -1 on failure
    """

    df = pd.read_csv(in_file, encoding = "ISO-8859-1", index_col=False)
    
    if x_field_name not in df:
        logg.write("Error: %s doesn't exist in %s\n" % (x_field_name, in_file))
        return -1

    plot_title = ""
    if options.title:
        plot_title=options.title
    
    # Sort the df based on the x field
    #   Currently, can't sort on date because it is in a strange format, assuming csv file is alread sorted
    sorted_df = df.sort_values([x_field_name])
    #sorted_df = df

    # Get all of the x values
    x_values = []
    # If the x values are dates, convert them to datetimes
    if options.x_date:
        #x_values = pd.to_datetime(sorted_df[x_field_name], infer_datetime_format=True)
        x_values = pd.to_datetime(sorted_df[x_field_name], format="%d/%m/%Y %H:%M:%S")        
        p1 = figure(plot_width=1000, x_axis_type="datetime", title=plot_title, tools=TOOLS)
    else:
        x_values = sorted_df[x_field_name]
        p1 = figure(plot_width=1000, title=plot_title, tools=TOOLS)        

    count = 0
    # Loop through all y fields, and add lines for them        
    #for y_field in y_field_names:
    for x, colr in zip(range(len(y_field_names)), COLORS):
        y_field = y_field_names[x]
        if y_field not in df:
            logg.write("Error: %s doesn't exist in %s\n" % (y_field, in_file))
            continue
        y_values = sorted_df[y_field]

        p1.line(x_values, y_values, legend = y_field, color=colr)

        count+=1
        
    output_file(out_file, title=plot_title)
    show(p1)
    return 0

def main():

    usage_str = "%prog x_field_name y_field_name(s) in_file out_file"
    usage_str = "%s\n x_field_name : Column (from header) that you want to plot on the x axis" % usage_str
    usage_str = "%s\n y_field_name(s) : Column (from header) (comma separated if multiple) that you want to plot on the y axis" % usage_str
    usage_str = "%s\n in_file : input file name" % usage_str
    usage_str = "%s\n out_file : output html file name" % usage_str            
    parser = OptionParser(usage = usage_str)
    parser.add_option("-l", "--log", dest="log", help="write log messages to specified file")
    parser.add_option("-d", "--x_field_is_date", dest="x_date", action="store_true", help="pass if the x_field is a date")
    parser.add_option("-t", "--title", dest="title", help="Use this as the plot title")
    
    (options, args) = parser.parse_args()

    if len(args) < 4:
        parser.print_help()
        sys.exit(2)
        
    if options.log:
        logg = log_msg.LogMessage(options.log)
        logg.set_suffix(".asc")
    else:
        logg = log_msg.LogMessage("")
        
    x_field_name = args[0]
    y_field_names = args[1].split(',')
    in_file = args[2]
    out_file = args[3]

    if not os.path.exists(in_file):
        logg.write("Error: %s doesn't exist" % in_file)
        sys.exit()
        
    process(x_field_name, y_field_names, in_file, out_file, options, logg)


if __name__ == "__main__":

   main()
