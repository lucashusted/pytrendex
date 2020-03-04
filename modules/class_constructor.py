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

class wb_gtrends:

    # Initialize pytrend
    pytrend = TrendReq(tz=300) # tz is the timezone offset, in this case EST

    # Universal parameter(s)
    cutoff = 270 - 20 # google returns max 270 values; I make it 250 just in case.
    overlap = 30 # An arbitrary length of time for the series to overlap

    def __init__(self, kw_list, geo,
                 date_start=None, date_end=None, frequency='daily'):

        # Input Arguments
        self.kw_list = kw_list
        self.geo = geo
        self.user_date_start = date_start
        self.user_date_end = date_end
        self.frequency = frequency

        # Derived Arguments
        self.benchmark, self.search_groups = self.get_benchmark()
        self.date_start, self.date_end = self.auto_dates()
        self.timechunks = self.get_timechunks()


    def make_index(self):

        # Loop through and get all the separate time frames (timechunks makes the intervals)
        for ii, dd in enumerate(self.timechunks):
            temp_trends = self.pull_timeframe(date_start=dd[0],date_end=dd[1])
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
                trends = trends.append(temp_trends.iloc[self.overlap+1:])


        if self.frequency == 'daily':
            pass
        elif self.frequency == 'weekly':
            trends = trends.reset_index()
            trends.date = trends.date.dt.to_period('W').dt.to_timestamp() # make weekly
            trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
            trends = trends.loc[trends.timecount.eq(7),:] # make sure no partial weeks
            trends = trends.groupby('date')[self.kw_list].mean()
            print('Converting to %s' %self.frequency)
        elif self.frequency == 'monthly':
            trends = trends.reset_index()
            trends.date = trends.date.dt.to_period('M').dt.to_timestamp() # make monthly
            trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
            trends = trends.loc[trends.timecount.eq(trends.date.dt.days_in_month),:]
            trends = trends.groupby('date')[self.kw_list].mean()
            print('Converting to %s' %self.frequency)
        elif self.frequency == 'quarterly':
            trends = trends.reset_index()
            trends.date = trends.date.dt.to_period('Q').dt.to_timestamp() # make qtrly
            trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
            trends = trends.loc[trends.timecount.ge(28*3),:] # minimum February 3 times
            trends = trends.groupby('date')[self.kw_list].mean()
            print('Converting to %s' %self.frequency)


        indices = pd.concat([
            trends.apply(self.normalize).sum(axis=1).to_frame('GTI (Normalized)'),
            trends.sum(axis=1).to_frame('GTI (Standard)')],axis=1).apply(self.normalize)

        indices.plot()

    def pull_timeframe(self):
        """
        This function pulls data from a set timeframe for all variables in kw_list.
        The outcome will be hourly, weekly, or monthly depending on

        Parameters
        ----------
        pytrend :
            Must be initiated with TrendReq.
            See pytrend documentation. The default is pytrend.
        kw_list :
            list
            The list of search terms (default is kw_list)
        benchmark :
            str
            The benchmark term, either blank or first word in kw_list.
            The default is benchmark.
        geo :
            str
            Country or region to run the search.
        date_start :
            str
            Date in %y-%m-%d format. The default is date_start.
        date_end :
            str, optional
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
        if self.benchmark:
            # Do the searches in batches
            # For each one initial transform and spit into dictionary of dataframes
            for idx, ss in enumerate(self.search_groups):

                # Do the search
                self.pytrend.build_payload(ss,geo=self.geo,
                                      timeframe='%s %s' %(self.date_start,
                                                          self.date_end))
                df = self.pytrend.interest_over_time()

                # Warn and stop if benchmark sucks
                if self.too_small(df[self.benchmark]):
                    raise ValueError('The benchmark has too many 0 or small values. '\
                                     'Please choose a different first search term.')
                    break

                # Get rid of partial days
                df = df.loc[df.isPartial.astype('str').eq('False'),ss]

                if idx==0:
                    trends = df
                else:
                    df = df.mul((trends[self.benchmark]/df[self.benchmark]).values,0)
                    trends = trends.join(df.drop(self.benchmark,axis=1))

        else:
            self.pytrend.build_payload(self.kw_list,geo=self.geo,
                                  timeframe='%s %s' %(self.date_start,self.date_end))
            df = self.pytrend.interest_over_time()
            trends = df.loc[df.isPartial.astype('str').eq('False'),self.kw_list]

        return trends


    def get_benchmark(self):
        # Limit on google trends searches is 5 words else need benchmark term
        if len(self.kw_list) > 5:
            benchmark = self.kw_list[0]
            search_groups = list(self.chunks(self.kw_list))
        else:
            benchmark = None
            search_groups = self.kw_list
        return benchmark, search_groups

    def auto_dates(self):
        if not self.user_date_end:
            date_end = pd.to_datetime(time.ctime()).strftime('%Y-%m-%d')
        else:
            date_end = self.user_date_end

        if not self.user_date_start:
            date_start = (pd.to_datetime(date_end) -
                          pd.Timedelta(days=self.cutoff)).strftime('%Y-%m-%d')
        else:
            date_start = self.user_date_start

        return date_start, date_end


    def get_timechunks(self):
        # if ending date was left blank, assume we want until today
        daterange = (pd.to_datetime(self.date_end) - pd.to_datetime(self.date_start)).days

        if daterange>self.cutoff:
            # see what length of time we are working with total
            # split it up into the overlapping chunks
            lst = [list(a) for a in zip(range(0,
                                              daterange+1,
                                              self.cutoff-self.overlap),
                                        range(self.cutoff,
                                              daterange+self.cutoff,
                                              self.cutoff-self.overlap))]
            # make sure that the last value lines up with our actual last value
            lst[-1][1] = daterange

            # turn it back into date strings
            for row in range(0,len(lst)):
                for column in range(0,2):
                    lst[row][column] = (pd.to_datetime(self.date_start)+
                                        pd.Timedelta(days=lst[row][column])).\
                                            strftime('%Y-%m-%d')
        else:
            lst = [[self.date_start,self.date_end]]

        return lst

    @staticmethod
    def chunks(lst, n=5):
        """Yield successive n-sized chunks from lst with benchmark first."""
        bench = lst[0]
        for i in range(1, len(lst), n-1):
            yield [bench] + lst[i:i+n-1]

    @staticmethod
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

    @staticmethod
    def normalize(x):
        return (x-x.mean())/x.std()


