# pytrendex
Code to generate a Google Trends Index

## Installation
```
pip install pytrendex
```

## Trendex
The main thrust of this package is a class `Trendex`.
This class makes an index utilizing Google Trends from keywords.

### Parameters

- `kw_list`: list
      The list of keywords that will be searched. If larger than 5, will create
      benchmark term from the first term in the list.

- `geo`: str
      The country or place the search is conducted in, see Trends documentation.

- `lang`: str, options are currently `en` for english and `es` for spanish
      The language that the `kw_list` is (required for optimal benchmark selection).

- `date_start`: str, optional
      The data where the index starts in format: 'yyyy-mm-dd',
      if none provided, then does it at the cutoff days before the date end.

- `date_end`: str, optional
      The data where the index ends in format: 'yyyy-mm-dd',
      if none provided, then defaults to current day.

- `frequency`: str, optional
      The frequency of the index. Note that the index always pulls daily data,
      so collapsing into larger time-frames is done by averages ex-post.

- `gen_index`: Binary, optional
      If true, then go ahead and instantiate class to generate indices.
      Default is True.

- `plot`: boolean, optional
      If True, and gen_index is True, then it plots index. Default is true.

- `kw_list_split`: boolean, optional
      If True then the max length for `kw_list` is 20 terms; after that it will
      split the search by using the "+" option for search terms (which acts
      as an "or" operator for google trends). Highly recommended to keep load down.

- `benchmark_select`: boolean, optional
      If True then optimally search over timeframe for best benchmark phrase, see
      documentation for that function for description of how this is done.
      If False, then the benchmark will be the first term in the `kw_list`.

- `slowdown`: boolean, optional
      If True then include time.sleep() at key moments to slow down the index.
      Currently defaults to random intervals of mean 5 or 7 seconds depending on
      where in the code. Remove this at your own peril (Google lockout).

- `seasonal_adjust`: boolean, optional (default = True)
      If True, then seasonally adjust the series (recommended). Seasonally
      adjusted trends are always constructed and saved in trends_sa,
      but this incorporates them into the index that is automatically constructed.

### Returns (back to class instance)
- `self.gti`: Series (main output)
      This is the normalized indexes made from the underlying data. It is
      the main thing returned from this function.

- `self.trends`: DataFrame (major output)
      It is the adjusted and combined series for each term searched.
      You could use this to plot individual keywords in the index.
      Will differ from raw_trends_adjusted if frequency is changed from daily.

- `self.trends_sa`: DataFrame (major output)
      These are the trends seasonally adjusted; they are always returned.

- `self.raw_trends_adjusted`: Dictionary (minor output)
      These are the adjusted (using overlapping timeframes) raw results
      for each term. Index of dictionary corresponds to index of timechunks.
      Could differ from trends if frequency is changed from daily.

- `self.raw_trends`: Dictionary (minor output)
      These are the unadjusted raw results for each term.
      Note: Adjustment has still been made by the benchmark term for
      searches exceeding 5 terms.

- `self.adjustment_factors`: Series (minor output)
      Returns the adjustment factors used on each overlapping segment.
      The adjustment is `[term]_1/[term_2] * segment_2`

## Example
A use case example is provided here:
```
from pytrendex import Trendex

kw_list = ['Obama','Biden','Clinton','Warren','Trump','Bernie']
geo = 'US'
date_start = '2018-01-01'
frequency = 'weekly'

## Generating the indexes in two different ways
result = Trendex(kw_list=kw_list, geo=geo, lang='en',
                  plot=False, date_start=date_start, frequency=frequency)

# A smaller index, here we create it in two steps (date start and end and frequency auto selected)
result2 = Trendex(['Obama','Trump'],geo='US',gen_index=False)
result2 = result2.make_index(plot=False)

## Analyzing the results

result.gti.plot() # creates a matplotlib plot of the index for us to look at
result2.trends_sa.plot() # plots the adjusted individual terms that make up the index

result.gti.to_csv('file.csv') # saves the index as a csv file

```
