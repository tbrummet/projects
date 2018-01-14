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
    yesterday_time = cur_time - 86400 - (cur_time%86400)
    dt = Tutils.epoch2tme(yesterday_time, "%Y%m%d")
    # RUN NBA SCRAPING
    cmd = "python C:\\Users\\Tom\\programming\\scripts\\python\\scrape_ncaa_game_scores.py %s" % (dt)
    ret = os.system(cmd)
    
    #dt_range = Tutils.gen_time_range("20171110", "20180113", "%Y%m%d", 86400)
    #for dt in dt_range:
    #    # RUN NBA SCRAPING
    #    cmd = "python C:\\Users\\Tom\\programming\\scripts\\python\\scrape_ncaa_game_scores.py %s" % dt
    #    ret = os.system(cmd)        
    #    print (dt)
    # Sleep for 1 minute
    #time.sleep(60)

if __name__ == "__main__":
    main()
