#%% Setup
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Imports
# =============================================================================

# Standard data analysis
import pandas as pd
import seaborn as sns; sns.set()
import time

# An unofficial google trends API
from pytrends.request import TrendReq

# =============================================================================
# Defaults (To Be Changed)
# =============================================================================

kw_list     = ['Flu','Epidemic','Pandemic','Outbreak','Disease','Sickness']
date_start  = '2017-10-01'
date_end    = '' # Leave blank for up until today
frequency   = 'daily' # daily, weekly, monthly, quarterly
geo         = 'US'


# =============================================================================
# Setup (Should Usually Not Be Changed)
# =============================================================================

# Initialize pytrend
pytrend = TrendReq(tz=300) # tz is the timezone offset, in this case EST

# Universal parameter(s)
cutoff = 270 - 20 # google returns max 270 values; I make it 250 just in case.
overlap = 30 # An arbitrary length of time for the series to overlap


# Limit on google trends searches is 5 words, need benchmark term if exceeds this
if len(kw_list)//5 >= 1:
    benchmark = kw_list[0]
    print('Running Search with Benchmark as %s' %benchmark)
else:
    benchmark = None
    print('Running Search with no benchmark necessary')


# =============================================================================
# Helper Functions
# =============================================================================
def chunks(lst, benchmark, n=4):
    """Yield successive n-sized chunks from lst with benchmark first."""
    for i in range(0, len(lst), n):
        yield [benchmark] + lst[i:i + n]


def timechunks(date_start=date_start, date_end=date_end,
               overlap=overlap, stepsize=cutoff):
    # if ending date was left blank, assume we want until today
    if not date_end:
        date_end = pd.to_datetime(time.ctime()).strftime('%Y-%m-%d')
    daterange = (pd.to_datetime(date_end) - pd.to_datetime(date_start)).days

    if daterange>stepsize:
        # see what length of time we are working with total
        # split it up into the overlapping chunks
        lst = [list(a) for a in zip(range(0,
                                          daterange+1,
                                          stepsize-overlap),
                                    range(stepsize,
                                          daterange+stepsize,
                                          stepsize-overlap))]
        # make sure that the last value lines up with our actual last value
        lst[-1][1] = daterange

        # turn it back into date strings
        for row in range(0,len(lst)):
            for column in range(0,2):
                lst[row][column] = (pd.to_datetime(date_start)+
                                    pd.Timedelta(days=lst[row][column])).strftime(
                                        '%Y-%m-%d')
    else:
        lst = [[date_start,date_end]]

    return lst


def too_small(x,tol=.2):
    """
    Checks whether a pd.Series has any 0s or "too many" ones
    Inputs:
        x is pd.Series
        tol is the percentage of ones allowable (default=20%)
    Returns:
        True/False
    """
    num_0 = x.eq(0).sum()
    num_1 = x.eq(1).sum()/x.count()

    if num_0 > 0 or num_1>tol:
        return True
    else:
        return False

def normalize(x):
    return (x-x.mean())/x.std()


def pull_timeframe(pytrend=pytrend, kw_list=kw_list, benchmark=benchmark,
                   geo=geo, date_start=date_start, date_end=date_end):
    """
    This function pulls data from a set timeframe for all variables in kw_list.
    The outcome will be hourly, weekly, or monthly depending on

    Parameters
    ----------
    pytrend : Must be initiated with TrendReq.
        See pytrend documentation. The default is pytrend.
    kw_list : list
        The list of search terms (default is kw_list)
    benchmark : str
        The benchmark term, either blank or first word in kw_list.
        The default is benchmark.
    geo : str
        Country or region to run the search.
    date_start : str
        Date in %y-%m-%d format. The default is date_start.
    date_end : str, optional
        Date in %y-%m-%d format. The default is date_end.

    Raises
    ------
    ValueError
        If the benchmark term has too many 0 values, then this will scale index
        poorly, so the function will kill if that is the case, and you need to
        change the benchmark term (trail and error necessary).

    Returns
    -------
    A dataframe of the index

    """
    if benchmark:
        # Do the searches in batches
        search_groups = list(chunks(lst=kw_list[1:],benchmark=benchmark))
        # For each one initial transform and spit into dictionary of dataframes
        for idx, ss in enumerate(search_groups):

            # Do the search
            pytrend.build_payload(ss,geo=geo,
                                  timeframe='%s %s' %(date_start,date_end))
            df = pytrend.interest_over_time()

            # Warn and stop if benchmark sucks
            if too_small(df[benchmark]):
                raise ValueError('The benchmark has too many 0 or small values. '\
                                 'Please choose a different first search term.')
                break

            # Get rid of partial days
            df = df.loc[df.isPartial.astype('str').eq('False'),ss]

            if idx==0:
                trends = df
            else:
                df = df.mul((trends[benchmark]/df[benchmark]).values,0)
                trends = trends.join(df.drop(benchmark,axis=1))

    else:
        pytrend.build_payload(kw_list,geo=geo,
                              timeframe='%s %s' %(date_start,date_end))
        df = pytrend.interest_over_time()
        trends = df.loc[df.isPartial.astype('str').eq('False'),kw_list]

    return trends


#%% Making the Index

# =============================================================================
# Looping Through TimeFrames
# =============================================================================
# Loop through and get all the separate time frames (timechunks makes the intervals)
for ii, dd in enumerate(timechunks()):
    temp_trends = pull_timeframe(date_start=dd[0],date_end=dd[1])
    if ii==0:
        trends = temp_trends
    else:
        # Calculate the means of the overlapping part
        meanadj = trends.join(temp_trends,how='inner',
                              lsuffix='_1',rsuffix='_2').mean()
        for jj in temp_trends.columns:
            # adjust the following parts to have the same overlap mean
            temp_trends.loc[:,jj] = temp_trends.loc[:,jj].values*\
                (meanadj['%s_1' %jj]/meanadj['%s_2' %jj])

        # append the new part
        trends = trends.append(temp_trends.iloc[overlap+1:])


if frequency == 'daily':
    pass
elif frequency == 'weekly':
    trends = trends.reset_index()
    trends.date = trends.date.dt.to_period('W').dt.to_timestamp() # make weekly
    trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
    trends = trends.loc[trends.timecount.eq(7),:] # make sure no partial weeks
    trends = trends.groupby('date')[kw_list].mean()
    print('Converting to %s' %frequency)
elif frequency == 'monthly':
    trends = trends.reset_index()
    trends.date = trends.date.dt.to_period('M').dt.to_timestamp() # make monthly
    trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
    trends = trends.loc[trends.timecount.eq(trends.date.dt.days_in_month),:]
    trends = trends.groupby('date')[kw_list].mean()
    print('Converting to %s' %frequency)
elif frequency == 'quarterly':
    trends = trends.reset_index()
    trends.date = trends.date.dt.to_period('Q').dt.to_timestamp() # make monthly
    trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
    trends = trends.loc[trends.timecount.ge(28*3),:] # minimum February 3 times
    trends = trends.groupby('date')[kw_list].mean()
    print('Converting to %s' %frequency)


indices = pd.concat([
    trends.apply(normalize).sum(axis=1).to_frame('GTI (Normalized)'),
    trends.sum(axis=1).to_frame('GTI (Standard)')],axis=1).apply(normalize)

indices.plot()


