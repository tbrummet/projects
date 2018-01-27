#!/usr/bin/python
# Filename: MODEL_utils.py
#  Some useful functions, put together by Tom Brummet

# ============================================================================== #
#                                                                                #
#   (c) Copyright, 2013 University Corporation for Atmospheric Research (UCAR).  #
#       All rights reserved.                                                     #
#                                                                                #
#       File: $RCSfile: fileheader,v $Tutils.py                                  #
#       Version: $Revision: 1.0 $  Dated: $Date: 2013/10/10 14:44:18 $           #
#                                                                                #
# ============================================================================== #

from datetime import datetime
import sys
import os
import time
import calendar
import pandas as pd
import numpy as np
import Tutils

def read_predictors_from_info(info_lines):
    preds = []
    for line in info_lines:
        if line.startswith("Predictors:"):
            poss_preds = line.split(":")[1]
            preds = poss_preds.replace(" ","").rstrip("\r\n").split(",")
    return preds

def read_end_date_from_info(info_lines):
    for line in info_lines:
        if line.startswith("Model dataset ended on:"):
            end_date = line.replace(" ", "").rstrip("\r\n").split(":")[1]
            return Tutils.tme2epoch(end_date, "%Y%m%d")
    print ("Error parsing the model end date")
    sys.exit()
