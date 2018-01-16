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
from bokeh.plotting import figure, show, output_file
import analyze_ML_model

TOOLS = 'pan,box_zoom,reset,box_select,undo,redo,crosshair,hover'

HOME_TEAM = 'HomeTeam'
HOME_TEAM_PTS = 'HomePoints'
AWAY_TEAM = 'AwayTeam'
AWAY_TEAM_PTS = 'AwayPoints'

PREDICTORS = ['Prior_1_game_score', 'Prior_3game_avg', 'HomeAway']

def look_at_daily_bets(game_df, odds_df, date, options):
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

    stat_map = {}
    # Add whatever columns we want to look at
    for d in range(3,4):
        for r in range(3, 15):
            pct_counts = add_col_and_print_threshold_counts(game_df, d, r, team_df_map)
            key = "%d %d" % (d, r)
            stat_map[key] = pct_counts
            
    #
    if options.plot_file:
        plot_over_under_pcts(stat_map, options.plot_file)    

    #
    # Add the running 3game average to look at
    #
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
    """
    home_col = "HomeTeamHomeAvg%sGames" % num_games
    game_df[home_col] = game_df.apply(lambda row: calculate_team_home_avg_xdays(row['HomeTeam'],
                                                                                num_games,
                                                                                row,
                                                                                team_df_map[row['HomeTeam']]),
                                      axis=1)
    away_col = "AwayTeamAwayAvg%sGames" % num_games
    game_df[away_col] = game_df.apply(lambda row: calculate_team_away_avg_xdays(row['AwayTeam'],
                                                                                num_games,
                                                                                row,
                                                                                team_df_map[row['AwayTeam']]),
                                      axis=1)
    """
    #
    # Add the model predicted scores
    #
    #model_df = analyze_cubist_model.create_base_df(sorted_game_df)
    #model_df = analyze_cubist_model.augment_df(model_df)
    #model = analyze_cubist_model.create_model(model_df)
    #model_df.to_csv("model_df.csv")
    
    #
    # Get the vegas lines for this date and iterate over them
    #    
    day_df = recent_odds_df[recent_odds_df['GameDateEpoch']==this_epch]    
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
        if (len(away_team_df)==0):
            print ("Can't make map for team: '%s'" % row['Away_Team'])
            continue
        if away_team_df.iloc[-1]['RemappedAwayTeam'] == row['Away_Team']:
            away_team_avg = away_team_df.iloc[-1]['AwayTeamAvg3Games']
        else:
            away_team_avg = away_team_df.iloc[-1]['HomeTeamAvg3Games']
        print ("%s %s : %f" % (row['Away_Team'], 'TeamAvg3Games', away_team_avg))
        
        home_team_df = game_df[(game_df['RemappedAwayTeam']==row['Home_Team']) |
                               (game_df['RemappedHomeTeam']==row['Home_Team'])]
        if (len(home_team_df)==0):
            print ("Can't make map for team: %s" % row['Home_Team'])
            continue        
        if home_team_df.iloc[-1]['RemappedAwayTeam'] == row['Home_Team']:
            home_team_avg = home_team_df.iloc[-1]['AwayTeamAvg3Games']            
        else:
            home_team_avg = home_team_df.iloc[-1]['HomeTeamAvg3Games']
            
        print ("%s %s : %f" % (row['Home_Team'], 'TeamAvg3Games', home_team_avg))
        print ("%f" % (home_team_avg+away_team_avg))
        if (home_team_avg+away_team_avg) - abs(row['Over_under_Open']) >= 8:
            print ("YOOO BET ON THE OVER HERE: BEEN AVERAGING %d!!!" % (home_team_avg+away_team_avg))
        if (abs(row['Over_under_Open']) - (home_team_avg+away_team_avg)) >= 8:
            print ("YOOO BET ON THE UNDER HERE: BEEN AVERAGING %d!!!" % (home_team_avg+away_team_avg))
        # ----------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------
        # ----------------------------------------------------------------------------------------------
        """
        away_team_df = game_df[(game_df['RemappedAwayTeam']==row['Away_Team'])]
        away_team_avg = away_team_df.iloc[-1]['AwayTeamAwayAvg3Games']
        print ("%s %s : %f" % (row['Away_Team'], 'TeamAwayAvg3Games', away_team_avg))
        
        home_team_df = game_df[(game_df['RemappedHomeTeam']==row['Home_Team'])]
        if (len(home_team_df)==0):
            print ("Can't make map for team: %s" % row['Home_Team'])
            continue        
        home_team_avg = home_team_df.iloc[-1]['HomeTeamHomeAvg3Games']            
            
        print ("%s %s : %f" % (row['Home_Team'], 'TeamHomeAvg3Games', home_team_avg))
        print ("%f" % (home_team_avg+away_team_avg))
        if (home_team_avg+away_team_avg) > abs(row['Over_under_Open']):
            print ("YOOO BET ON THE OVER HERE: BEEN AVERAGING %d!!!" % (home_team_avg+away_team_avg))
        """
        
        
def plot_over_under_pcts(stat_map, plot_file):
    """
    Stat_map : dictionary
        key = 'game_avg threshold'
        value = [over_over_pct, over_over_count, under_under_pct, under_under_count]
    """
    p1 = figure(plot_width=1000, tools=TOOLS)
    all_keys = list(stat_map.keys())
    all_days = sorted(list(set([int(k.split()[0]) for k in all_keys])))
    all_thresholds = sorted(list(set([int(k.split()[1]) for k in all_keys])))
    print (all_days)
    print (all_thresholds)
    # For each day and threshold, add a line
    colors = ['red','blue', 'black', 'green']
    for d in range(0, len(all_days)):
        dy = all_days[d]
        oo_pcts = []
        oo_counts = []
        uu_pcts = []
        uu_counts = []
        for t in all_thresholds:
            key = "%d %d" % (dy, t)
            oo_pcts.append(stat_map[key][0])
            oo_counts.append(stat_map[key][1]/3)
            uu_pcts.append(-stat_map[key][2])
            uu_counts.append(stat_map[key][3]/3)
        lgd = "%d game avg Over Over pct" % dy
        p1.line(all_thresholds, oo_pcts, color = colors[d], legend=lgd)
        p1.circle(all_thresholds, oo_pcts, fill_color='white', size=oo_counts)
        lgd = "%d game avg Under Under pct" % dy
        p1.line(all_thresholds, uu_pcts, color = colors[d], legend=lgd)
        p1.circle(all_thresholds, uu_pcts, fill_color='white', size=uu_counts)
    show(p1)
        
def add_col_and_print_threshold_counts(game_df, num_games, thshld, team_df_map):
    #
    # Home/Away spearate
    #
    home_col = "HomeTeamHomeAvgPast%sGames" % num_games
    away_col = "AwayTeamAwayAvgPast%sGames" % num_games    
    game_df[home_col] = game_df.apply(lambda row: calculate_team_home_avg_past_xdays(row['HomeTeam'],
                                                                                     num_games,
                                                                                     row,
                                                                                     team_df_map[row['HomeTeam']]),
                                      axis=1)
    game_df[away_col] = game_df.apply(lambda row: calculate_team_away_avg_past_xdays(row['AwayTeam'],
                                                                                     num_games,
                                                                                     row,
                                                                                     team_df_map[row['AwayTeam']]),
                                      axis=1)    
    this_info = NBA_utils.add_over_under_col(game_df, home_col, away_col, ("OU_HIT_HA_%s_avg" % num_games))
    print (home_col, away_col)
    print ("NUM GAMES AVG OVER/UNDERS: %d" % num_games)    
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])

    #
    # Considering all games
    #
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games    
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
    this_info = NBA_utils.add_over_under_col(game_df, home_col, away_col, ("OU_HIT_%s_avg" % num_games))
    print (home_col, away_col)    
    print ("NUM GAMES AVG OVER/UNDERS: %d" % num_games)    
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])

    #
    # Look at the counts for the home/away games
    #
    #home_col = "HomeTeamHomeAvgPast%sGames" % num_games
    #away_col = "AwayTeamAwayAvgPast%sGames" % num_games        
    #
    # Check O/U when teams are averaging more than thshld points over the spread
    #
    this_info = NBA_utils.add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_avg_%d" % (num_games, thshld)),
                                                       thshld)
    print (home_col, away_col)    
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG > spread+%d: %d games" % (thshld, num_games))
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
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
    this_info = NBA_utils.add_over_under_col_threshold(game_df, home_col, away_col,
                                                       ("OU_HIT_%s_avg_%d" % (num_games, -thshld)),
                                                       -thshld)
    print (home_col, away_col)    
    print ("NUM GAMES AVG OVER/UNDERS WHEN AVG < spread-%d: %d games" % (thshld, num_games))    
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
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
        
        
def get_team_xday_avg_vs_OU(team_name, team_df, num_games):
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

def calculate_team_home_avg_past_xdays(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[((team_df['EpochDt'] < row['EpochDt']) &
                            (team_df['HomeTeam']== team_name))][-num_games:]
    
    # If there aren't at least x games, return missing
    if len(last_x_games) < num_games:
        return np.nan
    
    return last_x_games['HomePoints'].mean()

def calculate_team_away_avg_past_xdays(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[((team_df['EpochDt'] < row['EpochDt']) &
                            (team_df['AwayTeam']== team_name))][-num_games:]    
    if len(last_x_games) < num_games:
        return np.nan
    
    return last_x_games['AwayPoints'].mean()

def calculate_team_home_avg_xdays(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[((team_df['EpochDt'] <= row['EpochDt']) &
                            (team_df['HomeTeam']== team_name))][-num_games:]
    
    # If there aren't at least x games, return missing
    if len(last_x_games) < num_games:
        return np.nan
    
    return last_x_games['HomePoints'].mean()

def calculate_team_away_avg_xdays(team_name, num_games, row, team_df):
    """
    """
    # Get the last x games
    last_x_games = team_df[((team_df['EpochDt'] <= row['EpochDt']) &
                            (team_df['AwayTeam']== team_name))][-num_games:]    
    if len(last_x_games) < num_games:
        return np.nan
    
    return last_x_games['AwayPoints'].mean()


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
    
def process(game_dir, odds_dir, odds_base, date, league, options):
    """
    """
    #
    # First read the game file and add the epoch date (Only date, no HHMM)
    #
    game_df = NBA_utils.read_OP_bball_dir(game_dir)
    game_df['EpochDt'] = game_df.apply(lambda row: get_epoch_dt(row), axis=1)
    if league=='NBA':
        # Add remapped home and away team names for matching from odds -> game
        game_df['RemappedAwayTeam'] = game_df.apply(lambda row: NBA_utils.remap_team_name(row['AwayTeam']),
                                                    axis=1)
        game_df['RemappedHomeTeam'] = game_df.apply(lambda row: NBA_utils.remap_team_name(row['HomeTeam']),
                                                    axis=1)    
    else:
        # Add remapped home and away team names for matching from odds -> game
        game_df['RemappedAwayTeam'] = game_df.apply(lambda row: NBA_utils.remap_NCAA_team_name(row['AwayTeam']),
                                                    axis=1)
        game_df['RemappedHomeTeam'] = game_df.apply(lambda row: NBA_utils.remap_NCAA_team_name(row['HomeTeam']),
                                                    axis=1)    
        
        
    #
    # Read all of the odds files and add the game date
    #
    odds_df = NBA_utils.read_odds_dir(odds_dir, odds_base)
    NBA_utils.add_odds_game_date(odds_df)
    odds_df.to_csv("odds_df.csv")
    #
    # Add the predicted_scores and predicted_over_under spreads to the game df
    #
    NBA_utils.add_odds(game_df, odds_df, league)
    
    # Add the 'Over_under_HIT' column to the dataframe
    # -1 = Less points scored than expected
    # 1 = More points scored than expected
    info_list = NBA_utils.add_over_under_col(game_df, "HomePoints", "AwayPoints", "Over_Under_HIT")
    print ("TOTAL OVER: %d" % info_list[0])
    print ("TOTAL UNDER: %d" % info_list[1])
    print ("TOTAL PERFECT: %d" % info_list[2])
    print ("TOTAL SKIPPED: %d" % info_list[3])
    
    this_epoch = Tutils.tme2epoch(date, "%Y%m%d")
    
    # Limit the dataframe to only games that happened on or before this date
    game_df = game_df[game_df['EpochDt']<this_epoch].reset_index(drop=True)

    # Analyze this dates bets
    look_at_daily_bets(game_df, odds_df, date, options)
    game_df.to_csv("game_df.csv")    

def main():
    usage_str = "%prog basketball_game_dir odds_dir file_base league date"
    usage_str = "%s\n\t basketball_game_dir : dir containing csv file containing final scores of the games" % usage_str
    usage_str = "%s\n\t odds_dir : directory with dated subdirs containing csv files of the odds" % usage_str
    usage_str = "%s\n\t file_base : basename of files to grab" % usage_str
    usage_str = "%s\n\t league : ['NBA' or 'NCAA']" % usage_str
    usage_str = "%s\n\t date : date of bets to look at (YYYYmmdd)" % usage_str        
    parser = OptionParser(usage = usage_str)
    parser.add_option("-p", "--plot_file", dest="plot_file", help="make a plots")
        
    (options, args) = parser.parse_args()
    
    if len(args) < 5:
        parser.print_help()
        sys.exit(2)

                                  
    game_dir = args[0]
    odds_dir = args[1]
    odds_base = args[2]
    league = args[3]
    date = args[4]

    process(game_dir, odds_dir, odds_base, date, league, options)


if __name__ == "__main__":
    main()
