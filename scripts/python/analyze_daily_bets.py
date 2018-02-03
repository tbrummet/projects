#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import NBA_utils
import MODEL_utils
import Tutils
import numpy as np
import pandas as pd
from bokeh.plotting import figure, show, output_file
import pickle
import analyze_strategy

TOOLS = 'pan,box_zoom,reset,box_select,undo,redo,crosshair,hover'

HOME_TEAM = 'HomeTeam'
HOME_TEAM_PTS = 'HomePoints'
AWAY_TEAM = 'AwayTeam'
AWAY_TEAM_PTS = 'AwayPoints'


model_file = r"C:\Users\Tom\programming\static\model\basic_RF_V5.sav"

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
    #d = 3
    #r = 8
    d=3
    for r in range(1, 20):    
        pct_counts = add_col_and_print_threshold_counts(game_df, d, r, team_df_map)
        key = "%d %d" % (d, r)
        stat_map[key] = pct_counts
            
    #
    if options.plot_file:
        plot_over_under_pcts(stat_map, options.plot_file)
        plot_col_running_sum(game_df, "OU_HIT_3_avg_8", options.plot_file)

        
    #
    # Add the running 3game average to look at
    #
    num_games=3
    home_col = "HomeTeamAvg%sGames" % num_games
    game_df[home_col] = game_df.apply(lambda row: NBA_utils.calculate_team_avg_xdays_game_df(row['HomeTeam'],
                                                                                             num_games,
                                                                                             row,
                                                                                             team_df_map[row['HomeTeam']]),
                                      axis=1)
    away_col = "AwayTeamAvg%sGames" % num_games
    game_df[away_col] = game_df.apply(lambda row: NBA_utils.calculate_team_avg_xdays_game_df(row['AwayTeam'],
                                                                                             num_games,
                                                                                             row,
                                                                                             team_df_map[row['AwayTeam']]),
                                      axis=1)

    #
    # Load up model information
    #
    model = pickle.load(open(model_file, "rb"))
    # Load in the info file
    info_file = model_file.replace(".sav", ".info")
    info_F = open(info_file, "r")
    info_lines = info_F.readlines()
    # Get the predictors
    predictors = MODEL_utils.read_predictors_from_info(info_lines)
    training_end_date = MODEL_utils.read_end_date_from_info(info_lines)
    game_df = add_model_predictors(predictors, game_df, this_epch, team_df_map)
            
    game_df.to_csv("game_df.csv")
    #
    # Get the vegas lines for this date and iterate over them
    #    
    day_df = recent_odds_df[recent_odds_df['GameDateEpoch']==this_epch]    
    for ind, row in day_df.iterrows():
        print ("Info on game %s at %s. Over_Under: %f" % (row['Away_Team'], row['Home_Team'], row['Over_under_Open']))

        ###########################################################        
        #
        # Unnecessary info print statements
        #
        # Look at over/unders for this team in either home or away games
        print_team_over_unders(game_df, row, 'Away_Team')
        print_team_over_unders(game_df, row, 'Home_Team')        
        # Look at last 3 away games for away team
        print_last_x_games(game_df, this_epch, 3, 'RemappedAwayTeam', 'Away_Team', row, 'away')
        print_last_x_games(game_df, this_epch, 3, 'RemappedHomeTeam', 'Home_Team', row, 'home')
        ###########################################################

        # Get game_df maps for this team
        away_team_df = game_df[(game_df['RemappedAwayTeam']==row['Away_Team']) |
                               (game_df['RemappedHomeTeam']==row['Away_Team'])]
        if (len(away_team_df)==0):
            print ("Can't make map for team: '%s'" % row['Away_Team'])
            continue
        home_team_df = game_df[(game_df['RemappedAwayTeam']==row['Home_Team']) |
                               (game_df['RemappedHomeTeam']==row['Home_Team'])]
        if (len(home_team_df)==0):
            print ("Can't make map for team: %s" % row['Home_Team'])
            continue        

        #
        # THIS IS THE KEY RIGHT NOW
        #        
        if away_team_df.iloc[-1]['RemappedAwayTeam'] == row['Away_Team']:
            away_team_avg = away_team_df.iloc[-1]['AwayTeamAvg3Games']
        else:
            away_team_avg = away_team_df.iloc[-1]['HomeTeamAvg3Games']
        print ("\t%s %s : %f" % (row['Away_Team'], 'TeamAvg3Games', away_team_avg))
        
        if home_team_df.iloc[-1]['RemappedAwayTeam'] == row['Home_Team']:
            home_team_avg = home_team_df.iloc[-1]['AwayTeamAvg3Games']
        else:
            home_team_avg = home_team_df.iloc[-1]['HomeTeamAvg3Games']
        print ("\t%s %s : %f" % (row['Home_Team'], 'TeamAvg3Games', home_team_avg))
        avg_points = home_team_avg+away_team_avg        
        print ("\t%f" % (avg_points))
        #
        # If the teams have been averaging more than 7 over the O/U, it's usually over
        #
        if avg_points - abs(row['Over_under_Open']) >= 7:
            print ("  --YOOO BET ON THE OVER HERE: BEEN AVERAGING %d!!!" % (avg_points))
        ###########################################
        # Add modeled_points
        ###########################################

        # Get home team modeled points
        ht_preds_list = []
        at_preds_list = []
        for p in predictors:
            ht_pred_col = "%s_%s" % ('HomeTeam', p)
            at_pred_col = "%s_%s" % ('AwayTeam', p)

            if p.startswith("Opp"):
                #
                # Need differen't logic for getting opponents averages
                #
                # Get home Predictor
                if away_team_df.iloc[-1]['RemappedHomeTeam'] == row['Away_Team']:
                    if pd.isnull(away_team_df.iloc[-1][at_pred_col]):
                        ht_preds_list.append(np.nan)
                    else:
                        ht_preds_list.append(away_team_df.iloc[-1][at_pred_col])
                else:
                    if pd.isnull(away_team_df.iloc[-1][ht_pred_col]):
                        ht_preds_list.append(np.nan)
                    else:
                        ht_preds_list.append(away_team_df.iloc[-1][ht_pred_col])
                # Get Away predictors
                if home_team_df.iloc[-1]['RemappedHomeTeam'] == row['Home_Team']:
                    if pd.isnull(home_team_df.iloc[-1][at_pred_col]):
                        at_preds_list.append(np.nan)
                    else:                
                        at_preds_list.append(home_team_df.iloc[-1][at_pred_col])
                else:
                    if pd.isnull(home_team_df.iloc[-1][ht_pred_col]):
                        at_preds_list.append(np.nan)
                    else:
                        at_preds_list.append(home_team_df.iloc[-1][ht_pred_col])      
                    
            else:
                # Get home Predictor
                if home_team_df.iloc[-1]['RemappedHomeTeam'] == row['Home_Team']:
                    if pd.isnull(home_team_df.iloc[-1][ht_pred_col]):
                        ht_preds_list.append(np.nan)
                    else:
                        ht_preds_list.append(home_team_df.iloc[-1][ht_pred_col])
                else:
                    if pd.isnull(home_team_df.iloc[-1][at_pred_col]):
                        ht_preds_list.append(np.nan)
                    else:
                        ht_preds_list.append(home_team_df.iloc[-1][at_pred_col])
                # Get Away predictors
                if away_team_df.iloc[-1]['RemappedHomeTeam'] == row['Away_Team']:
                    if pd.isnull(away_team_df.iloc[-1][ht_pred_col]):
                        at_preds_list.append(np.nan)
                    else:                
                        at_preds_list.append(away_team_df.iloc[-1][ht_pred_col])
                else:
                    if pd.isnull(away_team_df.iloc[-1][at_pred_col]):
                        at_preds_list.append(np.nan)
                    else:
                        at_preds_list.append(away_team_df.iloc[-1][at_pred_col])      
                        
        ht_preds = np.array(ht_preds_list)
        at_preds = np.array(at_preds_list)        
        if np.nan not in ht_preds_list:
            ht_fcst = model.predict(ht_preds.reshape(1,-1))[0]
        else:
            ht_fcst = "-9999"
        if np.nan not in at_preds_list:            
            at_fcst = model.predict(at_preds.reshape(1,-1))[0]
        else:
            at_fcst = "-9999"
        print (ht_preds)
        print ("\tModeled HomeTeam points: %s" % ht_fcst)
        print (at_preds)
        print ("\tModeled AwayTeam points: %s" % at_fcst)
        modeled_OU = ht_fcst + at_fcst
        # If the modeled OU is more than 3 under the vegas line, bet this bitch
        if (abs(row['Over_under_Open'])-modeled_OU) > 3:
            print ("  --YOOO BET ON THE UNDER HERE: Model expecting: %d!!!" % (modeled_OU))            


        # If modeled is more than 2 under AND average is more than 2 under.  Bet.
        if (((abs(row['Over_under_Open'])-modeled_OU) > 2) and
            ((abs(row['Over_under_Open'])-avg_points) > 2)):
            print ("  --YOOO BET ON THE UNDER HERE: Model expecting %d AND avg saying %d!!!" % (modeled_OU, avg_points))
        print ("-------------------------------------------------------")        
        

def plot_col_running_sum(game_df, col, plot_file):
    """
    """
    p1 = figure(plot_width=1000, tools=TOOLS)
    #this_df = game_df.dropna([col])
    all_dates = game_df['GameTime'].unique().tolist()
    y_data = []
    x_data = []
    itr = 0
    running_sum = 0
    for d in sorted(all_dates):
        x_data.append(itr)
        running_sum = running_sum + game_df[(game_df['GameTime']==d)][col].sum()
        y_data.append(running_sum)
        itr+=1
    p1.line(x_data, y_data, legend=col)        
    show(p1)
    
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

def add_model_predictors(predictors, game_df, this_epch, team_df_map):
    """
    """
    # Add the necessary predictors for this model
    for p in predictors:
        if (p.startswith("Prior_")) and (p.find("_game_score")!=-1):
            # add a column for the prior game score
            prior_day = int(p.split("_")[1])
            home_team_pred = 'HomeTeam_' + p
            away_team_pred = 'AwayTeam_' + p            
            game_df[home_team_pred] = game_df.apply(lambda row: NBA_utils.get_prior_score_game_df(row, game_df, 'HomeTeam', 'HomeTeam', 'AwayTeam',
                                                                                                  'EpochDt', prior_day-1),
                                                    axis=1)
            game_df[away_team_pred] = game_df.apply(lambda row: NBA_utils.get_prior_score_game_df(row, game_df, 'AwayTeam', 'HomeTeam', 'AwayTeam',
                                                                                                  'EpochDt', prior_day-1),
                                                    axis=1)
        elif (p.startswith("Prior_")) and (p.find("_game_avg")!=-1):
            # add a column for the prior game avg
            prior_day = int(p.split("_")[1])
            home_team_pred = 'HomeTeam_' + p
            away_team_pred = 'AwayTeam_' + p            
            game_df[home_team_pred] = game_df.apply(lambda row: NBA_utils.calculate_team_avg_xdays_game_df(row['HomeTeam'], prior_day, row,
                                                                                                           team_df_map[row['HomeTeam']]),
                                                    axis=1)
            game_df[away_team_pred] = game_df.apply(lambda row: NBA_utils.calculate_team_avg_xdays_game_df(row['AwayTeam'], prior_day, row,
                                                                                                           team_df_map[row['AwayTeam']]),
                                                    axis=1)
        elif (p.startswith("Opp_allowed_Prior")) and (p.find("_game_avg")!=-1):
              # Add column for opponent allowed points
              prior_day = int(p.split("_")[3])
              home_team_pred = 'HomeTeam_' + p
              away_team_pred = 'AwayTeam_' + p
              game_df[home_team_pred] = game_df.apply(lambda row: NBA_utils.calculate_team_allowed_avg_xdays_game_df(row['AwayTeam'], prior_day,
                                                                                                                     row, team_df_map[row['AwayTeam']]),
                                                      axis=1)
              game_df[away_team_pred] = game_df.apply(lambda row: NBA_utils.calculate_team_allowed_avg_xdays_game_df(row['HomeTeam'], prior_day,
                                                                                                                     row, team_df_map[row['HomeTeam']]),
                                                      axis=1)
        elif (p.find("rest")!=-1):
              # Add column for rest
              home_team_pred = 'HomeTeam_' + p
              away_team_pred = 'AwayTeam_' + p
              game_df[home_team_pred] = game_df.apply(lambda row: NBA_utils.calculate_current_team_rest_game_df(row['HomeTeam'], row, team_df_map[row['HomeTeam']],
                                                                                                                this_epch),
                                                      axis=1)
              game_df[away_team_pred] = game_df.apply(lambda row: NBA_utils.calculate_current_team_rest_game_df(row['AwayTeam'], row, team_df_map[row['AwayTeam']],
                                                                                                                this_epch),
                                                      axis=1)             
        else:
              print ("Error: Not sure how to calculate: %s" % p)
              sys.exit()
              
    return game_df
    
def add_col_and_print_threshold_counts(game_df, num_games, thshld, team_df_map):
    #########
    #
    # Considering all games
    #
    home_col = "HomeTeamAvgPast%sGames" % num_games
    away_col = "AwayTeamAvgPast%sGames" % num_games    
    game_df[home_col] = game_df.apply(lambda row: NBA_utils.calculate_team_avg_past_xdays_game_df(row['HomeTeam'],
                                                                                                  num_games,
                                                                                                  row,
                                                                                                  team_df_map[row['HomeTeam']]),
                                      axis=1)
    game_df[away_col] = game_df.apply(lambda row: NBA_utils.calculate_team_avg_past_xdays_game_df(row['AwayTeam'],
                                                                                                  num_games,
                                                                                                  row,
                                                                                                  team_df_map[row['AwayTeam']]),
                                      axis=1)
    this_info = NBA_utils.add_OU_HIT_col(game_df, home_col, away_col, ("OU_HIT_%s_avg" % num_games))
    print (home_col, away_col)    
    print ("NUM GAMES AVG OVER/UNDERS: %d" % num_games)    
    NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    ###########
    ###########    
    #
    # Look at the counts for the home/away games
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
        #oo_pct = 5
        oo_pct = 1        
        oo_count = this_info[0]+this_info[1]        
    else:
        #oo_pct = this_info[0]/this_info[1]
        oo_pct = this_info[0]/(this_info[1]+this_info[0])
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
        #uu_pct = 5
        uu_pct = 1
        uu_count = this_info[0]+this_info[1]        
    else:
        #uu_pct = this_info[1]/this_info[0]
        uu_pct = this_info[1]/(this_info[1]+this_info[0])
        uu_count = this_info[1]+this_info[0]

    ###########
    #
    # Home/Away spearate
    #  Note -- Doesn't look so good so ignoring
    #
    #home_col = "HomeTeamHomeAvgPast%sGames" % num_games
    #away_col = "AwayTeamAwayAvgPast%sGames" % num_games    
    #game_df[home_col] = game_df.apply(lambda row: calculate_team_home_avg_past_xdays(row['HomeTeam'],
    #                                                                                 num_games,
    #                                                                                 row,
    #                                                                                 team_df_map[row['HomeTeam']]),
    #                                  axis=1)
    #game_df[away_col] = game_df.apply(lambda row: calculate_team_away_avg_past_xdays(row['AwayTeam'],
    #                                                                                 num_games,
    #                                                                                 row,
    #                                                                                 team_df_map[row['AwayTeam']]),
    #                                  axis=1)
    #
    #this_info = NBA_utils.add_OU_HIT_col(game_df, home_col, away_col, ("OU_HIT_HA_%s_avg" % num_games))
    #print (home_col, away_col)
    #print ("NUM GAMES AVG OVER/UNDERS: %d" % num_games)    
    #NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    #########
    
    ###########
    # Look at allowed points
    #  Note -- Doesn't look so good so ignoring
    ###########    
    #home_col = "HomeTeamAllowedAvgPast%sGames" % num_games
    #away_col = "AwayTeamAllowedAvgPast%sGames" % num_games    
    #game_df[home_col] = game_df.apply(lambda row: calculate_team_allowed_avg_past_xdays(row['HomeTeam'],
    #                                                                                    num_games,
    #                                                                                    row,
    #                                                                                    team_df_map[row['HomeTeam']]),
    #                                  axis=1)
    #game_df[away_col] = game_df.apply(lambda row: calculate_team_allowed_avg_past_xdays(row['AwayTeam'],
    #                                                                                    num_games,
    #                                                                                    row,
    #                                                                                    team_df_map[row['AwayTeam']]),
    #                                  axis=1)
    #this_info = NBA_utils.add_OU_HIT_col(game_df, home_col, away_col, ("OU_HIT_%s_avg" % num_games))
    #print (home_col, away_col)    
    #print ("NUM GAMES ALLOWED AVG OVER/UNDERS: %d" % num_games)    
    #NBA_utils.print_over_under(this_info[0], this_info[1], this_info[2], this_info[3])
    ###########
        
    return (oo_pct, oo_count, uu_pct, uu_count)
        
        

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
    usage_str = "%prog basketball_game_dir odds_dir league date"
    usage_str = "%s\n\t basketball_game_dir : dir containing csv file containing final scores of the games" % usage_str
    usage_str = "%s\n\t odds_dir : directory with dated subdirs containing csv files of the odds" % usage_str
    usage_str = "%s\n\t league : ['NBA' or 'NCAA']" % usage_str
    usage_str = "%s\n\t date : date of bets to look at (YYYYmmdd)" % usage_str        
    parser = OptionParser(usage = usage_str)
    parser.add_option("-p", "--plot_file", dest="plot_file", help="make a plots")
        
    (options, args) = parser.parse_args()
    
    if len(args) < 4:
        parser.print_help()
        sys.exit(2)

                                  
    game_dir = args[0]
    odds_dir = args[1]
    league = args[2]
    date = args[3]

    if league == 'NBA':
        odds_base = "NBA_vegas_bets"
    else:
        odds_base = "NCAAB_vegas_bets"
        
    process(game_dir, odds_dir, odds_base, date, league, options)


if __name__ == "__main__":
    main()
