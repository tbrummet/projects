#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import urllib.request
from bs4 import BeautifulSoup

def process():
    wiki = "https://en.wikipedia.org/wiki/List_of_state_and_union_territory_capitals_in_India"

    # Read the wiki page
    page = urllib.request.urlopen(wiki)

    # Convert it to beautifulSoup format
    soup = BeautifulSoup(page,"lxml")

    # FOr veiwing it in a better format
    #print (soup.prettify())

    # print a specific html tag
    #print (soup.title)

    # Print only the string of the html tag
    print (soup.title.string)

    # Gets all of the links available on the webpage
    link_list = soup.find_all("a")

    # Get all of the tables
    tables_list = soup.find_all('table')

    # Get the specific table you want
    our_table=soup.find('table', class_='wikitable sortable plainrowheaders')
    
    print ("Number of elements in 'wikitable sortable plainrowheaders': %d" %
           len(our_table))
    
def main():
    usage_str = "%prog"
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 0:
        parser.print_help()
        sys.exit(2)

                                  
    process()


if __name__ == "__main__":
    main()
