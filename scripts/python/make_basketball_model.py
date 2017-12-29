#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import pandas as pd
import Tutils
import numpy as np

def get_epoch_dt(row):
    game_date_str = row['Date']
    game_time_str = row['Start (ET)']

    full_str = "%s %s" % (game_date_str, game_time_str)
    return Tutils.tme2epoch(full_str, "%a %b %d %Y %I:%M %p")

def read_input_dir(in_dir):
    """
    """
    dir_df = pd.DataFrame()
    file_listing = os.listdir(in_dir)
    for f in file_listing:
        file_path = "%s\%s" % (in_dir, f)
        print ("Reading: %s\n" % file_path)
        df = pd.read_csv(file_path)
        dir_df = pd.concat([dir_df, df])

    return dir_df
        
def create_base_df(sorted_game_df):
    # Iterate through the dataframe and make the data that I need
    #    Try 1:
    #       GameTime,Team,PointsScored
    game_time_list = []
    game_time_str_list = []
    teams_list = []
    points_list = []
    for ind, row in sorted_game_df.iterrows():
        # For each row, need to make 2 rows, one for home and 1 for away team
        game_time_list.append(row["EpochDt"])
        game_time_list.append(row["EpochDt"])
        game_time_str_list.append(row["Date"])
        game_time_str_list.append(row["Date"])        
        teams_list.append(row["Visitor/Neutral"])
        teams_list.append(row["Home/Neutral"])
        points_list.append(row["VisitorPTS"])
        points_list.append(row["HomePTS"])

    master_df = pd.DataFrame(columns=["GameTime","GameTimeStr","Team","PointsScored"])
    master_df["GameTime"] = game_time_list
    master_df["GameTimeStr"] = game_time_str_list
    master_df["Team"] = teams_list
    master_df["PointsScored"] = points_list
    return master_df

def get_prior_score(row, base_df, lookback_games):
    # Get prior games for this team
    team_df = base_df[((base_df["Team"] == row["Team"]) &
                       (base_df["GameTime"] < row["GameTime"]))].sort_values("GameTime").reset_index()
    if len(team_df) == 0:
        return np.nan
    elif len(team_df) < lookback_games:
        return np.nan
    else:
        # Return the most recent value
        last_ind = len(team_df) - lookback_games
        return team_df.loc[last_ind]["PointsScored"]

def get_prior_rest(row, base_df, last_game_ind, game_ind):
    """
    """
    # Get prior games for this team
    team_df = base_df[((base_df["Team"] == row["Team"]) &
                       (base_df["GameTime"] < row["GameTime"]))].sort_values("GameTime").reset_index()
    if len(team_df) == 0:
        return np.nan
    elif len(team_df) < last_game_ind:
        return np.nan
    else:
        # Get the indices of the games to calculate diffs
        df_last_game_ind = len(team_df) - last_game_ind
        if game_ind == 0:
            game_time = row["GameTime"]
        else:
            df_game_ind = len(team_df) - game_ind            
            game_time = team_df.loc[df_game_ind]["GameTime"]
        # Calculate the differences between the games at the given inds        
        return (round((game_time - team_df.loc[df_last_game_ind]["GameTime"])/86400))
    
def process(in_dir, out_file_base):
    """
    """
    # Read all of the files in 'in_dir'
    game_df = read_input_dir(in_dir)
    game_df['EpochDt'] = game_df.apply(lambda row: get_epoch_dt(row), axis=1)
    sorted_game_df = game_df.sort_values('EpochDt')

    base_df = create_base_df(sorted_game_df)

    # Add columns that I think will be helpful
    #   Prior 3 games and rest inbetween each one
    base_df["Prior_1_game_score"] = base_df.apply(lambda row: get_prior_score(row, base_df, 1), axis=1)
    base_df["Prior_2_game_score"] = base_df.apply(lambda row: get_prior_score(row, base_df, 2), axis=1)
    base_df["Prior_3_game_score"] = base_df.apply(lambda row: get_prior_score(row, base_df, 3), axis=1)    
    base_df["Rest_before_prior_3_game"] = base_df.apply(lambda row: get_prior_rest(row, base_df, 4, 3), axis=1)
    base_df["Rest_before_prior_2_game"] = base_df.apply(lambda row: get_prior_rest(row, base_df, 3, 2), axis=1)
    base_df["Rest_before_prior_1_game"] = base_df.apply(lambda row: get_prior_rest(row, base_df, 2, 1), axis=1)
    base_df["Rest_before_game"] = base_df.apply(lambda row: get_prior_rest(row, base_df, 1, 0), axis=1)        

    out_data_file = "%s_data.asc" % out_file_base
    print ("Writing: %s" % out_data_file)
    base_df.to_csv(out_data_file, index=False)
    

def main():
    usage_str = "%prog in_dir output_file_base"
    usage_str = "%s\n Will produce an output data and model file" % usage_str
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        parser.print_help()
        sys.exit(2)

                                  
    in_dir = args[0]
    out_file_base = args[1]

    process(in_dir, out_file_base)


if __name__ == "__main__":
    main()
