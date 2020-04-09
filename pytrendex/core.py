#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Imports
# =============================================================================
# Standard data analysis
import pandas as pd
from numpy.random import random as randn
import time
from statsmodels.api import tsa

# An unofficial google trends API
from pytrends.request import TrendReq

# This is for docstrings and representations of the indices
from io import StringIO
from pandas._config import get_option
from pandas.io.formats import console

class Trendex:
    """
    This class makes an index utilizing Google Trends from keywords.

    Parameters
    ----------
    kw_list:  list
        The list of keywords that will be searched. If larger than 5, will create
        benchmark term from the first term in the list.

    geo: str
        The country or place the search is conducted in, see Trends documentation.

    lang: str, options are currently 'en' for english and 'es' for spanish
        The language that the kw list is (required for optimal benchmark selection).

    date_start: str, optional
        The data where the index starts in format: 'yyyy-mm-dd',
        if none provided, then does it at the cutoff days before the date end.

    date_end: str, optional
        The data where the index ends in format: 'yyyy-mm-dd',
        if none provided, then defaults to current day.

    frequency: str, optional
        The frequency of the index. Note that the index always pulls daily data,
        so collapsing into larger time-frames is done by averages ex-post.

    gen_index: Binary, optional
        If true, then go ahead and instantiate class to generate index.
        Default is True.

    plot: boolean, optional
        If True, and make_index is True, then it plots index. Default is true.

    kw_list_split: boolean, optional
        If True then the max length for kw_list is 20 terms; after that it will
        split the search by using the "+" option for search terms (which acts
        as an "or" operator for google trends). Highly recommended to keep load down.

    benchmark_select: boolean, optional
        If True then optimally search over timeframe for best benchmark phrase, see
        documentation for that function for description of how this is done.
        If False, then the benchmark will be the first term in the kw_list.

    slowdown: boolean, optional
        If True then include time.sleep() at key moments to slow down the index.
        Currently defaults to random intervals of mean 5 or 7 seconds depending on
        where in the code. Remove this at your own peril (Google lockout).

    seasonal_adjust: boolean, optional (default = True)
        If True, then seasonally adjust the series (recommended). Seasonally
        adjusted trends are always constructed and saved in trends_sa,
        but this incorporates them into the index that is automatically constructed.

    sa_method: str, optional (default = 'trends')
        Three methods are acceptable: 'trends' or 'index' or 'both'.
        The trends method seasonally adjusts each trend separately (before adding).
        The index method seasonally adjusts only the final series.
        The both method seasonally adjusts separately and the final index.




    Returns (back to class instance)
    -------
    self.gti: Series
        This is the normalized indexes made from the underlying data. It is
        the main thing returned from this function.

    self.trends: Dataframe
        It is the adjusted and combined series for each term searched.
        You could use this to plot individual keywords in the index.
        Will differ from raw_trends_adjusted if frequency is changed from daily.

    self.trends_sa: Dataframe
        It is the trends dataframe where each trend has been seasonally adjusted.

    self.raw_trends_adjusted: Dictionary
        These are the adjusted (using overlapping timeframes) raw results
        for each term. Index of dictionary corresponds to index of timechunks.
        Could differ from trends if frequency is changed from daily.

    self.raw_trends: Dictionary
        These are the unadjusted raw results for each term.
        Note: Adjustment has still been made by the benchmark term for
        searches exceeding 5 terms.

    self.adjustment_factors: Series
        Returns the adjustment factors used on each overlapping segment.
        [term]_1 is the mean of the term in the earlier segment.
        [term]_2 is the mean of the term in the later segment.
        The adjustment is [term]_1/[term_2] * segment_2
        Note: means for each segment are bounded from below by 1, so that
        we do not seriously alter indices.

    """
    # Initialize pytrend
    pytrend = TrendReq(tz=300) # tz is the timezone offset, in this case EST

    # Universal parameter(s)
    cutoff = 270 - 20 # google returns max 270 values; I make it 250 just in case.
    overlap = 30 # An arbitrary length of time for the series to overlap
    kw_limit = 20 # Default is to break kw_list into chunks with "+" operator

    def __init__(self, kw_list, geo, lang, date_start=None, date_end=None,
                 frequency='daily', gen_index=True, plot=True,
                 kw_list_split=True, benchmark_select=True, slowdown=True,
                 seasonal_adjust=True, sa_method='trends'):

        # Input Arguments
        self.user_kw_list = kw_list.copy()
        self.geo = geo
        self.lang = lang
        self.user_date_start = date_start
        self.user_date_end = date_end
        self.frequency = frequency
        self.sa_method = sa_method
        self.seasonal = seasonal_adjust
        self.slowdown = slowdown
        self.benchmark_select = benchmark_select

        # Derived Arguments
        if len(kw_list)>self.kw_limit and kw_list_split:
            self.kw_list = self.combine_kw_list(kw_list)
        else:
            self.kw_list = kw_list
        self.date_start, self.date_end = self.auto_dates()
        self.benchmark, self.search_groups = self.get_benchmark()

        self.timechunks = self.get_timechunks()

        # Initialized None Arguments For make_index
        self.raw_trends = None
        self.adjustment_factors = None
        self.raw_trends = None
        self.raw_trends_adjusted = None
        self.trends = None
        self.trends_sa = None
        self.gti = None


        # Make the Index, unless False:
        if gen_index:
            self.make_index(plot=plot)

    def __repr__(self) -> str:

        # Return info on how to generate indices
        if self.gti is None:
            result = 'An instantiation of WBTrends Class. '\
                'Run make_index() to get result'
            return result


        # Otherwise return a string representation for indices attribute.
        df = self.gti
        buf = StringIO("")
        if df._info_repr():
            df.info(buf=buf)
            return buf.getvalue()

        max_rows = get_option("display.max_rows")
        min_rows = get_option("display.min_rows")
        max_cols = get_option("display.max_columns")
        max_colwidth = get_option("display.max_colwidth")
        show_dimensions = get_option("display.show_dimensions")
        if get_option("display.expand_frame_repr"):
            width, _ = console.get_console_size()
        else:
            width = None
        df.to_string(
            buf=buf,
            max_rows=max_rows,
            min_rows=min_rows,
            max_cols=max_cols,
            line_width=width,
            max_colwidth=max_colwidth,
            show_dimensions=show_dimensions,
        )

        return '\n'.join(['The Calculated Index (stored in object.gti):'
                          ,buf.getvalue()])

    def make_index(self,plot=True):
        """
        This is the main function to generate the index. It takes the class instance
        and returns the index(es). Along the way it saves several useful objects.

        Parameters
        ----------
        self: Instance of Class.
            You must instantiate the class in a valid way to run this function.

        plot: Binary, optional
            If you put True then will plot index. The default is True.

        Returns (back to class instance)
        -------
        self.gti: Dataframe
            This is the normalized indexes made from the underlying data. It is
            the main thing returned from this function.
            It also is returned to self.gti.

        self.trends: Dataframe
            It is the adjusted and combined series for each term searched.
            You could use this to plot individual keywords in the index.

        self.raw_trends_adjusted: Dictionary
            These are the adjusted (using overlapping timeframes) raw results
            for each term. Index of dictionary corresponds to index of timechunks.

        self.raw_trends: Dictionary
            These are the unadjusted raw results for each term.
            Note: Adjustment has still been made by the benchmark term for
            searches exceeding 5 terms.

        self.adjustment_factors: Series
            Returns the adjustment factors used on each overlapping segment.
            [term]_1 is the mean of the term in the earlier segment.
            [term]_2 is the mean of the term in the later segment.
            The adjustment is [term]_1/[term_2] * segment_2
            Note: means for each segment are bounded from below by 1, so that
            we do not seriously alter indices.

        """
        # Initialize a few things that will be stored as a result of this
        self.raw_trends = {}
        self.adjustment_factors = {}
        # Loop through and get all the separate time frames (timechunks makes the intervals)
        for ii, dd in enumerate(self.timechunks):
            if self.slowdown:
                time.sleep(round(randn()*6+2,2)) # sleep it so no timeout
            # iterate through and pull the timeframes
            temp_trends = self.pull_timeframe(date_start=dd[0],date_end=dd[1])
            self.raw_trends[ii] = temp_trends
            if ii==0:
                trends = temp_trends
            else:
                # Calculate the means of the overlapping part
                meanadj = trends.join(temp_trends,how='inner',
                                      lsuffix='_1',rsuffix='_2').mean()

                # make it so that the minimum is 1 when we do this overlap
                meanadj = meanadj.apply(lambda x: 1 if x<1 else x)

                # save them too so we can recover them if needed
                self.adjustment_factors[ii] = meanadj

                for jj in temp_trends.columns:
                    # adjust the following parts to have the same overlap mean
                    temp_trends.loc[:,jj] = temp_trends.loc[:,jj].values*\
                        (meanadj['%s_1' %jj]/meanadj['%s_2' %jj])

                # append the new part
                trends = trends.append(temp_trends.iloc[self.overlap+1:])

        # Save the adjusted trends too
        self.raw_trends_adjusted = trends

        if self.frequency == 'daily':
            pass
        elif self.frequency == 'weekly':
            trends = trends.reset_index()
            trends.date = trends.date.dt.to_period('W').dt.to_timestamp() # make weekly
            trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
            trends = trends.loc[trends.timecount.eq(7),:] # make sure no partial weeks
            trends = trends.groupby('date')[self.kw_list].mean()
        elif self.frequency == 'monthly':
            trends = trends.reset_index()
            trends.date = trends.date.dt.to_period('M').dt.to_timestamp() # make monthly
            trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
            trends = trends.loc[trends.timecount.eq(trends.date.dt.days_in_month),:]
            trends = trends.groupby('date')[self.kw_list].mean()
        elif self.frequency == 'quarterly':
            trends = trends.reset_index()
            trends.date = trends.date.dt.to_period('Q').dt.to_timestamp() # make qtrly
            trends.loc[:,'timecount'] = trends.groupby('date')['date'].transform('count')
            trends = trends.loc[trends.timecount.ge(28*3),:] # minimum February 3 times
            trends = trends.groupby('date')[self.kw_list].mean()

        # Save also the collapsed trend series
        self.trends = trends
        trends_sa = trends.apply(self.sadjust,axis=0)
        self.trends_sa = trends_sa


        # Old way
        # indices = pd.concat([
        #         trends_sa.apply(self.normalize).sum(axis=1).to_frame('GTI (Normalized)'),
        #         trends_sa.sum(axis=1).to_frame('GTI (Standard)')
        #         ],axis=1).apply(self.normalize)
        if self.seasonal and self.sa_method == 'trends':
            indices = self.normalize(trends_sa.sum(axis=1))
            indices.name = 'GTI'
        elif self.seasonal and self.sa_method == 'index':
            indices = self.normalize(self.sadjust(trends.sum(axis=1)))
            indices.name = 'GTI'
        elif self.season and self.sa_method == 'both':
            indices = self.normalize(self.sadjust(trends_sa.sum(axis=1)))
            indices.name = 'GTI'
        else:
            indices = self.normalize(trends.sum(axis=1))
            indices.name = 'GTI'

        if plot:
            indices.plot()

        # The final thing is to add the indices
        self.gti = indices

        return self

    def pull_timeframe(self, date_start=None, date_end=None):
        """
        This function pulls data from a set timeframe for all variables in kw_list.
        The outcome will be hourly, weekly, or monthly depending on the length
        of time specified. The point is to do this with a series of smaller time-frames.
        It can also be a standalone method.

        Parameters
        ----------
        pytrend: class
            Must be initiated with TrendReq.
            See pytrend documentation. The default is pytrend.
        kw_list: list
            The list of search terms (default is kw_list)
        benchmark: str
            The benchmark term, either blank or first word in kw_list.
            The default is benchmark.
        geo: str
            Country or region to run the search.
        date_start: str
            Date in %y-%m-%d format. The default is date_start.
        date_end: str, optional
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

        # If no custom timeframes are specified, it will just pull the whole range as is.
        if not date_start:
            date_start = self.date_start
        if not date_end:
            date_end = self.date_end


        if self.benchmark:
            # Do the searches in batches
            # For each one initial transform and spit into dictionary of dataframes
            for idx, ss in enumerate(self.search_groups):
                if self.slowdown:
                    time.sleep(round(randn()*4+2,2)) # sleep it so no timeout
                # Do the search
                self.pytrend.build_payload(ss,geo=self.geo,
                                      timeframe='%s %s' %(date_start,
                                                          date_end))
                df = self.pytrend.interest_over_time()

                # Warn and stop if benchmark sucks
                if not self.benchmark_select:
                    if self.too_small(df[self.benchmark]):
                        raise ValueError('The benchmark has too many 0 or small values. '\
                                         'Please choose a different first search term '\
                                         'or choose optimally.')
                        break
                else:
                    if self.too_small(df[self.benchmark]):
                        print('Benchmark term %s is optimally selected, but performs '\
                            'poorly between %s and %s' %(self.benchmark,date_start,date_end))

                # Get rid of partial days
                df = df.loc[df.isPartial.astype('str').eq('False'),ss]

                # Just in case replace 0 values in the benchmark with 1's
                df[self.benchmark] = df[self.benchmark].replace({0:1})

                if idx==0:
                    trends = df
                else:
                    df = df.mul((trends[self.benchmark]/df[self.benchmark]).values,0)
                    trends = trends.join(df.drop(self.benchmark,axis=1))

        else:
            self.pytrend.build_payload(self.kw_list,geo=self.geo,
                                  timeframe='%s %s' %(date_start,date_end))
            df = self.pytrend.interest_over_time()
            trends = df.loc[df.isPartial.astype('str').eq('False'),self.kw_list]

        return trends


    def get_benchmark(self):
        # Limit on google trends searches is 5 words else need benchmark term
        if len(self.kw_list) > 5 and not self.benchmark_select:
            benchmark = self.kw_list[0]
            search_groups = list(self.chunks(self.kw_list))
        elif len(self.kw_list) > 5 and self.benchmark_select:
            benchmark = self.optimal_benchmark()
            words = self.kw_list.copy()
            # put optimal benchmark first here
            words.insert(0, words.pop(words.index(benchmark)))
            search_groups = list(self.chunks(words))
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

    def optimal_benchmark(self):
        """
        Run generic searches over the timeframe to calculate best potential index:

        The function takes the self object, analyzes the language of the kw_list and
        runs searches over the entire timeframe, comparing the average of the series to
        football (english) or futbol + fútbol (spanish).

        The highest average over the timeframe (making sure there are not years
        with 0 average is selected as benchmark).
        """

        if self.lang == 'es':
            popterm = 'fútbol'
        elif self.lang == 'en':
            popterm = 'football'
        else:
            raise ValueError('Currently only supports English (en) and Spanish (es)')

        chunks = list(self.chunks([popterm]+self.kw_list))

        for index,chunk in enumerate(chunks):
            self.pytrend.build_payload(chunk,geo=self.geo,
                                  timeframe='%s %s' %(self.date_start,self.date_end))
            temp = self.pytrend.interest_over_time()
            temp = temp.loc[temp.isPartial.astype('str').eq('False'),chunk].drop(columns=popterm)

            if index==0:
                df = temp
            else:
                df = df.join(temp)

        # Returns number of nonzero years
        teststats = df.resample('Y').mean().apply(lambda x: x.eq(0).eq(False))\
                                           .sum().rename('numnonzero').to_frame()
        # Returns the mean over time of each potential benchmark
        teststats = teststats.join(df.mean(axis=0).rename('meanval').to_frame())
        # sorts it, the best is the highest mean among highest nonzero years
        teststats = teststats.sort_values(['numnonzero','meanval'],ascending=False)

        return teststats.index[0]

    @staticmethod
    def chunks(lst, n=5):
        """Yield successive n-sized chunks from lst with benchmark first."""
        bench = lst[0]
        for i in range(1, len(lst), n-1):
            yield [bench] + lst[i:i+n-1]

    @staticmethod
    def combine_kw_list(lst,n=100):
        """Combine long kw_list into "+" separated chunks"""
        for ii,jj in enumerate(lst):
            if ii==0:
                temp = jj
                master = []
            else:
                if len(temp+' + '+jj)<n:
                    temp+= ' + ' + jj
                else:
                    master.append(temp)
                    temp = jj
        return master

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
    def sadjust(x):
        """ Accepts a series with datetime index, returns statsmodels trend+resid """
        y = tsa.seasonal_decompose(x,extrapolate_trend='freq')
        z = y.resid + y.trend
        return z

    @staticmethod
    def normalize(x):
        return (x-x.mean())/x.std()
