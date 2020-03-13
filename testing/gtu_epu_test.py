'''
Recreating the US GTU from Castelnuovo and Tran (2017)
and comparing it with Bloom, Baker, Davis EPU and original GTU Index
See here: https://www.sciencedirect.com/science/article/pii/S0165176517303993#appSB
and here: https://www.policyuncertainty.com/us_monthly.html

Special Notes:
    1. I made "stock market" the benchmark term, because other terms had too many
    0 values. This should not affect output.
    2. I search 2006 through 2017, which seems right given their paper.

When last run, results were:
    1. Correlation with GTU in paper: 0.84
    2. Correlation with BBD in paper: 0.28, Correlation found here: 0.27

'''
import pandas as pd
from pytrendex import Trendex


# =============================================================================
# Making GTU Index from Castelnuovo and Tran (2017)
# =============================================================================

kw_list = [
    'stock market',
    'United States Congress',
    'Affirmative action',
    'American Recovery and Reinvestment Act of 2009',
    'At-will employment',
    'austerity',
    'bank loan',
    'Bank of England',
    'Bank rate',
    'Bank regulation',
    'bankruptcy',
    'budget cut',
    'business outlook',
    'Carbon tax',
    'Clean Water Act',
    'collective agreement',
    'Commodity Futures Trading Commission',
    'construction permit',
    'consumer confidence',
    'Consumer price index',
    'debt ceiling',
    'default',
    'Discount window',
    'Dodd-Frank',
    'economic outlook',
    'emission trading clean air act',
    'energy policy',
    'environment protection',
    'Equal Employment Opportunity Commission',
    'Equal opportunity employment',
    'European debt crisis',
    'Federal Deposit Insurance Corporation',
    'Federal funds rate',
    'Federal Reserve System',
    'financial crisis',
    'financial reform',
    'fiscal cliff',
    'Fiscal policy',
    'Food and Drug Administration',
    'food price',
    'fuel price',
    'gas price',
    'health care act',
    'health care reform',
    'home price',
    'home sales',
    'inflation',
    'job security',
    'Military budget',
    'minimum wage',
    'Monetary policy',
    'Money supply',
    'National debt of the United States',
    'National Labor Relations Act',
    'National Labor Relations Board',
    'natural reserve',
    'Open market operation',
    'Patient Protection and Affordable Care Act',
    'pollution control',
    'price level',
    'Quantitative easing',
    'real estate bubble',
    'recession',
    'reform',
    'regulation',
    'Right-to-work law',
    'Securities and Exchange Commission',
    'Share price',
    'slow economic recovery',
    'stock exchange',
    'tax cut',
    'Tort reform',
    'unemployment benefit',
    'unemployment extension',
    'United States Environmental Protection Agency',
    'United States federal budget',
    'United States housing bubble',
    'White House',
    'Workers compensation'
    ]

trends = Trendex(kw_list,'US','2006-01-01','2017-12-31','monthly')

# Result is in trends.indices, it is the "standard" aggregation
# the scaling is different, would be trivial to rescale as in their paper (no effect on correlation)
df = trends.indices.iloc[:,1].to_frame().rename(columns={'GTI (Standard)':'gti'})

# =============================================================================
# Getting EPU Index
# =============================================================================
epu = pd.read_excel('https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx')
epu.Year = pd.to_numeric(epu.Year,errors='coerce',downcast='integer')
epu = epu.loc[epu.Year.isnull().eq(False)]
epu.loc[:,'date'] = epu.apply(lambda x: pd.to_datetime('%i-%i-01' %(x.Year,x.Month)),axis=1)
epu = epu.set_index('date').rename(columns={'News_Based_Policy_Uncert_Index':'epu_bbd_news',
                                            'Three_Component_Index':'epu_bbd_main'})
epu = epu.filter(regex='epu_') # keep only relevant columns


# =============================================================================
# Getting Original Index
# =============================================================================
orig = pd.read_excel('https://sites.google.com/site/efremcastelnuovo/'\
                     'GTU_indices_EcLetts.xls?attredirects=0&d=1',
                     skiprows=5).rename(columns={'Month':'date'})
orig = orig.set_index('date')


# =============================================================================
# Merging them together and testing correlation
# =============================================================================

df = df.join(epu,how='left')
df = df.join(orig,how='left')

corr_report_epu = df.gti.corr(df.epu_bbd_main).round(2)
corr_report_orig = df.gti.corr(df.GTU_US).round(2)

print('Correlation with GTU in paper: %s' %corr_report_orig)
print('Correlation with BBD in paper: 0.28,','Correlation found here: %s' %corr_report_epu)
