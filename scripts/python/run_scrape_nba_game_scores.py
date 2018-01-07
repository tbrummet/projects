#!/usr/bin/env python


"""
THIS IS A SKELETON OF WHAT A NORMAL PYTHON SCRIPT SHOULD LOOK LIKE
"""

import time, os, sys
from datetime import datetime
from optparse import OptionParser
import time
import Tutils

def main():
    usage_str = "%prog"
    parser = OptionParser(usage = usage_str)
        
    (options, args) = parser.parse_args()
    
    if len(args) < 0:
        parser.print_help()
        sys.exit(2)

    cur_time = time.time()
    yesterday_time = cur_time - (3600*7) - 86400 - (cur_time%86400)
    dt = Tutils.epoch2tme(yesterday_time, "%Y%m%d")

    output_file = "C:\\Users\\Tom\\programming\\OP_basketball_games\%s_nba_scores.csv" % dt
    # RUN NBA SCRAPING
    cmd = "python C:\\Users\\Tom\\programming\\scripts\\python\\scrape_nba_game_scores.py %s %s" % (dt, output_file)
    ret = os.system(cmd)

    # Sleep for 1 minute
    time.sleep(60)

if __name__ == "__main__":
    main()
