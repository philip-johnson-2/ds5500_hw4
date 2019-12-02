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

# get total fed spending 
total = sum(ed_data['TFEDREV'])
percent_15_total = float(total) * .15


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
data = data[['LEAID', 'TOTAL', 'AM', 'AS','HI', 'BL', 'WH', 'HP', 'TR','ALL_MTH00PCTPROF_1516']] 
data['Cut'] = 'No Cut'
data.loc[budget_data['ALL_MTH00PCTPROF_1516'] > perf_threshold, 'Cut'] = 'Cut'
data.loc[budget_data['ALL_MTH00PCTPROF_1516'] <= perf_threshold, 'Cut'] = 'No Cut'

# create two datasets
cut_data = data[data['Cut'] == 'Cut']
cut_total = cut_data['TOTAL'].sum()
am_cut_percent = cut_data['AM'].sum() / cut_total
as_cut_percent = cut_data['AS'].sum() / cut_total
hi_cut_percent = cut_data['HI'].sum() / cut_total
bl_cut_percent = cut_data['BL'].sum() / cut_total
wh_cut_percent = cut_data['WH'].sum() / cut_total
hp_cut_percent = cut_data['HP'].sum() / cut_total
tr_cut_percent = cut_data['TR'].sum() / cut_total

# create two datasets
no_cut_data = data[data['Cut'] == 'No Cut']
no_cut_total = no_cut_data['TOTAL'].sum()
am_no_cut_percent = no_cut_data['AM'].sum() / no_cut_total
as_no_cut_percent = no_cut_data['AS'].sum() / no_cut_total
hi_no_cut_percent = no_cut_data['HI'].sum() / no_cut_total
bl_no_cut_percent = no_cut_data['BL'].sum() / no_cut_total
wh_no_cut_percent = no_cut_data['WH'].sum() / no_cut_total
hp_no_cut_percent = no_cut_data['HP'].sum() / no_cut_total
tr_no_cut_percent = no_cut_data['TR'].sum() / no_cut_total

# merge into table
plot_data = [ ('Cut', 'American Indian' , am_cut_percent) ,
             ('Cut', 'Asian' , as_cut_percent) ,
             ('Cut', 'Hispanic' , hi_cut_percent ) ,
             ('Cut', 'Black' , bl_cut_percent ) ,
             ('Cut', 'White' , wh_cut_percent) ,
             ('Cut', 'Hawaiin' , hp_cut_percent) ,
             ('Cut', 'Two + Races' , tr_cut_percent) ,
             ('No Cut', 'American Indian' , am_no_cut_percent) ,
             ('No Cut', 'Asian' , as_no_cut_percent) ,
             ('No Cut', 'Hispanic' , hi_no_cut_percent ) ,
             ('No Cut', 'Black' , bl_no_cut_percent ) ,
             ('No Cut', 'White' , wh_no_cut_percent) ,
             ('No Cut', 'Hawaiin' , hp_no_cut_percent) ,
             ('No Cut', 'Two + Races' , tr_no_cut_percent)  ]

#Create a DataFrame object
df = pd.DataFrame(plot_data, columns = ['Funding Cut','Race','Percent of Population'])

# plot data
sns.catplot(x="Funding Cut", y="Percent of Population", hue="Race", kind="bar", data=df);




