# pytrendex
Code to generate a Google Trends Index

## Installation
If there is already a `pytrendex-[xxx].tar.gz` file, then unzip the file and run:
```
pip install -e pytrendex-[xxx]
```
where the final argument is the unzipped folder.

If there is no `.tar.gz` file, then you will need one additional step. Navigate to
the file `setup.py` and run:
```
python setup.py sdist
```
This will create the necessary file.


## Trendex
The main thrust of this package is a class `Trendex`.
This class makes an index utilizing Google Trends from keywords.

### Parameters

- kw_list: list
      The list of keywords that will be searched. If larger than 5, will create
      benchmark term from the first term in the list.

- geo: str
      The country or place the search is conducted in, see Trends documentation.

- date_start: str, optional
      The data where the index starts in format: 'yyyy-mm-dd',
      if none provided, then does it at the cutoff days before the date end.

- date_end: str, optional
      The data where the index ends in format: 'yyyy-mm-dd',
      if none provided, then defaults to current day.

- frequency: str, optional
      The frequency of the index. Note that the index always pulls daily data,
      so collapsing into larger time-frames is done by averages ex-post.

- make_index: Binary, optional
      If true, then go ahead and instantiate class to generate indices.
      Default is True.

- plot: boolean, optional
      If True, and make_index is True, then it plots index. Default is true.


### Returns (back to class instance)
- self.indices: Dataframe
      This is the normalized indexes made from the underlying data. It is
      the main thing returned from this function.

- self.trends: Dataframe
      It is the adjusted and combined series for each term searched.
      You could use this to plot individual keywords in the index.
      Will differ from raw_trends_adjusted if frequency is changed from daily.

- self.raw_trends_adjusted: Dictionary
      These are the adjusted (using overlapping timeframes) raw results
      for each term. Index of dictionary corresponds to index of timechunks.
      Could differ from trends if frequency is changed from daily.

- self.raw_trends: Dictionary
      These are the unadjusted raw results for each term.
      Note: Adjustment has still been made by the benchmark term for
      searches exceeding 5 terms.

- self.adjustment_factors: Series
      Returns the adjustment factors used on each overlapping segment.
      [term]_1 is the mean of the term in the earlier segment.
      [term]_2 is the mean of the term in the later segment.
      The adjustment is [term]_1/[term_2] * segment_2
      Note: means for each segment are bounded from below by 1, so that
      we do not seriously alter indices.

## Example
A use case example is provided below:
```
from pytrendex import Trendex

kw_list = ['Trump','Obama','Biden','Clinton','Warren','Bernie']
geo = 'US'
date_start = '2018-01-01'
frequency = 'weekly'

result = Trendex(kw_list=kw_list,geo=geo,date_start=date_start,frequency=frequency)
```
