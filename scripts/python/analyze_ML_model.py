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
from sklearn import linear_model
import pandas as pd

PREDICTORS = ['Prior_1_game_score', 'Prior_3game_avg', 'HomeAway']
TARGET = ['PointsScored']

def get_epoch_dt(row):
    game_date_str = str(int(row['GameTime']))
    return Tutils.tme2epoch(game_date_str, "%Y%m%d")

def create_base_df(sorted_game_df):
    # Iterate through the dataframe and make the data that I need
    #    Try 1:
    #       GameTime,Team,PointsScored
    game_time_list = []
    game_time_str_list = []
    teams_list = []
    points_list = []
    home_away_list = []  # 1 = home, 0 = away
    for ind, row in sorted_game_df.iterrows():
        # For each row, need to make 2 rows, one for home and 1 for away team
        game_time_list.append(row["EpochDt"])
        game_time_list.append(row["EpochDt"])
        game_time_str_list.append(row["GameTime"])
        game_time_str_list.append(row["GameTime"])        
        teams_list.append(row["AwayTeam"])
        teams_list.append(row["HomeTeam"])
        points_list.append(row["AwayPoints"])
        points_list.append(row["HomePoints"])
        home_away_list.append(0)
        home_away_list.append(1)

    master_df = pd.DataFrame(columns=["GameTime","GameTimeStr","Team","PointsScored"])
    master_df["GameTime"] = game_time_list
    master_df["GameTimeStr"] = game_time_str_list
    master_df["Team"] = teams_list
    master_df["PointsScored"] = points_list
    master_df["HomeAway"] = home_away_list
    return master_df

def augment_df(base_df):
    """
    """
    # Add columns that I think will be helpful
    #   Prior 3 games and rest inbetween each one
    base_df["Prior_1_game_score"] = base_df.apply(lambda row: NBA_utils.get_prior_score(row, base_df, 1), axis=1)
    base_df["Prior_2_game_score"] = base_df.apply(lambda row: NBA_utils.get_prior_score(row, base_df, 2), axis=1)
    base_df["Prior_3_game_score"] = base_df.apply(lambda row: NBA_utils.get_prior_score(row, base_df, 3), axis=1)
    base_df["Prior_3game_avg"] = base_df.apply(lambda row: NBA_utils.get_prior_game_avg(row, base_df, 3), axis=1)
    return base_df

def make_predictor_target_arrays(base_df):
    """
    """
    # First, subset the dataframe to only rows where all of the necessary vars are non-missing
    use_df = base_df[PREDICTORS+TARGET].dropna()
    target_array = use_df[TARGET].values
    predictor_array = use_df[PREDICTORS].values

    return (predictor_array, target_array)


def create_model(dataset):
    (predictor_array, target_array) = make_predictor_target_arrays(dataset)
    model = linear_model.LinearRegression()
    model.fit(predictor_array, target_array.ravel())
    return model

def return_modeled_points(base_df, row_team, dt):
    this_df = base_df[((base_df['Team']==row_team) &
                       (base_df['GameTime']==dt))]
    if len(this_df) == 0:
        return np.nan
    elif pd.isnull(this_df['ModeledScore'].iloc[0]):
        return np.nan
    else:
        return (this_df['ModeledScore'].iloc[0])

def train_test_verify_model(game_df, testing_start_date):
    """
    """
    # Sort the dataframe, then split up the games into separate rows per team
    sorted_game_df = game_df.sort_values('EpochDt')    
    base_df = create_base_df(sorted_game_df)
    
    # Add important fields like prior game points scored
    base_df = augment_df(base_df)

    #Loop the days, train and test the model
    start_epoch = Tutils.tme2epoch(testing_start_date, "%Y%m%d")
    initial_training_data = base_df[base_df["GameTime"]<start_epoch]
    analysis_data = base_df[base_df["GameTime"]>=start_epoch]

    # Loop through each row of the analysis data
    running_training_dataset = initial_training_data
    # List should be all missing for the initial training dataset
    predicted_score_list = [np.nan]*len(initial_training_data)

    # Loop through analysis data and run the model to get the score
    for ind, row in analysis_data.iterrows():
        model = create_model(running_training_dataset)
        predicts = row[PREDICTORS].values
        predicted_score = model.predict(predicts.reshape(1,-1))
        predicted_score_list.append(predicted_score[0])
        # Add this row to the training dataset
        running_training_dataset = running_training_dataset.append(row).reset_index(drop=True)
        
    base_df['ModeledScore']=predicted_score_list
    base_df.to_csv("base_df.csv")
    #
    # Add the modeled score back to the game_df
    #        
    game_df['modeledHomePoints'] = game_df.apply(lambda row: return_modeled_points(base_df, row['HomeTeam'], row['EpochDt']),
                                                 axis=1)

    
    game_df['modeledAwayPoints'] = game_df.apply(lambda row: return_modeled_points(base_df, row['AwayTeam'], row['EpochDt']),
                                                 axis=1)
    
    #game_df.to_csv("game_df.csv")
    #all_info = NBA_utils.print_threshold_counts('modeledHomePoints', 'modeledAwayPoints', 2, game_df, 'modeled')
    #all_info = NBA_utils.print_threshold_counts('modeledHomePoints', 'modeledAwayPoints', 4, game_df, 'modeled')
    #all_info = NBA_utils.print_threshold_counts('modeledHomePoints', 'modeledAwayPoints', 6, game_df, 'modeled')
    #all_info = NBA_utils.print_threshold_counts('modeledHomePoints', 'modeledAwayPoints', 8, game_df, 'modeled')
    #all_info = NBA_utils.print_threshold_counts('modeledHomePoints', 'modeledAwayPoints', 10, game_df, 'modeled')    

    
    

def process(game_dir, odds_dir, odds_base, testing_start_date):
    """
    """
    #
    # Read the basketball games and add the epoch dt
    #
    game_df = NBA_utils.read_OP_bball_dir(game_dir)
    game_df['EpochDt'] = game_df.apply(lambda row: get_epoch_dt(row), axis=1)
    # Add remapped home and away team names for matching from odds -> game
    game_df['RemappedAwayTeam'] = game_df.apply(lambda row: NBA_utils.remap_team_name(row['AwayTeam']),
                                                axis=1)
    game_df['RemappedHomeTeam'] = game_df.apply(lambda row: NBA_utils.remap_team_name(row['HomeTeam']),
                                                axis=1)

    #
    # Read all of the odds files and add the game date
    #
    odds_df = NBA_utils.read_odds_dir(odds_dir, odds_base)
    NBA_utils.add_odds_game_date(odds_df)
    
    #
    # Add the predicted_scores and predicted_over_under spreads to the game df
    #
    NBA_utils.add_odds(game_df, odds_df)

    #
    # Train test and verify the model
    #
    train_test_verify_model(game_df, testing_start_date)
    

def main():
    usage_str = "%prog basketball_game_dir odds_dir file_base testing_start_date"
    usage_str = "%s\n\t basketball_game_dir : dir containing csv file containing final scores of the games" % usage_str
    usage_str = "%s\n\t odds_dir : directory with dated subdirs containing csv files of the odds" % usage_str
    usage_str = "%s\n\t file_base : basename of files to grab" % usage_str
    usage_str = "%s\n\t testing_start_date : date to start the testing (YYYYmmdd)" % usage_str        
    
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 4:
        parser.print_help()
        sys.exit(2)

                                  
    game_dir = args[0]
    odds_dir = args[1]
    odds_base = args[2]
    testing_start_date = args[3]


    process(game_dir, odds_dir, odds_base, testing_start_date)


if __name__ == "__main__":
    main()
