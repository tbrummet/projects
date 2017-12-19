#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import pandas as pd
import numpy as np

from bokeh.plotting import figure, show, output_file, save

TOOLS = "pan,wheel_zoom,box_zoom,reset,save,box_select,undo,redo,crosshair"
MISSING = -9999
FIELD = "Point_spread_MGM"

color_map = {'Philadelphia' : 'blue',
             'Phoenix' : 'yellow',
             'Brooklyn' : 'black',
             'Charlotte' : 'teal',
             'Indiana' : 'gold'
}

def read_csv_files(in_dir, file_base_name):
    """
    Reads all csv files from the given directory (expects dated subdirs) and 
      organizes the data into a dataframe which is returned
    """
    df = pd.DataFrame()
    
    # Get the dated subdirs
    dated_subdirs = os.listdir(in_dir)
    num_files = 0
    for dt in dated_subdirs:
        dir_path = "%s\%s" % (in_dir, dt)
        file_listing = os.listdir(dir_path)
        for f in file_listing:
            # Skip files that don't have this base name
            if f.find(file_base_name) == -1:
                continue
            file_path = "%s\%s" % (dir_path, f)
            file_df = pd.read_csv(file_path)
            df = pd.concat([df, file_df])
            num_files += 1

    df.reset_index(inplace=True)
    print ("Read %d files" % num_files)
    return df

def depricate_values(x_values, y_values):
    """
    """
    # Make it so that the x axis starts at 0 by subtracting the first value from them all
    x_values = x_values-x_values.iloc[0]

    # Make it so that the final line is 0
    y_values = y_values-y_values.iloc[-1]

    return (x_values, y_values)

def plot_data(game_df, p1):
    """
    """
    # First sort the dataframe on the time
    sorted_df = game_df.sort_values(['Time'])

    # remove all rows where the value we need is missing
    sorted_df = sorted_df[sorted_df[FIELD] != -9999]
    #sorted_df['FIELD'].replace([-9999], [np.nan], inplace=True)

    #x_values = pd.to_datetime(sorted_df['Time'], unit='s')
    x_values = sorted_df['Time'][:]
    y_values = sorted_df[FIELD][:]
    if (len(x_values) == 0) or (len(y_values) == 0):
        return

    #print (x_values, y_values)    
    (x_values, y_values) = depricate_values(x_values, y_values)
    #print (x_values, y_values)

    if game_df['Home_Team'].iloc[0] in color_map:
        col = color_map[game_df['Home_Team'].iloc[0]]
    else:
        col = 'black'
    p1.line(x_values, y_values, legend=FIELD, color=col)
    

def process(in_dir, file_base_name):
    """
    """

    data_df = read_csv_files(in_dir, file_base_name)

    
    # Try to get the list of over/under lines for a single game
    # A single game is a home_team/date match
    home_team = data_df["Home_Team"][0]
    game_time = data_df["Game_Time"][0]

    # Get all bets for this specific game
    game_df = data_df[((data_df["Home_Team"]==home_team) &
                       (data_df["Game_Time"]==game_time))]


    # Set up the plot figure
    p1 = figure(plot_width=1000, x_axis_type="datetime", tools=TOOLS)

    # Get a list of all game/time pairs
    data_df['Team-Game'] = data_df.apply(lambda row: '%s|%s' % (row['Home_Team'],
                                                           row['Game_Time']), axis=1)
    all_games = data_df['Team-Game'].unique().tolist()

    print ("Plotting %d games" % len(all_games))
    for game in all_games:
        (ht, gt) = game.split("|")
        #print (ht, gt)
        game_df = data_df[((data_df["Home_Team"]==ht) & (data_df["Game_Time"]==gt))]
        plot_data(game_df, p1)
    
    show(p1)        
    

    
def main():
    usage_str = "%prog in_dir file_base_name"
    usage_str = "%s\n\tin_dir : directory containing dated subdirs containing csv files" % usage_str
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        parser.print_help()
        sys.exit(2)

                                  
    in_dir = args[0]
    file_base_name = args[1]

    if not os.path.exists(in_dir):
        print ("Error: %s doesn't exist." % in_dir)
        sys.exit()

    process(in_dir, file_base_name)


if __name__ == "__main__":
    main()
