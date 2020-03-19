'''
This file gives a numerical example of how searching for separate keywords is
equivalent to searching kw_1 + kw_2 + ...

I conduct two searches:
    1. The first searching ['Biden','Obama','Schumer','Bernie','Clinton']
    2. The second searching 'Biden + Obama + Schumer + Bernie + Clinton'

I plot the results

'''
import pandas as pd
import seaborn as sns; sns.set()

df = pd.read_csv('test_democrats.csv',skiprows=2)
df.columns = ['Week','Obama','Biden','Clinton','Schumer','Bernie','GTI (Together)']
df.loc[:,'GTI (Separate)'] = df[['Obama','Biden',
                                 'Clinton','Schumer','Bernie']].sum(axis=1)

df = df.set_index('Week').filter(regex='GTI')
for ii in df.columns:
    df[ii] = (df[ii] - df[ii].mean())/df[ii].std()

df.plot()
