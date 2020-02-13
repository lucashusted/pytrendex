#%% Setup
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Imports and Setup
# =============================================================================

# Standard data analysis
import pandas as pd
#import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import time

# An unofficial google trends API
from pytrends.request import TrendReq

# Defaults
kw_list     = ['Beyonce','Kesha','Justin Beiber','Britney Spears','JLo','Shakira']
date_start  = '2016-01-01'
date_end    = '' # Leave blank for up until today
frequency   = 'hourly' # weekly, monthly, daily, hourly are options


# Initialize pytrend
pytrend = TrendReq(tz=300) # tz is the timezone offset, in this case EST


# =============================================================================
# Variable Definitions
# =============================================================================

# Universal parameters
cutoff = 270 # this is the cutoff in google trends from day -> week and week -> month

# Limit on google trends searches is 5 words, need to have benchmark if exceeds this
if len(kw_list)//5 >= 1:
    benchmark = kw_list[0]
else:
    benchmark = None

if not date_end:
    date_end = pd.to_datetime(time.ctime()).strftime('%Y-%m-%d')

# We need to check frequency against the input
daterange = (pd.to_datetime(date_end) - pd.to_datetime(date_start)).days
weekrange = daterange/7

# #TODO: Loop over possibilities
#Discovery made: if it is <= 270 days then it spits out daily, if it is < 270 weeks, then it spits out weekly
# if daterange//52 >= 270 and (frequency == 'daily' or frequency == 'hourly'):
#     raise ValueError('It is not currently possible to run daily/hourly '\
#                      'frequency with a timerange exceeding 5 years.')

# if daterange//52 >= 270 and (frequency == 'daily' or frequency == 'hourly'):
#     raise ValueError('It is not currently possible to run daily/hourly '\
#                      'frequency with a timerange exceeding 5 years.')
# elif daterange//52 >= 270 and frequency == 'monthly':
#     print('cool')
#     # execute code as it is. no need to partition
# elif daterange//52 >= 270 and frequency == 'weekly':
#     print('nipples')
#     # run overlapping code of 5 year lengths

# elif daterange//365 < 5 and frequency == 'monthly':
#     print('what')
# elif daterange//365 < 5 and frequency == 'weekly':
#     # execute code as is. no need to partition
# elif daterange//365 < 5 and frequency == 'weekly':


# =============================================================================
# Helper Functions
# =============================================================================
def chunks(benchmark=benchmark, lst=kw_list[1:], n=4):
    """Yield successive n-sized chunks from lst with benchmark first."""
    for i in range(0, len(lst), n):
        yield [benchmark] + lst[i:i + n]

def too_small(x,tol=.1):
    """
    Checks whether a pd.Series has any 0s or "too many" ones
    Inputs:
        x is pd.Series
        tol is the percentage of ones allowable (default=10%)
    Returns:
        True/False
    """

    num_0 = x.eq(0).sum()
    num_1 = x.eq(1).sum()/x.count()

    if num_0 > 0 or num_1>tol:
        return True
    else:
        return False


#%% The loop
# =============================================================================
# Looping through kw for creating of >5 word index (if necessary)
# =============================================================================
if benchmark:
    # Do the searches in batches
    search_groups = list(chunks())
    # For each one initial transform and spit into dictionary of dataframes
    for idx, ss in enumerate(search_groups):

        # Do the search
        pytrend.build_payload(ss,geo='US',timeframe='%s %s' %(date_start,date_end))
        df = pytrend.interest_over_time()

        # Warn and stop if benchmark sucks
        if too_small(df[benchmark]):
            raise ValueError('The benchmark has too many 0 or small values. '\
                             'Please choose a different first search term.')
            break

        # Get rid of partial weeks
        df = df.loc[df.isPartial.eq('False'),ss] #encoded as string not bool

        if idx==0:
            trends = df
        else:
            df = df.mul(trends[benchmark]/df[benchmark],0)
            trends = trends.join(df.drop(benchmark,axis=1))

else:
    pytrend.build_payload(ss,geo='US',timeframe='%s %s' %(date_start,date_end))
    trends = pytrend.interest_over_time()


