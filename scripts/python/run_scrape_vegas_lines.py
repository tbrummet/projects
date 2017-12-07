#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import time

def main():
    usage_str = "%prog"
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 0:
        parser.print_help()
        sys.exit(2)


    # RUN NBA SCRAPING
    cmd = "python C:\\Users\\Tom\\programming\\scripts\\python\\scrape_vegas_lines.py NBA"
    ret = os.system(cmd)

    # Sleep for 1 minute
    time.sleep(60)
    
    # RUN NCAA SCRAPING    
    cmd = "python C:\\Users\\Tom\\programming\\scripts\\python\\scrape_vegas_lines.py NCAAB"
    ret = os.system(cmd)

if __name__ == "__main__":
    main()
