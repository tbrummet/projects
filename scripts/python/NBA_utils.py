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

    # Make sure we have home and away scores
    df = df[(np.isfinite(df['HomePoints']) &
             (np.isfinite(df['AwayPoints'])))]
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
            predicted_points = game_odds['Over_under_VI Consensus'].tolist()[-1]
            predicted_spread = game_odds['Point_spread_VI Consensus'].tolist()[-1]      

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
        
        actual_points = row[home_points_col] + row[away_points_col]
        predicted_points = row['predicted_over_under']
        # If the modeled points were greater than the over under, AND more points
        #    were scored than the over under, add a point
        if abs(actual_points) > abs(predicted_points):
            # If more points were scored than predicted            
            over += 1
            new_col.append(1)
        # If the modeled points were less than the over under, AND less points
        #    were scored than the over under, add a point            
        elif abs(actual_points) < abs(predicted_points):
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


def add_OU_HIT_col(game_df, home_points_col, away_points_col, col_name):
    """
    """
    hit = 0
    missed = 0
    perfect = 0
    skipped = 0
    new_col = []
    """
    tmp_df = game_df.dropna(['predicted_over_under', home_points_col, away_points_col])
    tmp_df['avg_pts'] = tmp_df[home_points_col]+tmp_df[away_points_col]
    tmp_df['game_pts'] = tmp_df[HOME_TEAM_PTS] + tmp_df[AWAY_TEAM_PTS]
    hit = (len(tmp_df[(tmp_df['avg_pts'] > abs(tmp_df['predicted_over_under']) &
                      tmp_df['game_pts'] > abs(tmp_df['predicted_over_under']))]) +
           len(tmp_df[(tmp_df['avg_pts'] < abs(tmp_df['predicted_over_under']) &
                      tmp_df['game_pts'] < abs(tmp_df['predicted_over_under']))]) +))

    missed = (len(tmp_df[(tmp_df['avg_pts'] > abs(tmp_df['predicted_over_under']) &
                          tmp_df['game_pts'] < abs(tmp_df['predicted_over_under']))]) +
              len(tmp_df[(tmp_df['avg_pts'] < abs(tmp_df['predicted_over_under']) &
                       tmp_df['game_pts'] > abs(tmp_df['predicted_over_under']))]) +))
    perfect = (len(tmp_df['game_points']==abs(tmp_df['predicted_over_under'])))
    missed = len(tmp_df) - hit - missed - perfect
    """
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
        game_points = row[HOME_TEAM_PTS] + row[AWAY_TEAM_PTS]
        predicted_points = abs(row['predicted_over_under'])
        if avg_points > predicted_points:
            if game_points > predicted_points:
                hit +=1
                new_col.append(1)
            elif game_points < predicted_points:
                missed += 1
                new_col.append(-1)
            else:
                perfect += 1
                new_col.append(0)            
        elif avg_points < predicted_points:
            if game_points < predicted_points:
                hit += 1
                new_col.append(1)
                continue
            elif game_points > predicted_points:
                missed += 1
                new_col.append(-1)
                continue
            else:
                perfect += 1
                new_col.append(0)
        else:
            skipped += 1
            new_col.append(np.nan)
            
    game_df[col_name] = new_col

    return (hit, missed, perfect, skipped)                
            
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
        #
        # If we are missing any of these fields, skip
        # 
        if pd.isnull(row['predicted_over_under']):
            skipped += 1
            new_col.append(np.nan)
            continue
        if pd.isnull(row[home_points_col]) or pd.isnull(row[away_points_col]):
            skipped += 1
            new_col.append(np.nan)
            continue
        elif abs(row['predicted_over_under']) == 9999:
            skipped += 1
            new_col.append(np.nan)
            continue
        my_points = row[home_points_col] + row[away_points_col]
        predicted_points = abs(row['predicted_over_under'])
        #
        # If there is a posative threshold --
        #      ignore all cases where the avg was less than predicted+threshold
        #
        if threshold > 0:
#            if ((abs(my_points) < (predicted_points + threshold)) or
#                (abs(my_points) > (predicted_points + threshold+2))):
            if (abs(my_points) < (predicted_points + threshold)):                
                skipped += 1
                new_col.append(np.nan)
                continue
        #
        # If there is a negative threshold --
        #      ignore all cases where the avg was more than predicted+threshold
        #
        else:
            #if ((abs(my_points) > (predicted_points + threshold)) or
            #    (abs(my_points) < (predicted_points + threshold-2))):
            if (abs(my_points) > (predicted_points + threshold)):
                skipped += 1
                new_col.append(np.nan)
                continue
        game_points = row[HOME_TEAM_PTS] + row[AWAY_TEAM_PTS]
        if abs(game_points) > predicted_points:
            # If more points were scored than predicted            
            over += 1
            new_col.append(1)
        elif abs(game_points) < predicted_points:
            # If less points were scored than predicted
            under += 1
            new_col.append(-1)
        else:
            # If the predicted points matched the game points perfectly
            perfect += 1
            new_col.append(0)

    game_df[col_name] = new_col

    return (over, under, perfect, skipped)

def add_PS_col_threshold(game_df, home_points_col, away_points_col, col_name, threshold):
    """
    Same as 'add_over_under_col' but only looks at games where
    the difference is over a certain threshold -- POINT SPREAD
    """
    # Get count of how many games were over or under the spread
    hit = 0
    miss = 0
    perfect = 0
    skipped = 0
    new_col = []
    for ind, row in game_df.iterrows():
        #
        # If we are missing any of these fields, skip
        # 
        if pd.isnull(row['predicted_spread']):
            skipped += 1
            new_col.append(np.nan)
            continue
        if pd.isnull(row[home_points_col]) or pd.isnull(row[away_points_col]):
            skipped += 1
            new_col.append(np.nan)
            continue
        elif abs(row['predicted_spread'])==9999:
            skipped += 1
            new_col.append(np.nan)
            continue
        my_spread = row[away_points_col]-row[home_points_col]
        predicted_spread = row['predicted_spread']
        actual_spread = row[AWAY_TEAM_PTS] - row[HOME_TEAM_PTS]
        #
        # Ignore all cases where my PS doesn't differ from the given PS by more than threshold
        #
        if abs(my_spread - predicted_spread) < threshold:
            skipped += 1
            new_col.append(np.nan)
            continue
        #
        # Check to see if I hit or miss
        #
        if ((my_spread > predicted_spread) and
            (actual_spread > predicted_spread)):
            hit += 1
            new_col.append(1)
        elif ((my_spread < predicted_spread) and
              (actual_spread < predicted_spread)):
            hit += 1
            new_col.append(1)
        elif (actual_spread == predicted_spread):
            perfect += 1
            new_col.append(0)
        else:
            miss += 1
            new_col.append(-1)

    game_df[col_name] = new_col            
    return (hit, miss, perfect, skipped)

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
    if this_info[0]+this_info[1]==0:
        oo_pct = np.nan
        oo_count = np.nan
    elif this_info[1] == 0:
        #oo_pct = 5
        oo_pct = 1        
        oo_count = this_info[0]+this_info[1]        
    else:
        #oo_pct = this_info[0]/this_info[1]
        oo_pct = this_info[0]/(this_info[0]+this_info[1])
        oo_count = this_info[0]+this_info[1]
    #
    # Check O/U when teams are averaging thshld points less than the spread
    #
    this_info = add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_%d" % (col_name, -threshold)),
                                                       -threshold)
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG < spread-%d: %s" % (threshold, col_name))    
    print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    if this_info[0]+this_info[1]==0:
        uu_pct = np.nan
        uu_count = np.nan
    elif this_info[0] == 0:
        #uu_pct = 5
        uu_pct = 1
        uu_count = this_info[0]+this_info[1]        
    else:
        #uu_pct = this_info[1]/this_info[0]
        uu_pct = this_info[1]/(this_info[0]+this_info[1])
        uu_count = this_info[1]+this_info[0]

    return (oo_pct, oo_count, uu_pct, uu_count)

def print_PS_threshold_counts(home_col, away_col, threshold, game_df, col_name):
    """
    Prints how many times the 'home_col'+'away_col' beat the predicted based on the threshold
    """
    #
    # Check O/U when teams are averaging more than thshld points over the spread
    #
    this_info = add_PS_col_threshold(game_df, home_col, away_col,
                                     ("PS_HIT_%s_%d" % (col_name, threshold)),
                                     threshold)
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG > spread+%d: %s" % (threshold, col_name))
    print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    if this_info[0]+this_info[0]==0:
        hit_pct = np.nan
        hit_count = np.nan
    elif this_info[1] == 0:
        #oo_pct = 5
        hit_pct = 1        
        hit_count = this_info[0]
    else:
        #oo_pct = this_info[0]/this_info[1]
        hit_pct = this_info[0]/(this_info[0]+this_info[1])
        hit_count = this_info[0]
    miss_count = this_info[1]
    miss_pct = 1-hit_pct
    
    return (hit_pct, hit_count, miss_pct, miss_count)


def get_bball_epoch_dt(row):
    game_date_str = str(int(row['GameTime']))
    return Tutils.tme2epoch(game_date_str, "%Y%m%d")
    
def get_prior_score(row, base_df, lookback_games):
    """
      Used to create ML models, requires 'team' and 'gameTime' (seconds)
         NOTE : COULD BE MERGED WITH 'GET_PRIOR_SCORE_GAME_DF'
    """
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

def get_prior_score_game_df(row, base_df, team_col, ht_col, at_col, tim_col, lookback_games):
    """
      Used to create ML models, used for the 'game_df' created from the OP_basketball_games_dir
         NOTE : COULD BE MERGED WITH 'GET_PRIOR_SCORE'
    """
    if lookback_games==0:
        if row[team_col] == row[ht_col]:
            return row['HomePoints']
        else:
            return row['AwayPoints']
        
    # Get prior games for this team
    team_df = base_df[((base_df[ht_col] == row[team_col]) |
                       (base_df[at_col] == row[team_col]))]
    if len(team_df) == 0:
        return np.nan
    
    # Get only the previous games
    sorted_team_df = team_df[(team_df["EpochDt"] < row[tim_col])].sort_values("EpochDt").reset_index()
    if len(sorted_team_df) < lookback_games:
        return np.nan
    
    last_ind = len(sorted_team_df) - lookback_games
    last_game_row = sorted_team_df.loc[last_ind]
    
    if last_game_row[ht_col] == row[team_col]:
        return last_game_row['HomePoints']
    else:
        return last_game_row['AwayPoints']    

def calculate_team_avg_past_xdays_game_df(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[team_df['EpochDt'] < row['EpochDt']][-num_games:]
    # If there aren't at least x games, return missing
    if len(last_x_games) < num_games:
        return np.nan
    team_points = []
    for i, rw in last_x_games.iterrows():
        if rw['AwayTeam'] == team_name:
            team_points.append(rw['AwayPoints'])
        elif rw['HomeTeam'] == team_name:
            team_points.append(rw['HomePoints'])
    return (sum(team_points)/len(team_points))

def calculate_team_avg_xdays_game_df(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[team_df['EpochDt'] <= row['EpochDt']][-num_games:]
    # If there aren't at least x games, return missing
    if len(last_x_games) < num_games:
        return np.nan
    team_points = []
    for i, rw in last_x_games.iterrows():
        if rw['AwayTeam'] == team_name:
            team_points.append(rw['AwayPoints'])
        elif rw['HomeTeam'] == team_name:
            team_points.append(rw['HomePoints'])
    return (sum(team_points)/len(team_points))


def calculate_team_avg_past_xdays_base_df(row, base_df, lookback_games):
    """
    """
    # Get the last x games
    team_df = base_df[((base_df["Team"] == row["Team"]) &
                       (base_df["GameTime"] < row["GameTime"]))].sort_values("GameTime").reset_index()
    # If there aren't at least x games, return missing
    if len(team_df) < lookback_games:
        return np.nan
    return (team_df[-lookback_games:]["PointsScored"].mean())

def calculate_opp_team_allowed_avg_past_xdays_base_df(row, base_df, lookback_games):
    """
    """
    # Get the last x games
    team_df = base_df[((base_df["Team"] == row["OppTeam"]) &
                       (base_df["GameTime"] < row["GameTime"]))].sort_values("GameTime").reset_index()
    # If there aren't at least x games, return missing
    if len(team_df) < lookback_games:
        return np.nan
    return (team_df[-lookback_games:]["OppPointsScored"].mean())

def calculate_team_rest_base_df(row, base_df):
    """
    """
    # Get the last x games
    team_df = base_df[((base_df["Team"] == row["Team"]) &
                       (base_df["GameTime"] < row["GameTime"]))].sort_values("GameTime").reset_index()
    if len(team_df) == 0:
        return np.nan
    game_time = row["GameTime"]
    last_game_time = team_df.iloc[-1]["GameTime"]
    rest = round((game_time - last_game_time) / 86400)
    return rest

def calculate_opp_team_rest_base_df(row, base_df):
    """
    """
    # Get the last x games
    team_df = base_df[((base_df["Team"] == row["OppTeam"]) &
                       (base_df["GameTime"] < row["GameTime"]))].sort_values("GameTime").reset_index()
    if len(team_df) == 0:
        return np.nan
    game_time = row["GameTime"]
    last_game_time = team_df.iloc[-1]["GameTime"]
    rest = round((game_time - last_game_time) / 86400)
    return rest

def calculate_team_rest_game_df(team_name, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[team_df['EpochDt'] < row['EpochDt']]
    if len(last_x_games) == 0:
        return np.nan
    game_time = row['EpochDt']
    last_game_time = last_x_games.iloc[-1]["EpochDt"]
    rest = round((game_time - last_game_time) / 86400)
    return rest

def calculate_current_team_rest_game_df(team_name, row, team_df, this_epch):
    """
    """
    # Get the last x games
    last_x_games = team_df[team_df['EpochDt'] <= row['EpochDt']]
    if len(last_x_games) == 0:
        return np.nan
    last_game_time = last_x_games.iloc[-1]["EpochDt"]
    rest = round((this_epch - last_game_time) / 86400)
    return rest

def calculate_team_allowed_avg_past_xdays_game_df(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[team_df['EpochDt'] < row['EpochDt']][-num_games:]
    # If there aren't at least x games, return missing
    if len(last_x_games) < num_games:
        return np.nan
    team_points = []
    for i, rw in last_x_games.iterrows():
        if rw['AwayTeam'] == team_name:
            team_points.append(rw['HomePoints'])
        elif rw['HomeTeam'] == team_name:
            team_points.append(rw['AwayPoints'])
    return (sum(team_points)/len(team_points))

def calculate_team_allowed_avg_xdays_game_df(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[team_df['EpochDt'] <= row['EpochDt']][-num_games:]
    # If there aren't at least x games, return missing
    if len(last_x_games) < num_games:
        return np.nan
    team_points = []
    for i, rw in last_x_games.iterrows():
        if rw['AwayTeam'] == team_name:
            team_points.append(rw['HomePoints'])
        elif rw['HomeTeam'] == team_name:
            team_points.append(rw['AwayPoints'])
    return (sum(team_points)/len(team_points))


def analyze_point_spreads(game_df):
    """
    """
    # Get a count of the times vegas was over the spread and under
    OS = 0
    US = 0
    avg_error = []
    for ind, row in game_df.iterrows():
        if pd.isnull(row['predicted_spread']):
            continue
        elif abs(row['predicted_spread'])==9999:
            continue
        adjusted_home_points = row['HomePoints']+row['predicted_spread']
        if (adjusted_home_points > row['AwayPoints']):
            OS += 1
        else:
            US += 1
        avg_error.append(abs(adjusted_home_points - row['AwayPoints']))
        print (avg_error[-1])
    print ("Num Times spread was too high: %d" % OS)
    print ("Num Times spread was too low: %d" % US)
    print ("Avg Error: %f" % (sum(avg_error)/len(avg_error)))
    

def check_mult_var_OU_counts(var1, var2, game_df, value, new_col_name):
    """
    Looks at all cases where var1 AND var2 say 'value' and see how they compare vs the over under
    """
    hit = 0
    miss = 0
    perfect = 0
    new_col = []
    for ind, row in game_df.iterrows():
        # Skip mising rows
        if pd.isnull(row[var1]) or pd.isnull(row[var2]) or pd.isnull(row['Over_Under_HIT']):
            new_col.append(np.nan)
            continue
        # If both columns hit their value, it is a hit
        if row[var1] == value and row[var2] == value:
            new_col.append(1)
            hit += 1
        elif row[var1] == 0 and row[var2] == 0:
            new_col.append(0)
            perfect += 1                
        else:
            new_col.append(-1)
            miss += 1

    game_df[new_col_name] = new_col
    if hit == 0:
        hit_pct = 0
    else:
        hit_pct = (hit / (hit + miss))
    miss_pct = 1-hit_pct
    return (hit_pct, hit, miss_pct, miss)

def get_team_win_sum_base_df(row, base_df, team):
    """
    """
    team_df = base_df[((base_df['Team']==team) &
                       (base_df['GameTime']<row['GameTime']))]
    win_loss = 0
    for ind, rw in team_df.iterrows():
        if rw['PointsScored'] > rw['OppPointsScored']:
            win_loss += 1
        else:
            win_loss -= 1            
    return win_loss

def get_team_win_sum_game_df(row, game_df, team):
    """
    """
    team_home_df = game_df[((game_df['HomeTeam']==team) &
                            (game_df['EpochDt']<row['EpochDt']))]
    team_away_df = game_df[((game_df['AwayTeam']==team) &
                            (game_df['EpochDt']<row['EpochDt']))]    
    
    win_loss = 0
    for ind, rw in team_home_df.iterrows():
        if rw['HomePoints'] > rw['AwayPoints']:
            win_loss += 1
        else:
            win_loss -= 1            

    for ind, rw in team_away_df.iterrows():
        if rw['AwayPoints'] > rw['HomePoints']:
            win_loss += 1
        else:
            win_loss -= 1            

    return win_loss

def get_team_current_win_sum_game_df(row, game_df, team):
    """
    """
    team_home_df = game_df[((game_df['HomeTeam']==team) &
                            (game_df['EpochDt']<=row['EpochDt']))]
    team_away_df = game_df[((game_df['AwayTeam']==team) &
                            (game_df['EpochDt']<=row['EpochDt']))]    
    
    win_loss = 0
    for ind, rw in team_home_df.iterrows():
        if rw['HomePoints'] > rw['AwayPoints']:
            win_loss += 1
        else:
            win_loss -= 1            

    for ind, rw in team_away_df.iterrows():
        if rw['AwayPoints'] > rw['HomePoints']:
            win_loss += 1
        else:
            win_loss -= 1            

    return win_loss

def calc_team_win_sum_base_df(base_df):
    """
    """
    team_map = {}
    all_teams = base_df['Team'].unique().tolist()
    for tm in all_teams:
        tm_games = base_df[base_df['Team']==tm]
        win_loss = 0
        for ind, row in tm_games.iterrows():
            if row['PointsScored'] > row['OppPointsScored']:
                win_loss += 1
            else:
                win_loss -= 1            
        team_map[tm] = win_loss
        
    return team_map

def calc_team_win_sum_game_df(game_df):
    """
    """
    team_map = {}
    all_teams = pd.unique(game_df[['HomeTeam','AwayTeam']].values.ravel('K')).tolist()
    for tm in all_teams:
        win_loss = 0        
        tm_home_games = game_df[game_df['HomeTeam']==tm]
        tm_away_games = game_df[game_df['AwayTeam']==tm]        
        for ind, row in tm_home_games.iterrows():
            if row['HomePoints']>row['AwayPoints']:
                win_loss+=1
            else:
                win_loss-=1                
        for ind, row in tm_away_games.iterrows():
            if row['AwayPoints'] > row['HomePoints']:
                win_loss += 1
            else:
                win_loss -= 1            
        team_map[tm] = win_loss
        
    return team_map
