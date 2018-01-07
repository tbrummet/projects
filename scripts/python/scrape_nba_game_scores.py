#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import requests
import pandas as pd
import nba_py
from nba_py import game
import NBA_ABBREV_MAP
    
def process(date, out_file):
    dt = datetime.strptime(date, "%Y%m%d")
    all_abbrevs = []
    score_df = read_scores_by_date(dt)

    score_df.to_csv(out_file, index=False)
    # append this data to the csv file
    #ap_output(out_file, date, score_df)

def append_output(out_file, date, score_df):
    """
    """
    inf = open(out_file, "r+")
    header = inf.readline().rstrip("\r\n").split(',')
    print (header)    
    dt_ind = header.index("Date")
    home_team_ind = header.index("Home/Neutral")
    home_pts_ind = header.index("HomePTS")
    away_team_ind = header.index("Visitor/Neutral")
    away_pts_ind = header.index("VisitorPTS")
    for ind, row in score_df.iterrows():
        out_row = ['']*len(header)
        out_row[dt_ind] = date
        out_row[home_team_ind] = NBA_ABBREV_MAP.TEAM_ABBREV_MAP[row['HomeTeam']]
        out_row[away_team_ind] = NBA_ABBREV_MAP.TEAM_ABBREV_MAP[row['AwayTeam']]
        out_row[home_pts_ind] = str(row['HomePoints'])
        out_row[away_pts_ind] = str(row['AwayPoints'])
        out_str = ",".join(out_row)+"\n"
        inf.write(out_str)

    inf.close()

def read_scores_by_date(dt):
    bs = nba_py.Scoreboard(month=dt.month, day=dt.day, year=dt.year)    
    away_teams = []
    home_teams = []
    away_points = []
    home_points = []    
    for table in bs.json['resultSets']:
        # Get the proper table with the scores
        if table['name'] == 'LineScore':
            header = table['headers']
            team_ind = header.index("TEAM_ABBREVIATION")
            points_ind = header.index("PTS")
            game_list = table['rowSet']
            # Away team always comes first
            for g in range(0, len(game_list), 2):
                away_teams.append(game_list[g][team_ind])
                away_points.append(game_list[g][points_ind])                
                home_teams.append(game_list[g+1][team_ind])
                home_points.append(game_list[g+1][points_ind])
                    
    df = pd.DataFrame()
    df['AwayTeam'] = [NBA_ABBREV_MAP.TEAM_ABBREV_MAP[t] for t in away_teams]
    df['HomeTeam'] = [NBA_ABBREV_MAP.TEAM_ABBREV_MAP[t] for t in home_teams]
    df['AwayPoints'] = away_points
    df['HomePoints'] = home_points
    game_dt_str = "%s%02d%02d" % (dt.year, dt.month, dt.day)
    df['GameTime'] = game_dt_str
    return (df)
        
def main():
    usage_str = "%prog date output_file"
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        parser.print_help()
        sys.exit(2)

                                  
    date = args[0]
    out_file = args[1]

    process(date, out_file)


if __name__ == "__main__":
    main()
