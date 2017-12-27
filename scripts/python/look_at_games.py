#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import pandas as pd
import numpy as np
import Tutils

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

def find_odds(odds_df, game_date, home_team, away_team):
    #print ("Looking for game")
    #print (game_date, home_team , away_team)
    this_game_df = odds_df[((odds_df['Home_Team']==home_team) &
                       (odds_df['Away_Team']==away_team))].reset_index()

    # If the game doesn't exist
    if len(this_game_df) == 0:
        #print ("Can't find game")
        return this_game_df
        
    actual_df = pd.DataFrame()
    for ind, row in this_game_df.iterrows():
        odds_game_date = row['Game_Time'].split()[0]
        if odds_game_date == game_date:
            #actual_df = pd.concat([actual_df, row])
            actual_df = actual_df.append(row)
            
    #print ("Found game, returning odds")
    return actual_df.reset_index()
    

def add_odds(game_df, odds_df):
    """
    Adds the predicted over/under keys as columns to the game_df dataframe
    """
    predicted_spread_list = []
    predicted_over_under_list = []
    for ind, row in game_df.iterrows():
        game_date = row['Date']
        if row['Home/Neutral'].find("Los Angeles Lakers") != -1:
            home_team = "L.A. Lakers"
        elif row['Home/Neutral'].find("Los Angeles Clippers") != -1:
            home_team = "L.A. Clippers"
        else:            
            home_team = ' '.join(row['Home/Neutral'].split()[:-1])
            
        if row['Visitor/Neutral'].find("Los Angeles Lakers") != -1:
            away_team = "L.A. Lakers"
        elif row['Visitor/Neutral'].find("Los Angeles Clippers") != -1:
            away_team = "L.A. Clippers"
        else:            
            away_team = ' '.join(row['Visitor/Neutral'].split()[:-1])
        date_fields = game_date.split()
        # Need to fix this with right conversion
        mon = 12
        day = "%02d" % int(date_fields[2])
        formatted_date = "%s/%s" % (mon, day)

        game_odds = find_odds(odds_df, formatted_date, home_team, away_team)

        
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
    #analyze_point_spread(games_map)

def analyze_team_over_under(game_df):
    """
    Look at the over under spreads for each team, not considering home/away
    """
    # Get all of the teams that we have
    all_teams = game_df['Home/Neutral'].append(game_df['Visitor/Neutral']).unique().tolist()

    # Loop over each specific team, and see how games they play in compare to the over/under
    team_list = []
    home_over_list = []
    home_under_list = []
    home_perfect_list = []
    home_skipped_list = []
    away_over_list = []
    away_under_list = []
    away_perfect_list = []
    away_skipped_list = []
    
    for team in all_teams:
        # Get all home games for this team
        team_home_games = game_df[game_df['Home/Neutral']==team]
        # Check the over/under spreads
        (home_over, home_under, home_perfect, home_skipped) = analyze_over_under(team_home_games)
        
        # Get all away games for this team
        team_away_games = game_df[game_df['Visitor/Neutral']==team]
        # Check the over/under spreads
        (away_over, away_under, away_perfect, away_skipped) = analyze_over_under(team_away_games)
        team_list.append(team)
        home_over_list.append(home_over)
        home_under_list.append(home_under)
        home_perfect_list.append(home_perfect)
        home_skipped_list.append(home_skipped)
        away_over_list.append(away_over)
        away_under_list.append(away_under)
        away_perfect_list.append(away_perfect)
        away_skipped_list.append(away_skipped)
        
        #print ("Home games for team: %s" % team)
        #print_over_under(home_over, home_under, home_perfect, home_skipped)        
        #print ("Away games for team: %s" % team)
        #print_over_under(away_over, away_under, away_perfect, away_skipped)

    df = pd.DataFrame()
    df['Team'] = team_list
    df['Home_over_count'] = home_over_list
    df['Home_under_count'] = home_under_list
    df['Home_perfect_count'] = home_perfect_list
    df['Home_skipped_count'] = home_skipped_list
    df['Away_over_count'] = away_over_list
    df['Away_under_count'] = away_under_list
    df['Away_perfect_count'] = away_perfect_list
    df['Away_skipped_count'] = away_skipped_list            
    df['Total_over_count'] = df['Home_over_count']+df['Away_over_count']
    df['Total_under_count'] = df['Home_under_count']+df['Away_under_count']
    df['Total_perfect_count'] = df['Home_perfect_count']+df['Away_perfect_count']
    df['Total_skipped_count'] = df['Home_skipped_count']+df['Away_skipped_count']
    out_file = "Team_away_under_map.csv"
    print ("Writing team over under counts to %s" % out_file)
    df.to_csv(out_file, columns = ['Team', 'Total_over_count', 'Total_under_count',
                                   'Total_perfect_count'], index=False)
    
def analyze_over_under(game_df):    
    # Get count of how many games were over or under the spread
    under = 0
    over = 0
    perfect = 0
    skipped = 0
    new_col = []
    for ind, row in game_df.iterrows():
        if pd.isnull(row['predicted_over_under']):
            skipped += 1
            new_col.append(-1)
            continue
        game_points = row['VisitorPTS'] + row['HomePTS']
        predicted_points = row['predicted_over_under']
        # If the predicted points were less than the actual points
        if abs(game_points) > abs(predicted_points):
            under += 1
            new_col.append(1)
        elif abs(game_points) < abs(predicted_points):
            # If the predicted points were more than the game points            
            over += 1
            new_col.append(0)
        else:
            # If the predicted points matched the game points perfectly
            perfect += 1
            new_col.append(9)

    game_df["Over_Under_HIT"] = new_col

    return (over, under, perfect, skipped)

def get_over_under_error(game_df):    
    # Get count of how many games were over or under the spread
    error_list = []
    for ind, row in game_df.iterrows():
        if pd.isnull(row['predicted_over_under']):
            continue
        game_points = row['VisitorPTS'] + row['HomePTS']
        predicted_points = abs(row['predicted_over_under'])
        diff = abs(game_points - predicted_points)
        error_list.append(diff)
    
    return (sum(error_list)/len(error_list))

def get_team_points_map(game_df):
    """
    """
    # Key = team
    # Value = [home_points, allowed_points_at_home,
    #          away_points, allowed_points_away,
    #          avg_points, avg_allowed_points]
    points_map = {}
    
    
    # Get all of the teams that we have
    all_teams = game_df['Home/Neutral'].append(game_df['Visitor/Neutral']).unique().tolist()
    for team in all_teams:
        points_list = []
        # Get every game where this team is the home team
        team_home_df = game_df[game_df['Home/Neutral']==team]
        home_points = team_home_df['HomePTS'].mean()
        points_list.append(home_points)
        allowed_home_points = team_home_df['VisitorPTS'].mean()
        points_list.append(allowed_home_points)
        
        # Get every game where this team is the away team
        team_away_df = game_df[game_df['Visitor/Neutral']==team]
        away_points = team_away_df['VisitorPTS'].mean()
        points_list.append(away_points)
        allowed_away_points = team_away_df['HomePTS'].mean()
        points_list.append(allowed_away_points)
        
        avg_scored_points = (home_points + away_points) / 2
        points_list.append(avg_scored_points)
        avg_allowed_points = (allowed_home_points + allowed_away_points) / 2
        points_list.append(avg_allowed_points)
        
        points_map[team] = points_list

    return points_map
        

def print_over_under(over, under, perfect, skipped):
    print ("---------------------------------------")
    print ("Num times more points were scored than predicted: %d" % under)
    print ("Num times less points were scored than predicted: %d" % over)
    print ("Num times vegas predicted the score perfectly: %d" % perfect)
    print ("Num games couldn't find odds for: %d" % skipped)
    print ("---------------------------------------")    


def find_previous_game_home_team(row, ind, game_df):
    """
    """
    # Get all games for this team and sort them on 'Start (ET)'
    team_df = game_df[((game_df['Home/Neutral'] == row['Home/Neutral']) |
                       (game_df['Visitor/Neutral'] == row['Home/Neutral']))].sort_values('EpochDt')

    t_ind = ind
    while t_ind > 0:
        t_ind -= 1
        if t_ind in team_df.index:
            return team_df.loc[t_ind]

    return pd.DataFrame()

def find_previous_game_away_team(row, ind, game_df):
    """
    """
    # Get all games for this team and sort them on 'Start (ET)'
    team_df = game_df[((game_df['Home/Neutral'] == row['Visitor/Neutral']) |
                       (game_df['Visitor/Neutral'] == row['Visitor/Neutral']))].sort_values('EpochDt')

    t_ind = ind
    while t_ind > 0:
        t_ind -= 1
        if t_ind in team_df.index:
            return team_df.loc[t_ind]

    return pd.DataFrame()

    
    
def analyze_team_rest_over_under(game_df):    
    """
    """
    time_sorted_df = game_df.sort_values('EpochDt').reset_index()
    for ind, row in time_sorted_df.iterrows():
        prev_home_team_game = find_previous_game_home_team(row, ind, time_sorted_df)
        prev_away_team_game = find_previous_game_away_team(row, ind, time_sorted_df)        
        if len(prev_home_team_game) == 0:
            print (row)
            print ("No previous home game")
            print ("------------------------------")
        else:
            print (row)
            print ("Previous_home_game ----------------")
            print (prev_home_team_game)
        if len(prev_away_team_game) == 0:
            print (row)
            print ("No previous away game")
            print ("------------------------------")            
        else:
            print (row)
            print ("Previous_away_game ----------------")
            print (prev_away_team_game)

            
def get_epoch_dt(row):
    game_date_str = row['Date']
    game_time_str = row['Start (ET)']

    full_str = "%s %s" % (game_date_str, game_time_str)
    return Tutils.tme2epoch(full_str, "%a %b %d %Y %I:%M %p")

def print_statistics(game_df, out_file):
    """
    """
    print ("Printing statistics to: %s" % out_file)
    outF = open(out_file, "w")

    # Get the total over_under error
    total_over_under_error = get_over_under_error(game_df)
    outLine = "Total over_under error: %s\n" % total_over_under_error
    outF.write(outLine)

    # Get actual team home and away points
    team_points_map = get_team_points_map(game_df)
    outLine = "Team, AvgHomePoints, AvgAllowedHomePoints, AvgAwayPoints, AvgAllowedPointsAwway, AvgPointsScored, AvgAllowedPoints\n"
    outF.write(outLine)
    for t in team_points_map:
        outLine = "%-25s,%3d,%3d,%3d,%3d,%3d,%3d\n" % (t, team_points_map[t][0], team_points_map[t][1],
                                                       team_points_map[t][2], team_points_map[t][3],
                                                       team_points_map[t][4], team_points_map[t][5])
        
        outF.write(outLine)
        
    outF.close()

def get_prior_home_game_avg(row, game_df, points_var, lookback_games):
    """
    """
    # Get a subset of the dataframe that is only for this teams home games
    home_game_df = game_df[((game_df["Home/Neutral"] == row["Home/Neutral"]) &
                            (game_df["EpochDt"] < row["EpochDt"]))].reset_index()

    return home_game_df[points_var][-lookback_games:].mean()

def get_prior_away_game_avg(row, game_df, points_var, lookback_games):
    """
    """
    # Get a subset of the dataframe that is only for this teams home games
    away_game_df = game_df[((game_df["Visitor/Neutral"] == row["Visitor/Neutral"]) &
                            (game_df["EpochDt"] < row["EpochDt"]))].reset_index()

    return away_game_df[points_var][-lookback_games:].mean()

def get_team_rest(row, game_df, key):
    """
    """
    # Get all games for this team
    team_df = game_df[((game_df['Home/Neutral'] == row[key]) | (game_df['Visitor/Neutral'] == row[key]))]
    time_df = team_df[(team_df['EpochDt'] < row['EpochDt'])].reset_index()

    if len(time_df) == 0:
        return -1
    
    last_game = time_df.iloc[-1]['EpochDt']

    # Get difference in time
    time_diff_secs = row['EpochDt']-last_game

    # Return the time in days and round up to nearest day
    return (round(time_diff_secs/86400))

def analyze_betting_strats(game_df):
    """
    """
    # Add columns for points scored over past X games
    prior_games_to_avg = [1,3]
    for prior_game in prior_games_to_avg:
        var_key = "HomeTeamPointsScoredPast_%d_HomeGame" % prior_game
        game_df[var_key] = game_df.apply(lambda row: get_prior_home_game_avg(row, game_df, "HomePTS", prior_game),
                                          axis=1)
        var_key = "AwayTeamPointsScoredPast_%d_AwayGame" % prior_game
        game_df[var_key] = game_df.apply(lambda row: get_prior_away_game_avg(row, game_df, "VisitorPTS", prior_game),
                                          axis=1)


    # Add columns for home and away team rest
    game_df["HomeRest"] = game_df.apply(lambda row: get_team_rest(row, game_df, "Home/Neutral"), axis=1)
    game_df["AwayRest"] = game_df.apply(lambda row: get_team_rest(row, game_df, "Visitor/Neutral"), axis=1)    

    rest_over_under_map = {}
    for ind, row in game_df.iterrows():
        # If there isn't a rest listed for one of the teams, skip
        if (row['HomeRest'] == -1) or (row['AwayRest'] == -1):
            continue
        total_rest = row['HomeRest'] + row['AwayRest']
        if total_rest not in rest_over_under_map:
            rest_over_under_map[total_rest] = []

        game_points = row['VisitorPTS'] + row['HomePTS']
        # APpend 1 if it is over the predicted amnt, 0 if not
        if game_points > abs(row['predicted_over_under']):
            rest_over_under_map[total_rest].append(1)
        elif game_points < abs(row['predicted_over_under']):
            rest_over_under_map[total_rest].append(0)
        
    for key in sorted(rest_over_under_map):
        print ("Total_Rest: %d" % key)
        print ("BeatOdds: %f" % (sum(rest_over_under_map[key]) / len(rest_over_under_map[key])))
        print ("SampleSize: %d" % len(rest_over_under_map[key]))
               
    ## Test Over/Under strategy
    #strat_success_list = []
    #for ind, row in game_df.iterrows():
    #    # Ignore if either of these are missing
    #    if pd.isnull(row['HomeTeamPointsScoredPast_1_HomeGame'])==True or pd.isnull(row['AwayTeamPointsScoredPast_1_AwayGame'])==True:
    #        continue
    #    # Ignore if we don't have predicted values
    #    if pd.isnull(row['predicted_over_under']):
    #        continue
    #    avg_points_scored_past_games = row['HomeTeamPointsScoredPast_1_HomeGame'] + row['AwayTeamPointsScoredPast_1_AwayGame']
    #    game_points = row['VisitorPTS'] + row['HomePTS']

    #    print (row)
    #    print ("Average_past_points: %f" % avg_points_scored_past_games)
    #    print ("Game_Points: %f" % game_points)
    #    if avg_points_scored_past_games < abs(row['predicted_over_under']):
    #        if game_points < abs(row['predicted_over_under']):
    #            strat_success_list.append(1)
    #        else:
    #            strat_success_list.append(0)
    #    elif avg_points_scored_past_games > abs(row['predicted_over_under']):
    #        if game_points > abs(row['predicted_over_under']):
    #            strat_success_list.append(1)
    #        else:
    #            strat_success_list.append(0)
    #    print ("Success/Fail: %s" % strat_success_list[-1])
    #print (len(strat_success_list))
    #print (sum(strat_success_list)/len(strat_success_list))
                
    game_df.to_csv("tmp.csv")
    
    
def process(game_file, odds_dir, file_base, options):
    """
    """
    # First read the game file
    game_df = pd.read_csv(game_file)

    """
    NOTE -- Add an epoch-time column to the game_df here
    """
    game_df['EpochDt'] = game_df.apply(lambda row: get_epoch_dt(row), axis=1)

    
    # Read all of the odds files
    odds_df = read_odds_dir(odds_dir, file_base)

    # Add the predicted_scores and predicted_over_under spreads to the game df
    add_odds(game_df, odds_df)

    if options.statistics_file:
        print_statistics(game_df, options.statistics_file)
        sys.exit()
    print ("Analyzing %d games" % (len(game_df)))
    
    # Look at all over unders
    (over, under, perfect, skipped) = analyze_over_under(game_df)
    print_over_under(over, under, perfect, skipped)

    # Look at team-specific over unders
    #analyze_team_over_under(game_df)

    # Find rest inbetween games
    #  -- To see if teams who just recently played often beat the spread or not
    #analyze_team_rest_over_under(game_df)

    # Look at betting strategies
    analyze_betting_strats(game_df)


def main():
    usage_str = "%prog basketball_game_file odds_dir file_base"
    usage_str = "%s\n\t basketball_game_file : csv file containing final scores of the games" % usage_str
    usage_str = "%s\n\t odds_dir : directory with dated subdirs containing csv files of the odds" % usage_str
    usage_str = "%s\n\t file_base : basename of files to grab" % usage_str    
    parser = OptionParser(usage = usage_str)
    parser.add_option("-s", "--print_statistics", dest="statistics_file", help="Write statistic info to this file")
        
    (options, args) = parser.parse_args()
    
    if len(args) < 3:
        parser.print_help()
        sys.exit(2)

                                  
    game_file = args[0]
    odds_dir = args[1]
    file_base = args[2]

    process(game_file, odds_dir, file_base, options)


if __name__ == "__main__":
    main()
