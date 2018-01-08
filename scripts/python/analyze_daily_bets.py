#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import NBA_utils
import Tutils
import numpy as np

HOME_TEAM = 'HomeTeam'
HOME_TEAM_PTS = 'HomePoints'
AWAY_TEAM = 'AwayTeam'
AWAY_TEAM_PTS = 'AwayPoints'

def look_at_daily_bets(game_df, odds_df, date):
    """
    """
    # Convert the date to an epoch dt
    this_epch = Tutils.tme2epoch(date, "%Y%m%d")

    # sort by time downloaded and remove duplicates, keeping the most recent one
    odds_df = odds_df.sort_values("Time")
    recent_odds_df = odds_df.drop_duplicates(subset=(["Away_Team","Home_Team","Game_Time"]),keep='last')


    # Maps team names to dataframe of that team
    team_df_map = NBA_utils.make_team_df_map(game_df)
    all_teams = sorted(list(team_df_map.keys()))

    # Add whatever columns we want to look at
    num_games = 6
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games
    add_col_and_print_threshold_counts(game_df, home_col, away_col, num_games, team_df_map)    
    #  Right now is averages over past 5 and 2 games
    num_games = 5
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games
    add_col_and_print_threshold_counts(game_df, home_col, away_col, num_games, team_df_map)
    num_games = 4
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games
    add_col_and_print_threshold_counts(game_df, home_col, away_col, num_games, team_df_map)
    num_games = 3
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games
    add_col_and_print_threshold_counts(game_df, home_col, away_col, num_games, team_df_map)
    num_games = 2
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games
    add_col_and_print_threshold_counts(game_df, home_col, away_col, num_games, team_df_map)
    

    home_col = "HomeTeamAvg%sGames" % num_games
    game_df[home_col] = game_df.apply(lambda row: calculate_team_avg_xdays(row['HomeTeam'],
                                                                           num_games,
                                                                           row,
                                                                           team_df_map[row['HomeTeam']]),
                                      axis=1)    
    away_col = "AwayTeamAvg%sGames" % num_games
    game_df[away_col] = game_df.apply(lambda row: calculate_team_avg_xdays(row['AwayTeam'],
                                                                           num_games,
                                                                           row,
                                                                           team_df_map[row['AwayTeam']]),
                                      axis=1)

    #------------------------------------------------------------------
    #------------------------------------------------------------------    
           
    num_games = 2
    home_col = "HomeTeamAvgPast%sGames" % num_games
    game_df[home_col] = game_df.apply(lambda row: calculate_team_avg_past_xdays(row['HomeTeam'],
                                                                                num_games,
                                                                                row,
                                                                                team_df_map[row['HomeTeam']]),
                                      axis=1)
    away_col = "AwayTeamAvgPast%sGames" % num_games
    game_df[away_col] = game_df.apply(lambda row: calculate_team_avg_past_xdays(row['AwayTeam'],
                                                                                num_games,
                                                                                row,
                                                                                team_df_map[row['AwayTeam']]),
                                      axis=1)
    this_info = NBA_utils.add_over_under_col(game_df, home_col, away_col,("OU_HIT_%s_avg" % num_games))
    print ("NUM GAMES AVG OVER/UNDERS: %d" % num_games)
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])    
    game_df.to_csv("game_df.csv")
    # Add columns for fields we want to modify to the database
    #for tme in all_teams:
    #    num_games = 5        
    #    new_col = "last_%s_game_avg" % num_games
    #    team_df = team_df_map[tme]
    #    team_df[new_col] = team_df.apply(lambda row : calculate_team_avg_past_xdays(tme, num_games, row, team_df), axis=1)
    #    num_games = 2
    #    new_col = "last_%s_game_avg" % num_games
    #    team_df = team_df_map[tme]
    #    team_df[new_col] = team_df.apply(lambda row : calculate_team_avg_past_xdays(tme, num_games, row, team_df), axis=1)

    #
    # First, get the lines for this date
    #    
    day_df = recent_odds_df[recent_odds_df['GameDateEpoch']==this_epch]

    # Add this row to check for this days bets
    num_games=3
    home_col = "HomeTeamAvg%sGames" % num_games
    game_df[home_col] = game_df.apply(lambda row: calculate_team_avg_xdays(row['HomeTeam'],
                                                                           num_games,
                                                                           row,
                                                                           team_df_map[row['HomeTeam']]),
                                      axis=1)
    away_col = "AwayTeamAvg%sGames" % num_games
    game_df[away_col] = game_df.apply(lambda row: calculate_team_avg_xdays(row['AwayTeam'],
                                                                           num_games,
                                                                           row,
                                                                           team_df_map[row['AwayTeam']]),
                                      axis=1)    
    for ind, row in day_df.iterrows():
        print ("Info on game %s at %s. Over_Under: %f" % (row['Away_Team'], row['Home_Team'], row['Over_under_Open']))

        # Look at over/unders for this team in either home or away games
        print_team_over_unders(game_df, row, 'Away_Team')
        print_team_over_unders(game_df, row, 'Home_Team')        

        # Look at last 3 away games for away team
        print_last_x_games(game_df, this_epch, 3, 'RemappedAwayTeam', 'Away_Team', row, 'away')
        print_last_x_games(game_df, this_epch, 3, 'RemappedHomeTeam', 'Home_Team', row, 'home')


        #
        # THIS IS THE KEY RIGHT NOW
        #
        away_team_df = game_df[(game_df['RemappedAwayTeam']==row['Away_Team']) |
                               (game_df['RemappedHomeTeam']==row['Away_Team'])]
        if away_team_df.iloc[-1]['RemappedAwayTeam'] == row['Away_Team']:
            away_team_avg = away_team_df.iloc[-1]['AwayTeamAvg3Games']            
        else:
            away_team_avg = away_team_df.iloc[-1]['HomeTeamAvg3Games']            
        print ("%s %s : %f" % (row['Away_Team'], 'TeamAvg3Games', away_team_avg))
        away_team_df.to_csv("tmp.csv")
        
        home_team_df = game_df[(game_df['RemappedAwayTeam']==row['Home_Team']) |
                               (game_df['RemappedHomeTeam']==row['Home_Team'])]
        if home_team_df.iloc[-1]['RemappedAwayTeam'] == row['Away_Team']:
            home_team_avg = home_team_df.iloc[-1]['AwayTeamAvg3Games']            
        else:
            home_team_avg = home_team_df.iloc[-1]['HomeTeamAvg3Games']                    

        print ("%s %s : %f" % (row['Home_Team'], 'TeamAvg3Games', home_team_avg))
        print ("%f" % (home_team_avg+away_team_avg))
        if (home_team_avg+away_team_avg) - abs(row['Over_under_Open']) > 10:
            print ("YOOO BET ON THE OVER HERE: BEEN AVERAGING %d!!!" % (home_team_avg+away_team_avg))
        if (abs(row['Over_under_Open']) - (home_team_avg+away_team_avg)) > 10:
            print ("YOOO BET ON THE UNDER HERE: BEEN AVERAGING %d!!!" % (home_team_avg+away_team_avg))                   
            
        

        """
           This gets complicated because you need to do it for every team.
               Need to add column "home_team_avg_last_x_days"
               Need to add column "away_team_avg_last_x_days"
           DONE!!
        """
        #success_rate = get_team_xday_avg_vs_OU(row['Home_Team'], team_game_df, 5)

def add_col_and_print_threshold_counts(game_df, home_col, away_col, num_games, team_df_map):
    game_df[home_col] = game_df.apply(lambda row: calculate_team_avg_past_xdays(row['HomeTeam'],
                                                                                num_games,
                                                                                row,
                                                                                team_df_map[row['HomeTeam']]),
                                      axis=1)
    game_df[away_col] = game_df.apply(lambda row: calculate_team_avg_past_xdays(row['AwayTeam'],
                                                                                num_games,
                                                                                row,
                                                                                team_df_map[row['AwayTeam']]),
                                      axis=1)
    
    #
    #
    #
    this_info = NBA_utils.add_over_under_col(game_df, home_col, away_col, ("OU_HIT_%s_avg" % num_games))
    print ("NUM GAMES AVG OVER/UNDERS: %d" % num_games)    
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    #
    # Check O/U when teams are averaging more than 10 points over the spread
    #
    this_info = NBA_utils.add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_avg_%d" % (num_games, 10)),
                                                       10)
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG > spread+%d: %d games" % (10, num_games))
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    #
    # Check O/U when teams are averaging 10 points less than the spread
    #
    this_info = NBA_utils.add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_avg_%d" % (num_games, -10)),
                                                       -10)
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG < spread-%d: %d games" % (10, num_games))    
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])        
        
        
def get_team_xday_avg_vs_OU(team_name, team_df, num_games):
    team_df.to_csv("team_df.csv")
    sorted_team_df = team_df.sort_values(['EpochDt'])
    avg_col_name = "last_%s_game_avg" % num_games
    sorted_team_df[avg_col_name] = sorted_team_df.apply(lambda row : calculate_team_avg_past_xdays(team_name,
                                                                                                   num_games,
                                                                                                   row,
                                                                                                   sorted_team_df),
                                                        axis=1)    
    
    return 0.0

def calculate_team_avg_past_xdays(team_name, num_games, row, team_df):
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

def calculate_team_avg_xdays(team_name, num_games, row, team_df):
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

def print_last_x_games(game_df, this_epch, num_games, game_team_str, team_str, row, HA_str):
    last_x_games = game_df[((game_df[game_team_str]==row[team_str]) &
                            (game_df['EpochDt'] < this_epch))].sort_values(['EpochDt'])[-num_games:]
    info_list = NBA_utils.analyze_over_under(last_x_games)
    print ("\t%s has beat the spread %d times out of the last 3 %s games" % (row[team_str],
                                                                             info_list[0], HA_str))

        
def print_team_over_unders(game_df, row, team_str):
    info_list =  NBA_utils.get_team_over_under(game_df, row[team_str],
                                               'RemappedHomeTeam', 'RemappedAwayTeam')
    print ("\t%s(%s) Over(%d) Under(%d)" % (team_str, row[team_str],
                                            info_list[0], info_list[1]))    
        
def get_epoch_dt(row):
    game_date_str = str(int(row['GameTime']))
    return Tutils.tme2epoch(game_date_str, "%Y%m%d")
    
def process(game_dir, odds_dir, odds_base, date):
    """
    """
    # First read the game file
    game_df = NBA_utils.read_OP_bball_dir(game_dir)
    game_df['EpochDt'] = game_df.apply(lambda row: get_epoch_dt(row), axis=1)
    # Add remapped home and away team names for matching from odds -> game
    game_df['RemappedAwayTeam'] = game_df.apply(lambda row: NBA_utils.remap_team_name(row['AwayTeam']), axis=1)
    game_df['RemappedHomeTeam'] = game_df.apply(lambda row: NBA_utils.remap_team_name(row['HomeTeam']), axis=1)    
    
    # Read all of the odds files
    odds_df = NBA_utils.read_odds_dir(odds_dir, odds_base)

    # Add the game date column
    NBA_utils.add_odds_game_date(odds_df)
    
    # Add the predicted_scores and predicted_over_under spreads to the game df
    NBA_utils.add_odds(game_df, odds_df)

    # Add the 'Over_under_HIT' column to the dataframe
    # -1 = Less points scored than expected
    # 1 = More points scored than expected
    info_list = NBA_utils.add_over_under_col(game_df, "HomePoints", "AwayPoints", "Over_Under_HIT")
    print ("TOTAL OVER: %d" % info_list[0])
    print ("TOTAL UNDER: %d" % info_list[1])
    print ("TOTAL PERFECT: %d" % info_list[2])
    print ("TOTAL SKIPPED: %d" % info_list[3])    
    
    look_at_daily_bets(game_df, odds_df, date)
    

def main():
    usage_str = "%prog basketball_game_dir odds_dir file_base date"
    usage_str = "%s\n\t basketball_game_dir : dir containing csv file containing final scores of the games" % usage_str
    usage_str = "%s\n\t odds_dir : directory with dated subdirs containing csv files of the odds" % usage_str
    usage_str = "%s\n\t file_base : basename of files to grab" % usage_str    
    parser = OptionParser(usage = usage_str)

        
    (options, args) = parser.parse_args()
    
    if len(args) < 4:
        parser.print_help()
        sys.exit(2)

                                  
    game_dir = args[0]
    odds_dir = args[1]
    odds_base = args[2]
    date = args[3]

    process(game_dir, odds_dir, odds_base, date)


if __name__ == "__main__":
    main()
