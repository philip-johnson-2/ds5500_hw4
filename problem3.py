import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import plotly.graph_objects as go
import statistics
import seaborn as sns
import matplotlib.pyplot as plt

# read the base dataset
ed_data = pd.read_csv(os.path.expanduser('~/Desktop/Sdf16_1a.txt'), sep='\t')
math_data = pd.read_csv(os.path.expanduser('~/Desktop/math-achievement-lea-sy2015-16.csv'))
geo_data = pd.read_csv(os.path.expanduser('~/Desktop/ccd_lea_052_1516_w_1a_011717.csv'))
geo_data['LEAID'] = geo_data['LEAID'].astype(str)
disable_data = pd.read_csv(os.path.expanduser('~/Desktop/ccd_lea_002089_1516_w_1a_011717.csv'))
disable_data['LEAID'] = disable_data['LEAID'].astype(str)


# function for cleaning data
def clean_data(field):
    """ 
    Function to take a column and covert non-numeric values into numeric values to account 
    for range values in the data as well as account for greater than and less than 
    symbols in the data. For ranges, I take the average numeric value within the range. 
    For greater then and less then strings I use 0 or 100 to determin average value.
    Other values that do not have a numeric definition get converted to NA.
    """
    num = field

    for i in range(len(num)):
        if num[i] == '.': # convert to NA
            value = np.nan
        
        elif num[i] == 'PS': # convert to NA
            value = np.nan

        elif num[i] == ' ': # convert to NA
            value = np.nan
        
        elif num[i].count('-') > 0: # get range values
            y = num[i].split("-")
            value = np.mean([int(y[0]),int(y[1])])
        
        elif num[i][0:2] == 'LE': # less than or equal to
            x = float(num[i].lstrip('LE'))
            value = np.mean([0,int(x)])
        elif num[i][0:2] == 'GE': # greater than or equal to
            x = float(num[i].lstrip('GE'))
            value = np.mean([int(x),100])
        elif num[i][0:2] == 'LT': # less than
            x = float(num[i].lstrip('LT'))
            value = np.mean([0,int(x)])
        elif num[i][0:2] == 'GT': # greater than
            x = float(num[i].lstrip('GT'))
            value = np.mean([int(x),100])
           
        else:
            value = int(num[i])
        
        num[i] = value

        
    return num
        




'''

Adjust county budgets based on district performace
based on the districts performance compared to the 
national average - if the district is above average
we will reduce funding 

'''
# clean up math score data
math_scores = clean_data(math_data['ALL_MTH00PCTPROF_1516'])
math_scores = pd.DataFrame(math_scores)

# merge new scores with district information
budget_data = pd.merge(ed_data, math_scores, left_index=True, right_index=True)

# get population stats 
national_average = math_scores['ALL_MTH00PCTPROF_1516'].mean()
std_dev = statistics.pstdev(budget_data['ALL_MTH00PCTPROF_1516'].dropna())

# use the national average and stdev to identify the score cutpoint
perf_threshold = national_average + (std_dev*.5)

# get sum of revenue for districts above performance threshold
sum_rev_above = budget_data.query('ALL_MTH00PCTPROF_1516>' + str(perf_threshold))['TFEDREV'].sum()


# get amount of budget to be cut vs overall and create an updated funding field
budget_cut = percent_15_total / sum_rev_above
budget_data['Updated_Funding'] = budget_data['TFEDREV']
budget_data.loc[budget_data['ALL_MTH00PCTPROF_1516'] > perf_threshold, 'Updated_Funding'] = budget_data.loc[
    budget_data['ALL_MTH00PCTPROF_1516'] > perf_threshold, 'Updated_Funding'].copy() * (budget_cut)


# get count of districts with budget cuts 
budget_data.query('ALL_MTH00PCTPROF_1516>' + str(perf_threshold))['TFEDREV'].count()

# merge geo data
data = pd.merge(budget_data,geo_data, on='LEAID')
data = pd.merge(data, disable_data, on='LEAID')
data = data[['LEAID', 'TOTAL', 'SPECED','ALL_MTH00PCTPROF_1516']] 
data['Cut'] = 'No Cut'
data.loc[budget_data['ALL_MTH00PCTPROF_1516'] > perf_threshold, 'Cut'] = 'Cut'
data.loc[budget_data['ALL_MTH00PCTPROF_1516'] <= perf_threshold, 'Cut'] = 'No Cut'


# create two datasets
cut_data = data[data['Cut'] == 'Cut']
cut_total = cut_data['TOTAL'].sum()
spec_cut_percent = cut_data['SPECED'].sum() / cut_total

# create two datasets
no_cut_data = data[data['Cut'] == 'No Cut']
no_cut_total = no_cut_data['TOTAL'].sum()
spec_no_cut_percent = no_cut_data['SPECED'].sum() / no_cut_total


# merge into table
plot_data = [ ('Cut', spec_cut_percent) ,
             ('No Cut', spec_no_cut_percent) ]

#Create a DataFrame object
df = pd.DataFrame(plot_data, columns = ['Funding Cut','Percent of Population with Special Education'])

# plot data
sns.catplot(x="Funding Cut", y="Percent of Population with Special Education", kind="bar", data=df);

