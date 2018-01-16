#!/usr/bin/python
# Filename: NBA_utils.py
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
import pandas as pd
import numpy as np
import Tutils

HOME_TEAM = 'HomeTeam'
HOME_TEAM_PTS = 'HomePoints'
AWAY_TEAM = 'AwayTeam'
AWAY_TEAM_PTS = 'AwayPoints'

NCAA_NAME_MAP = {
    "UC Santa Barb." :  "UC Santa Barbara",
    "Army West Point" :  "Army",
    "Saint Joseph's" :  "St. Josephs (PA)",
    "NC State" :  "North Carolina State",
    "Ohio St." :  "Ohio State",
    "USC" :  "Southern Cal",
    "Monmouth" :  "Monmouth (NJ)",
    "St. Peter's" :  "St. Peters",
    "Sacramento St." :  "CS Sacramento",
    "Montana St." :  "Montana State",
    "CSUN" :  "CS Northridge",
    "Long Beach St." :  "CS Long Beach",
    "CSU Fullerton" :  "CS Fullerton",
    "CSU Bakersfield" :  "CS Bakersfield",    
    "FIU" :  "Florida Intl",
    "Saint Joseph's" :  "St. Josephs (PA)",
    "LSU" : "Louisiana State",
    "UNI" : "Northern Iowa",
    "UNC-Greensboro" : "UNC Greensboro",
    "Eastern Wash." : "Eastern Washington",
    "St. Mary's (Cal.)" : "St. Marys (CA)"
    }

def read_OP_bball_dir(in_dir):
    """
    Reads the OP_basketball_game dir into a pandas dataframe
    """
    df = pd.DataFrame()
    
    # Get the dated subdirs
    num_files = 0
    files = os.listdir(in_dir)
    for f in files:
        file_path = "%s\%s" % (in_dir, f)
        file_df = pd.read_csv(file_path)
        df = pd.concat([df, file_df])
        num_files += 1

    df.drop_duplicates(inplace=True)        
    df.reset_index(inplace=True)
    print ("Read %d files" % num_files)
    return df

def read_odds_dir(odds_dir, file_base):
    """
    Returns a pandas dataframe
    """
    odds_df = pd.DataFrame()
    date_listing = os.listdir(odds_dir)
    num_files = 0
    for dt in date_listing:
        date_path = "%s\%s" % (odds_dir, dt)
        file_listing = os.listdir(date_path)        
        for f in file_listing:
            if not f.startswith(file_base):
                continue
            #print ("Reading: %s" % f)
            file_path = "%s\%s" % (date_path, f)
            df = pd.read_csv(file_path)
            odds_df = pd.concat([odds_df, df])
            num_files += 1
    print ("Read %d files" % num_files)
    return odds_df

def remap_team_name(team_name):
    team = ''
    if team_name.find("Los Angeles Lakers") != -1:
        team = "L.A. Lakers"
    elif team_name.find("Los Angeles Clippers") != -1:
        team = "L.A. Clippers"
    elif team_name.find("Portland Trail Blazers") != -1:
        team = "Portland"
    else:            
        team = ' '.join(team_name.split()[:-1])
    return team

def remap_NCAA_team_name(team_name):
    """
    """
    if team_name in NCAA_NAME_MAP:
        return NCAA_NAME_MAP[team_name]
    else:
        return team_name

def add_odds(game_df, odds_df, league):
    """
    """
    predicted_spread_list = []
    predicted_over_under_list = []
    for ind, row in game_df.iterrows():
        if league=='NBA':
            home_team = remap_team_name(row[HOME_TEAM])
            away_team = remap_team_name(row[AWAY_TEAM])
        else:
            home_team = remap_NCAA_team_name(row[HOME_TEAM])
            away_team = remap_NCAA_team_name(row[AWAY_TEAM])

        game_day = row['EpochDt']

        game_odds = find_odds(odds_df, game_day, home_team, away_team)
        
        if (len(game_odds) > 0):
            # Retrieve the last odds that were recorded for this game
            predicted_points = game_odds['Over_under_Open'].tolist()[-1]
            predicted_spread = game_odds['Point_spread_Open'].tolist()[-1]      

            predicted_spread_list.append(predicted_spread)
            predicted_over_under_list.append(predicted_points)
        else:
            predicted_spread_list.append(np.nan)
            predicted_over_under_list.append(np.nan)

    game_df['predicted_over_under'] = predicted_over_under_list
    game_df['predicted_spread'] = predicted_spread_list
    
    return
        
def find_odds(odds_df, game_date, home_team, away_team):
    #print ("Looking for game")
    #print (game_date, home_team, away_team)
    this_game_df = odds_df[((odds_df['Home_Team']==home_team) &
                            (odds_df['Away_Team']==away_team) &
                            (odds_df["GameDateEpoch"]==game_date))].reset_index()

    # If the game doesn't exist
    #if len(this_game_df) == 0:
    #    print ("Can't find game %s %s %s" % (Tutils.epoch2tme(game_date, "%Y%m%d"), home_team, away_team))
    #else:
    #    print ("Found Game, Returning odds")
    #print (this_game_df)
    return (this_game_df.reset_index())

#    actual_df = pd.DataFrame()
#    for ind, row in this_game_df.iterrows():
#        odds_game_date = row['GameDateEpoch']
#        if odds_game_date == game_date:
#            #actual_df = pd.concat([actual_df, row])
#            actual_df = actual_df.append(row)

def get_team_over_under(game_df, team, home_team_str, away_team_str):
    """
    Returns counts of over/unders for this team
    """
    team_df = game_df[((game_df[home_team_str]==team) |
                       (game_df[away_team_str]==team))]
    info_list = analyze_over_under(team_df)
    return (info_list)


def add_over_under_col(game_df, home_points_col, away_points_col, col_name):    
    # Get count of how many games were over or under the spread
    under = 0
    over = 0
    perfect = 0
    skipped = 0
    new_col = []
    for ind, row in game_df.iterrows():
        if pd.isnull(row['predicted_over_under']):
            skipped += 1
            new_col.append(np.nan)
            continue
        if pd.isnull(row[home_points_col]) or pd.isnull(row[away_points_col]):
            skipped += 1
            new_col.append(np.nan)
            continue
        guess_points = row[home_points_col] + row[away_points_col]
        
        actual_points = row[HOME_TEAM_PTS] + row[AWAY_TEAM_PTS]
        predicted_points = row['predicted_over_under']
        # If the modeled points were greater than the over under, AND more points
        #    were scored than the over under, add a point
        if (abs(guess_points) > abs(predicted_points) and
            abs(actual_points) > abs(predicted_points)):
            # If more points were scored than predicted            
            over += 1
            new_col.append(1)
        # If the modeled points were less than the over under, AND less points
        #    were scored than the over under, add a point            
        elif (abs(guess_points) < abs(predicted_points) and
              abs(actual_points) < abs(predicted_points)):
            # If less points were scored than predicted
            under += 1
            new_col.append(-1)
        elif (abs(actual_points) == abs(predicted_points)):
            # If the predicted points matched the game points perfectly
            perfect += 1
            new_col.append(0)
        else:
            skipped+=1
            new_col.append(np.nan)
            
    game_df[col_name] = new_col

    return (over, under, perfect, skipped)

def add_over_under_col_threshold(game_df, home_points_col, away_points_col, col_name, threshold):
    """
    Same as 'add_over_under_col' but only looks at games where
    the difference is over a certain threshold
    """
    # Get count of how many games were over or under the spread
    under = 0
    over = 0
    perfect = 0
    skipped = 0
    new_col = []
    for ind, row in game_df.iterrows():
        if pd.isnull(row['predicted_over_under']):
            skipped += 1
            new_col.append(np.nan)
            continue
        if pd.isnull(row[home_points_col]) or pd.isnull(row[away_points_col]):
            skipped += 1
            new_col.append(np.nan)
            continue
        avg_points = row[home_points_col] + row[away_points_col]
        predicted_points = row['predicted_over_under']
        if threshold > 0:
            # Skip cases where the predicted_points + threshold ISN'T more then the gamepoints
            if (abs(avg_points) < (abs(predicted_points) + threshold)):
                skipped += 1
                new_col.append(np.nan)
                continue
        else:
            # skip cases where the predicted_points + threshold IS greater than predicted            
            if (abs(avg_points) > (abs(predicted_points) + threshold)):
                skipped += 1
                new_col.append(np.nan)
                continue
        game_points = row[HOME_TEAM_PTS] + row[AWAY_TEAM_PTS]
        if abs(game_points) > abs(predicted_points):
            # If more points were scored than predicted            
            over += 1
            new_col.append(1)
        elif abs(game_points) < abs(predicted_points):
            # If less points were scored than predicted
            under += 1
            new_col.append(-1)
        else:
            # If the predicted points matched the game points perfectly
            perfect += 1
            new_col.append(0)

    game_df[col_name] = new_col

    return (over, under, perfect, skipped)

def print_over_under(over, under, perfect, skipped):
    print ("---------------------------------------")
    print ("Num times more points were scored than predicted: %d" % over)
    print ("Num times less points were scored than predicted: %d" % under)
    print ("Num times vegas predicted the score perfectly: %d" % perfect)
    print ("Num games couldn't find odds for: %d" % skipped)
    print ("---------------------------------------")    


def analyze_over_under(game_df):    
    # Get count of how many games were over or under the spread
    skipped = len(game_df[pd.isnull(game_df['Over_Under_HIT'])]==True)
    under = len(game_df[game_df['Over_Under_HIT']==-1])
    over = len(game_df[game_df['Over_Under_HIT']==1])
    perfect = len(game_df[game_df['Over_Under_HIT']==0])
    
    return (over, under, perfect, skipped)

def get_odds_dt(row):
    year = Tutils.epoch2tme(row['Time'], "%Y")
    dt_str = row['Game_Time'].split()
    (mon,day) = dt_str[0].split("/")
    #if int(mon) > 6:
    #    year = int(year)-1
    out_str = "%s%s%s" % (year, mon, day)
    return Tutils.tme2epoch(out_str, "%Y%m%d")

def add_odds_game_date(odds_df):
    """
    """
    odds_df["GameDateEpoch"] = odds_df.apply(lambda row: get_odds_dt(row), axis=1)
    return

def make_team_df_map(game_df):
    """
    """
    team_df_map = {}
    all_teams = game_df[HOME_TEAM].append(game_df[AWAY_TEAM]).unique().tolist()
    for tm in all_teams:
        team_df_map[tm] = game_df[((game_df[HOME_TEAM]==tm) |
                                   (game_df[AWAY_TEAM]==tm))].sort_values('EpochDt').reset_index(drop=True)
    return team_df_map

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

def get_prior_game_avg(row, base_df, lookback_games):
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
        return team_df.iloc[-3:]["PointsScored"].mean()
    
    
def print_threshold_counts(home_col, away_col, threshold, game_df, col_name):
    """
    Prints how many times the 'home_col'+'away_col' beat the predicted based on the threshold
    """
    #
    # Check O/U when teams are averaging more than thshld points over the spread
    #
    this_info = add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_%d" % (col_name, threshold)),
                                                       threshold)
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG > spread+%d: %s" % (threshold, col_name))
    print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    if this_info[0]+this_info[0]==0:
        oo_pct = np.nan
        oo_count = np.nan
    elif this_info[1] == 0:
        oo_pct = 5
        oo_count = this_info[0]+this_info[1]        
    else:
        oo_pct = this_info[0]/this_info[1]
        oo_count = this_info[0]+this_info[1]
    #
    # Check O/U when teams are averaging thshld points less than the spread
    #
    this_info = add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_%d" % (col_name, -threshold)),
                                                       -threshold)
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG < spread-%d: %s" % (threshold, col_name))    
    print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    if this_info[0]+this_info[0]==0:
        uu_pct = np.nan
        uu_count = np.nan
    elif this_info[0] == 0:
        uu_pct = 5
        uu_count = this_info[0]+this_info[1]        
    else:
        uu_pct = this_info[1]/this_info[0]
        uu_count = this_info[1]+this_info[0]

    return (oo_pct, oo_count, uu_pct, uu_count)
    
