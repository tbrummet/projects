#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import pandas as pd
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
    print ("Looking for game")
    print (game_date, home_team , away_team)
    game_df = odds_df[((odds_df['Home_Team']==home_team) &
                       (odds_df['Away_Team']==away_team))].reset_index()

    # If the game doesn't exist
    if len(game_df) == 0:
        print ("Can't find game")
        return game_df
        
    actual_df = pd.DataFrame()
    for ind, row in game_df.iterrows():
        odds_game_date = row['Game_Time'].split()[0]
        if odds_game_date == game_date:
            #actual_df = pd.concat([actual_df, row])
            actual_df = actual_df.append(row)
            
    print ("Found game, returning odds")
    return actual_df.reset_index()
    

def match_games(game_df, odds_df):
    """
    """
    games_map = {}
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
        game_key = "%s|%s|%s" % (game_date, home_team, away_team)
        
        if (len(game_odds) > 0):
            game_points = row['VisitorPTS'] + row['HomePTS']
            predicted_points = game_odds['Over_under_Open'].tolist()[-1]
            predicted_spread = game_odds['Point_spread_Open'].tolist()[-1]      
            games_map[game_key] = [row['HomePTS'], row['VisitorPTS'],
                                   predicted_points, predicted_spread]
            #for ind, row in game_odds.iterrows():
            #    print (row['Time'], Tutils.epoch2tme(row['Time'], "%Y/%m/%d %H%M"), row['Over_under_Open'])


    analyze_over_under(games_map)
    #analyze_point_spread(games_map)

def analyze_point_spread(games_map):
    """
    """
                         

def analyze_over_under(games_map):    
    # Get count of how many games were over or under the spread
    print ("Analyzing %d games" % (len(games_map)))
    under = 0
    over = 0
    perfect = 0
    for key in games_map:
        game_points = games_map[key][0] + games_map[key][1]
        predicted_points = games_map[key][2]
        # If the predicted points were less than the actual points
        if abs(game_points) > abs(predicted_points):
            under += 1
        elif abs(game_points) < abs(predicted_points):
            # If the predicted points were more than the game points            
            over += 1
        else:
            # If the predicted points matched the game points perfectly
            perfect += 1
    print ("Num times more points were scored than predicted: %d" % under)
    print ("Num times less points were scored than predicted: %d" % over)
    print ("Num times vegas predicted the score perfectly: %d" % perfect)        
        

def process(game_file, odds_dir, file_base):
    """
    """
    # First read the game file
    game_df = pd.read_csv(game_file)

    # Read all of the odds files
    odds_df = read_odds_dir(odds_dir, file_base)

    # Match up the games
    games_map = match_games(game_df, odds_df)
    

def main():
    usage_str = "%prog basketball_game_file odds_dir file_base"
    usage_str = "%s\n\t basketball_game_file : csv file containing final scores of the games" % usage_str
    usage_str = "%s\n\t odds_dir : directory with dated subdirs containing csv files of the odds" % usage_str
    usage_str = "%s\n\t file_base : basename of files to grab" % usage_str    
    
    
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 3:
        parser.print_help()
        sys.exit(2)

                                  
    game_file = args[0]
    odds_dir = args[1]
    file_base = args[2]

    process(game_file, odds_dir, file_base)


if __name__ == "__main__":
    main()
