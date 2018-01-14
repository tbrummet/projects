#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
#import urllib.request
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
import Tutils
import numpy as np

OUTPUT_DIR = r"C:\Users\Tom\programming\OP_NCAA_games"

def process_odds_table(this_table):
    #print ("Processing table")

    all_entries = this_table.findAll("tr")

    away_ind = 1
    away_row = all_entries[away_ind]
    away_cells = away_row.findAll('td')
    away_cl = away_cells[0].find('a')
    away_team = away_cl.find(text=True)
    away_points = np.nan
    for j in range(1, len(away_cells)):
        if away_cells[j].has_attr('class') and away_cells[j]["class"]==['final','score']:
            away_points=away_cells[j].find(text=True)
    home_ind = 2
    home_row = all_entries[home_ind]
    home_cells = home_row.findAll('td')
    home_cl = home_cells[0].find('a')
    home_team = home_cl.find(text=True)
    home_points = np.nan
    for j in range(0, len(home_cells)):
        if home_cells[j].has_attr('class') and home_cells[j]["class"]==['final','score']:
            home_points = home_cells[j].find(text=True)

    return (away_team, home_team, away_points, home_points)

    
def process(date, options):
    # Get current time
    url = "http://www.ncaa.com/scoreboard/basketball-men/d1/%s/%s/%s" % (date[:4], date[4:6],
                                                                         date[6:])
        
    lg_str = "Reading %s" % (url)
    logging.info(lg_str)
    # Read the wiki page
    #page = urllib.request.urlopen(url)
    page = requests.get(url)

    lg_str = "Finished reading url"
    logging.info(lg_str)
    
    # Convert it to beautifulSoup format
    soup = BeautifulSoup(page.content, "html.parser")

    # For veiwing it in a better format    
    if options.prettyOut:
        with open(options.prettyOut, 'w', encoding='utf-8') as f:
            print(soup.prettify(),file=f)

    # print a specific html tag
    #print (soup.title)
    logging.info("Processing odds table")
    
    tables_list = soup.find_all('table')
    entries_list = []
    for x in range(0, len(tables_list)):
        (info_list) = process_odds_table(tables_list[x])
        entries_list.append(info_list)

    df = pd.DataFrame()
    df["AwayTeam"] = [e[0] for e in entries_list]
    df["HomeTeam"] = [e[1] for e in entries_list]
    df["AwayPoints"] = [e[2] for e in entries_list]
    df["HomePoints"] = [e[3] for e in entries_list]
    df["GameTime"] = date

    output_file = "%s\%s_ncaa_scores.csv" % (OUTPUT_DIR, date)
    lg_str = "Writing: %s" % output_file
    logging.info(lg_str)
    df.to_csv(output_file, index=False)

    logging.info("Exit\n")
    #our_table = soup.find('table', class_="frodds-data-tb1")
    #print (our_table)
    
    
def main():
    usage_str = "%prog date"
    usage_str = "%s\n\tdate : YYYYmmdd" % usage_str
    parser = OptionParser(usage = usage_str)
    parser.add_option("-p", "--pretty_output_file", dest="prettyOut", help="Write the raw xml file to this output asc file")
    
        
    (options, args) = parser.parse_args()
            
    if len(args) < 1:
        parser.print_help()
        sys.exit(2)    
        
    date = args[0]    

    log_file = "C:/Users/Tom/programming/log/scrape_ncaa_game.%s.log" % (time.strftime("%Y%m%d"))
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S ')

    logging.info("Starting")        
    
    process(date, options)


if __name__ == "__main__":
    main()
