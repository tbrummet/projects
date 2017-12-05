#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import re

OUTPUT_DIR = r"C:\Users\Tom\programming\NBA_LINES"

SPORTSBOOK_LIST = ['Open', 'VI Consensus', 'Westgate', 'MGM', 'WIlliam Hill', 'Wynn',
                   'CG Technology', 'Stations', 'BetOnline']

def generate_lists(this_table):
    """
    """
    list_array = [[]]*7

    for row in this_table.findAll("tr"):
        cells = row.findAll('td')        
        states = row.findAll('th')
        # TO only extract the table body
        if len(cells)==6:
            list_array[0].append(states[0].find(text=True))            
            list_array[1].append(cells[0].find(text=True))
            list_array[2].append(cells[1].find(text=True))
            list_array[3].append(cells[2].find(text=True))
            list_array[4].append(cells[3].find(text=True))
            list_array[5].append(cells[4].find(text=True))
            list_array[6].append(cells[5].find(text=True))            

    df = pd.DataFrame(list_array[1],columns=['Number'])
    df['State/UT'] = list_array[0]
    df['Admin_Capital'] = list_array[2]
    df['Legislative_Capital'] = list_array[3]
    df['Judiciary_Capital'] = list_array[4]
    df['Year_Capital'] = list_array[5]
    df['Former_Capital'] = list_array[6]
    
    return df

def parse_PS_string(PS_string):
    """
    Gets the point spread and the value of the bet from the string
    """
    fields = PS_string.split()
    PS = -9999
    value = -9999
    try:
        PS = float(fields[0])
    except:
        PS = float(fields[0][:-1])
        if PS < 0:
            PS -= .5
        else:
            PS += .5

    # If it is an even line
    if fields[1].find("EV") != -1:
        value = 0
    else:
        value = float(fields[1])
        
    return [PS, value]
    
def parse_OU_string(OU_string):
    """
    Gets the over_under point amount and the value of the bet from the string
    """
    if OU_string.find("u") == -1 and OU_string.find("o") == -1:
        print ("WARNING: over_under_line('%s') doesn't contain an 'o' or a 'u'" % OU_string)
        return [-9999,-9999]

    fields = []
    # True/False flag based on if the spread is an over or an under
    under = True
    if OU_string.find("u") != -1:
        # This is the under spread
        fields = OU_string.split("u")
    else:
        under = False
        fields = OU_string.split("o")

    over_under = -9999
    value = -9999
    try:
        over_under = float(fields[0])
    except:
        over_under = float(fields[0][:-1])+.5
        
    if (fields[1].find("EV") != -1):
        value = 0
    else:
        value = float(fields[1])

    if under == True:
        over_under = -over_under
    return [over_under, value]

def process_odds_table(this_table, cur_time):
    print ("Processing table")

    all_entries = this_table.findAll("tr")
    # Loop through each matchup
    current_time_list = []
    home_team_list = []
    away_team_list = []
    game_time_list = []
    over_under_map = []
    point_spread_map = []
    for x in range(0, len(all_entries),2):
        data_row = all_entries[x]
        cells = data_row.findAll('td')
        #notes_row = all_entries[x+1]
        #notes_cells = notes_row.findAll('td')

        # Get the two teams that are playing        
        xml_teams = cells[0].findAll('b')
        home_team = xml_teams[0].find(text=True)
        away_team = xml_teams[1].find(text=True)
        
        # Get the match time
        xml_time = cells[0].find('span')
        game_time = xml_time.find(text=True)
        #print ("Game_time: %s Home_team: %s  Away_team: %s\n" % (game_time, home_team, away_team))
        over_under_list = []
        point_spread_list = []
        for b in range(1, len(cells)):            
            xml_bet_entry = cells[b].find('a')
            if (xml_bet_entry==None) or (len(xml_bet_entry) == 0):
                over_under_list.append([-9999,-9999])
                point_spread_list.append([-9999,-9999])
                continue
            first_string = "%s" % xml_bet_entry.contents[2]
            second_string = "%s" % xml_bet_entry.contents[4]

            # IF this is an over/under string
            if (first_string.find("u") != -1) or (first_string.find("o") != -1):
                (spread, spread_value) = parse_OU_string(first_string)
                (line, line_value) = parse_PS_string(second_string)
                
                over_under_list.append([spread, spread_value])
                point_spread_list.append([line, line_value])
            else:                
                (spread, spread_value) = parse_OU_string(second_string)
                (line, line_value) = parse_PS_string(first_string)
                
                over_under_list.append([spread, spread_value])
                point_spread_list.append([line, line_value])
        
        #print ("Over Under List")
        #print (over_under_list)
        #print ("Point Spread List")
        #print (point_spread_list)
        current_time_list.append(cur_time)
        home_team_list.append(home_team)
        away_team_list.append(away_team)
        game_time_list.append(game_time)
        over_under_map.append(over_under_list)
        point_spread_map.append(point_spread_list)
        #print (cells[1])

    # Convert the data to a pandas Dataframe
    df = pd.DataFrame()
    df['Time'] = current_time_list
    df['Home_Team'] = home_team_list
    df['Away_Team'] = away_team_list
    df['Game_Time'] = game_time_list
    for s in range(0, len(SPORTSBOOK_LIST)):
        OU_key = "Over_under_%s" % SPORTSBOOK_LIST[s]        
        df[OU_key] = [v[s][0] for v in over_under_map]
        PS_key = "Point_spread_%s" % SPORTSBOOK_LIST[s]
        df[PS_key] = [v[s][0] for v in point_spread_map]
    #df['Over_Unders'] = over_under_map
    #df['Point_spreads'] = point_spread_map

    today_date = time.strftime("%Y%m%d", time.localtime(cur_time))
    output_file = "%s/vegas_bets.%s.csv" % (OUTPUT_DIR, today_date)
    print ("Writing: %s" % output_file)
    df.to_csv(output_file)
       
    
def process(options):
    # Get current time
    cur_time = time.time()
    url = "http://www.vegasinsider.com/nba/odds/las-vegas/"
    
    # Read the wiki page    
    page = urllib.request.urlopen(url)

    # Convert it to beautifulSoup format
    soup = BeautifulSoup(page,"lxml")

    # For veiwing it in a better format    
    if options.prettyOut:
        with open(options.prettyOut, 'w', encoding='utf-8') as f:
            print(soup.prettify(),file=f)

    # print a specific html tag
    #print (soup.title)

    tables_list = soup.find_all('table')
    #print (len(tables_list))
    #for x in range(0, len(tables_list)):
    #    print ("-------------------------- %d ---------------------------------" % len(tables_list[x]))
    #    print (tables_list[x])
    #sys.exit()

    # Assume the Odds table is the largest one
    table_len_list = [len(tables_list[x]) for x in range(0, len(tables_list))]
    our_table_ind = table_len_list.index(max(table_len_list))

    process_odds_table(tables_list[our_table_ind], cur_time)


    #our_table = soup.find('table', class_="frodds-data-tb1")
    #print (our_table)
    
    
def main():
    usage_str = "%prog"
    usage_str = "%s\n Default behavior is to output the daily bet information to a csv file under %s" % (usage_str, OUTPUT_DIR)
    parser = OptionParser(usage = usage_str)
    parser.add_option("-p", "--pretty_output_file", dest="prettyOut", help="Write the raw xml file to this output asc file")
    
        
    (options, args) = parser.parse_args()
    
    if len(args) < 0:
        parser.print_help()
        sys.exit(2)

    
    process(options)


if __name__ == "__main__":
    main()
