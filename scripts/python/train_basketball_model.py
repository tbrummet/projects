#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import NBA_utils
import Tutils
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor,GradientBoostingRegressor
from sklearn.datasets import make_classification
from sklearn.neighbors import KNeighborsRegressor,NearestCentroid
from sklearn.cross_decomposition import PLSRegression
from sklearn import datasets, linear_model, tree, utils, preprocessing
from sklearn.naive_bayes import GaussianNB,BernoulliNB
from sklearn import cross_validation
import pickle

# V1
#PREDICTORS = ['Prior_1_game_score', 'Prior_2_game_score', 'Prior_3_game_score',
#              'Prior_5_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest']
#V2
#PREDICTORS = ['Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest']
#V3
#PREDICTORS = ['Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest']
#V4
#PREDICTORS = ['Prior_3_game_avg', 'Prior_5_game_avg', 'Prior_7_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg',
#              'Opp_allowed_Prior_7_game_avg', 'rest']
#V5
#PREDICTORS = ['Prior_1_game_score', 'Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest']
#V6
#PREDICTORS = ['Prior_1_game_score', 'Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest',
#              'win_sum']
#V7 -- Decent at the under, non autotune
#PREDICTORS = ['Prior_1_game_score', 'Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest',
#              'Opp_rest', 'win_sum', 'Opp_win_sum']
#V8
PREDICTORS = ['Prior_1_game_score', 'Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest',
              'win_sum']
#V9
#PREDICTORS = ['Prior_1_game_score', 'Prior_3_game_avg', 'Prior_5_game_avg', 'Opp_allowed_Prior_3_game_avg', 'Opp_allowed_Prior_5_game_avg', 'rest',
#              'win_sum', 'Opp_win_sum']

WEEK = 604800

def create_base_df(sorted_game_df):
    # Iterate through the dataframe and make the data that I need
    #    Try 1:
    #       GameTime,Team,PointsScored
    game_time_list = []
    game_time_str_list = []
    teams_list = []
    opp_teams_list = []
    points_list = []
    opp_points_list = []    
    home_away_list = []  # 1 = home, 0 = away
    for ind, row in sorted_game_df.iterrows():
        if pd.isnull(row['AwayPoints']) or pd.isnull(row['HomePoints']):
            continue
        # For each row, need to make 2 rows, one for home and 1 for away team
        game_time_list.append(row["EpochDt"])
        game_time_list.append(row["EpochDt"])
        game_time_str_list.append(row["GameTime"])
        game_time_str_list.append(row["GameTime"])        
        teams_list.append(row["AwayTeam"])
        teams_list.append(row["HomeTeam"])
        points_list.append(row["AwayPoints"])
        points_list.append(row["HomePoints"])
        opp_teams_list.append(row["HomeTeam"])
        opp_teams_list.append(row["AwayTeam"])        
        opp_points_list.append(row["HomePoints"])
        opp_points_list.append(row["AwayPoints"])
        home_away_list.append(0)
        home_away_list.append(1)

    master_df = pd.DataFrame()
    master_df["GameTime"] = game_time_list
    master_df["GameTimeStr"] = game_time_str_list
    master_df["Team"] = teams_list
    master_df["PointsScored"] = points_list
    master_df["OppTeam"] = opp_teams_list
    master_df["OppPointsScored"] = opp_points_list
    master_df["HomeAway"] = home_away_list
    return master_df

def make_predictor_target_arrays(base_df, target):
    """
    """
    # First, subset the dataframe to only rows where all of the necessary vars are non-missing
    use_df = base_df[PREDICTORS+[target]].dropna()
    target_array = use_df[target].values
    predictor_array = use_df[PREDICTORS].values

    return (predictor_array, target_array)


def augment_df(base_df):
    """
    """
    # Add columns that I think will be helpful
    #   Prior 3 games and rest inbetween each one
    base_df["Prior_1_game_score"] = base_df.apply(lambda row: NBA_utils.get_prior_score(row, base_df, 1), axis=1)
    base_df["Prior_2_game_score"] = base_df.apply(lambda row: NBA_utils.get_prior_score(row, base_df, 2), axis=1)
    base_df["Prior_3_game_score"] = base_df.apply(lambda row: NBA_utils.get_prior_score(row, base_df, 3), axis=1)
    base_df["Prior_3_game_avg"] = base_df.apply(lambda row: NBA_utils.calculate_team_avg_past_xdays_base_df(row, base_df, 3),
                                                axis=1)    
    base_df["Prior_5_game_avg"] = base_df.apply(lambda row: NBA_utils.calculate_team_avg_past_xdays_base_df(row, base_df, 5),
                                                axis=1)
    base_df["Prior_7_game_avg"] = base_df.apply(lambda row: NBA_utils.calculate_team_avg_past_xdays_base_df(row, base_df, 7),
                                                axis=1)    
    base_df["Opp_allowed_Prior_3_game_avg"] = base_df.apply(lambda row: NBA_utils.calculate_opp_team_allowed_avg_past_xdays_base_df(row, base_df, 3),
                                                            axis=1)        
    base_df["Opp_allowed_Prior_5_game_avg"] = base_df.apply(lambda row: NBA_utils.calculate_opp_team_allowed_avg_past_xdays_base_df(row, base_df, 5),
                                                            axis=1)
    base_df["Opp_allowed_Prior_7_game_avg"] = base_df.apply(lambda row: NBA_utils.calculate_opp_team_allowed_avg_past_xdays_base_df(row, base_df, 7),
                                                            axis=1)        
    base_df["rest"] = base_df.apply(lambda row: NBA_utils.calculate_team_rest_base_df(row, base_df), axis=1)
    base_df["Opp_rest"] = base_df.apply(lambda row: NBA_utils.calculate_opp_team_rest_base_df(row, base_df), axis=1)

    base_df['win_sum'] = base_df.apply(lambda row: NBA_utils.get_team_win_sum_base_df(row, base_df, row['Team']), axis=1)
    base_df['Opp_win_sum'] = base_df.apply(lambda row: NBA_utils.get_team_win_sum_base_df(row, base_df, row['OppTeam']), axis=1)
    
    #team_win_sum_map = NBA_utils.calc_team_win_sum_base_df(base_df)
    #base_df['win_sum'] = base_df.apply(lambda row: team_win_sum_map[row['Team']], axis=1)
    #base_df['Opp_win_sum'] = base_df.apply(lambda row: team_win_sum_map[row['OppTeam']], axis=1)    

    return base_df

def test_model(model, preds, tgts):
    """
     Currently just returns MAE
    """
    error = []
    # loop through all of the predictors and calculate an mae
    for x in range(0, len(preds)):
        fcst = model.predict(preds[x].reshape(1,-1))
        diff = tgts[x]-fcst
        #print ("Forecast, actual, error: %d %d %d" % (fcst, tgts[x], diff))
        error.append(abs(diff))

    return (sum(error)/len(error))
        
def create_ML_model(base_df, target, training_start, training_end, testing_end, output_base):
    """
    """
    # Training data should only be within the provided start/end date
    training_df = base_df[((base_df['GameTime']>=training_start) &
                           (base_df['GameTime']<training_end))].reset_index(drop=True)
    (train_predictor_array, train_target_array) = make_predictor_target_arrays(training_df, target)

    # Testing data
    testing_df = base_df[((base_df['GameTime']>=training_end) &
                          (base_df['GameTime']<testing_end))].reset_index(drop=True)
    (test_predictor_array, test_target_array) = make_predictor_target_arrays(testing_df, target)
    
    print ("Length of training dataset: %d" % len(train_target_array))
    print ("Length of testing dataset: %d" % len(test_target_array))    
    
    # Fit the model
    model = RandomForestRegressor(random_state=1)
    #model = ExtraTreesRegressor(random_state=1)    
    model.fit(train_predictor_array, train_target_array)

    # Score the model over the testing dataset
    MAE = test_model(model, test_predictor_array, test_target_array)
    print ("RandomForest MAE over %d cases: %f" % (len(test_target_array), MAE))        

    ##########################################
    # Save all of the model and config info
    ##########################################
    # First save the model to a .pkl file
    model_name = output_base + ".sav"
    print ("Saving: %s" % (model_name))
    pickle.dump(model, open(model_name, 'wb'))

    # Save some info to a config ascii file
    info_name = output_base + ".info"
    print ("Saving: %s" % info_name)
    outF = open(info_name, "w")
    outLine = "Target: %s\n" % target
    outF.write(outLine)
    outLine = "Predictors: %s\n" % (",".join(PREDICTORS))
    outF.write(outLine)
    outLine = "Len of training dataset: %s\n" % (len(train_target_array))
    outF.write(outLine)
    outLine = "Model dataset ended on: %s\n" % (Tutils.epoch2tme(training_end, "%Y%m%d"))
    outF.write(outLine)        
    outLine = "Sample training_data:\n"
    outF.write(outLine)
    outLine = ",".join([str(t) for t in train_predictor_array[0]]) + "\n"
    outF.write(outLine)
    outF.close()

    return model    


def process(bball_games_dir, league, output_base, options):
    # Read all of the basketball games
    game_df = NBA_utils.read_OP_bball_dir(bball_games_dir)
    game_df['EpochDt'] = game_df.apply(lambda row: NBA_utils.get_bball_epoch_dt(row), axis=1)
    sorted_game_df = game_df.sort_values('EpochDt')

    # Split up the dataframe into something better for machine learning
    #  Time, Team, PointsScored, Home/Away
    base_df = create_base_df(sorted_game_df)

    # Add predictors we need, like the prior game score
    base_df = augment_df(base_df)

    base_df.to_csv("base_df.csv", index=False)
    
    # Create the ML model
    model_start_epoch = Tutils.tme2epoch("20171001", "%Y%m%d")
    model_end_epoch = Tutils.tme2epoch("20180110", "%Y%m%d")
    testing_end = game_df['EpochDt'].max()
    # Create models for each team
    if options.team_model:
        teams = base_df['Team'].unique().tolist()
        for tm in teams:
            team_df = base_df[base_df['Team']==tm]
            team_str = tm.replace(" ","").replace(".","")
            team_model_base = "%s_%s" % (output_base, team_str)
            team_model = create_ML_model(team_df, 'PointsScored', model_start_epoch, model_end_epoch, testing_end, team_model_base)
    elif options.autotune_model:
        model_end_epoch = time.time()
        this_model_end_epoch = Tutils.tme2epoch("20171215", "%Y%m%d")
        # Loop over each week, creating the model from start_epoch -> start of week, evaluate on that week.
        while this_model_end_epoch < model_end_epoch:
            weekly_base = "%s_%s" % (output_base, Tutils.epoch2tme(this_model_end_epoch, "%Y%m%d"))
            testing_end = this_model_end_epoch + WEEK
            print ("Creating model from %s - %s.  Evaluating from %s - %s" % (Tutils.epoch2tme(model_start_epoch, "%Y%m%d:%H%M"),
                                                                              Tutils.epoch2tme(this_model_end_epoch, "%Y%m%d:%H%M"),
                                                                              Tutils.epoch2tme(this_model_end_epoch, "%Y%m%d:%H%M"),
                                                                              Tutils.epoch2tme(testing_end, "%Y%m%d:%H%M")))
            weekly_model = create_ML_model(base_df, 'PointsScored', model_start_epoch, this_model_end_epoch, testing_end,
                                           weekly_base)
            this_model_end_epoch += WEEK
    else:
        model = create_ML_model(base_df, 'PointsScored', model_start_epoch, model_end_epoch, testing_end, output_base)            
    
def main():
    usage_str = "%prog basketball_game_dir league output_base"
    parser = OptionParser(usage = usage_str)
    parser.add_option("-t", "--team_model", action="store_true", dest="team_model", help="make models specific to each team")
    parser.add_option("-a", "--autotune_model", action="store_true", dest="autotune_model", help="makes and tests model on a weekly basis")    
        
    (options, args) = parser.parse_args()
    
    if len(args) < 3:
        parser.print_help()
        sys.exit(2)

                                  
    bball_games_dir = args[0]
    league = args[1]
    output_base = args[2]

    process(bball_games_dir, league, output_base, options)


if __name__ == "__main__":
    main()
