import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
from matplotlib import dates
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
def add_merge_cols(states_df,merge_col='state'):
    states_df = states_df.merge(\
                (pd.pivot_table(states_df,values='cases',index = 'date', columns=merge_col).fillna(0)-\
                 pd.pivot_table(states_df,values='cases',index = 'date', columns=merge_col).fillna(0).shift()).stack().reset_index(),\
                how = 'left',on=['date',merge_col]).rename(columns={0:'daily_new_cases'})
    states_df = states_df.merge(\
                (pd.pivot_table(states_df,values='deaths',index = 'date', columns=merge_col).fillna(0)-\
                 pd.pivot_table(states_df,values='deaths',index = 'date', columns=merge_col).fillna(0).shift()).stack().reset_index(),\
                how = 'left',on=['date',merge_col]).rename(columns={0:'daily_new_deaths'})
    for val in [7,14]:
        states_df = states_df.merge(\
                (pd.pivot_table(states_df,values='deaths',index = 'date', columns=merge_col).fillna(0)-\
                 pd.pivot_table(states_df,values='deaths',index = 'date', columns=merge_col).fillna(0).shift(val)).stack().reset_index(),\
                how = 'left',on=['date',merge_col]).rename(columns={0:'deaths_last_{}'.format(val)})
        states_df = states_df.merge(\
                (pd.pivot_table(states_df,values='cases',index = 'date', columns=merge_col).fillna(0)-\
                 pd.pivot_table(states_df,values='cases',index = 'date', columns=merge_col).fillna(0).shift(val)).stack().reset_index(),\
                how = 'left',on=['date',merge_col]).rename(columns={0:'cases_last_{}'.format(val)})
        states_df['deaths_last_{}_scaled'.format(val)] = states_df['deaths_last_{}'.format(val)]/states_df[merge_col].map(states_df.groupby(merge_col)['deaths_last_{}'.format(val)].max())
        states_df['cases_last_{}_scaled'.format(val)] = states_df['cases_last_{}'.format(val)]/states_df[merge_col].map(states_df.groupby(merge_col)['cases_last_{}'.format(val)].max())
    states_df['date'] = pd.to_datetime(states_df['date'])
    return states_df
def prep_data():
    states_df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv').pipe(add_merge_cols,merge_col='state')
    return states_df
def prep_data_region():

    states_df = pd.read_csv('https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv')
    region_df = pd.read_csv('https://raw.githubusercontent.com/cphalpert/census-regions/master/us%20census%20bureau%20regions%20and%20divisions.csv')
    state_region = states_df.merge(region_df,how='inner',left_on='state',right_on='State')
    final_df = state_region.groupby(['Region','date'])[['deaths','cases']].sum().reset_index().pipe(add_merge_cols,merge_col='Region')
    return final_df
        
def plot_deaths_vs_cases(date,cases,deaths,title,ax=False,add_lines=True,add_legend=True, label_num=2):
    if not ax:
        ax = sns.lineplot(date,cases,label='Cases')
    else:
        sns.lineplot(date,cases,ax=ax,label='Cases')
    ax.fill_between(date,0,cases,color='dodgerblue',alpha=0.2)
    sns.lineplot(date,deaths,ax=ax,label='Deaths')
    ax.fill_between(date,0,deaths,color='orange',alpha=0.2)

    peak_case_date = date[cases.idxmax()]
    peak_death_date = date[deaths.idxmax()]
    days = (peak_death_date-peak_case_date).days
    ax.plot(peak_death_date,deaths.max(),'o',color='orange')
    ax.plot(peak_case_date,cases.max(),'o',color='dodgerblue')
    if add_lines:
        if days <0:
            color='red'
        else:
            color='green'
        y = [deaths.max(),cases.max()]
        x = [peak_death_date, peak_case_date]
        ax.plot(x,y,color=color,linewidth=2,linestyle='--')
    ax.axes.get_yaxis().set_visible(False)
    date_set = datetime.datetime(year=2020,month=4,day=1)
    date_set2 = (date.max()-date_set)/2+date_set
    date_ticks = [date_set,date_set2,date.max()]
    ax.set_xticks([dates.date2num(x) for x in date_ticks])
    ax.set_xticklabels([x.strftime('%b %d') for x in date_ticks])
    ax.text(1.05,0.3,"Peak Cases: {}\nPeak Deaths: {}\nDiff: {} day(s)"
            .format(peak_case_date.strftime('%b %d'),peak_death_date.strftime('%b %d'),days),transform=ax.transAxes)
    if add_legend:
        ax.legend(fontsize='small',loc='upper right')
    else:
        ax.legend().set_visible(False)
    ax.text(.03,.6,title,fontsize=10,fontweight='bold',transform=ax.transAxes)
    
def plot_deaths_state_grid(df,num=14,geo='state',sort_by='deaths',**kwargs):
    state_cnt = df[geo].nunique()
    state_list = df[[geo,'date']].iloc[df.groupby(geo)['{}_last_{}_scaled'.format(sort_by,num)].idxmax()].sort_values(by='date')[geo].tolist()
    if 'figsize' not in kwargs.keys():
        figsize=(5,20)
    else:
        figsize = kwargs.pop('figsize')
    fig, axes = plt.subplots(nrows=state_cnt,sharex='all',figsize=figsize)
    add_legend = True
    label_num = num/7
    for state,ax in zip(state_list,axes):
        print(state)
        state_df = df[df[geo]==state]
        plot_deaths_vs_cases(state_df['date'],state_df['cases_last_{}_scaled'.format(num)],state_df['deaths_last_{}_scaled'.format(num)],title=state,ax=ax,add_legend=add_legend,label_num=label_num,**kwargs)
        if add_legend:
            add_legend=False
#     fig.suptitle('Covid 19 Cases and Death Peaks By State', fontsize=16, ha='center',y=1.02)

    return fig, axes

def main():
    exclude_states = ['Puerto Rico', 'Virgin Islands',
       'Guam', 'Northern Mariana Islands']
    death_df = prep_data()
#     fig,axes = plot_deaths_state_grid(death_df[~death_df['state'].isin(exclude_states)].reset_index(drop=True),add_lines=False,figsize=(5,120))
#     fig.text(1,.11,'Data Source:https://github.com/nytimes/covid-19-data',fontsize=10,horizontalalignment='right',
#          fontstyle='italic', bbox=dict(facecolor='dodgerblue',alpha=0.5))
#     fig.savefig('covid_2week_peaks.png')
#     fig,axes = plot_deaths_state_grid(death_df[~death_df['state'].isin(exclude_states)].reset_index(drop=True),num=7,add_lines=False,figsize=(5,120))
#     fig.text(1,.11,'Data Source:https://github.com/nytimes/covid-19-data',fontsize=10,horizontalalignment='right',
#          fontstyle='italic', bbox=dict(facecolor='dodgerblue',alpha=0.5))
#     fig.savefig('covid_1week_peaks.png')
    test_sizes = [(5,50),(10,50),(10,40),(5,60)]
    for size in test_sizes:
        fig,axes = plot_deaths_state_grid(death_df[~death_df['state'].isin(exclude_states)].reset_index(drop=True),add_lines=False,figsize=size)
        axes[0].set_title("Covid 19 Cases and Death Peaks By State",fontsize=12,fontweight='bold',wrap=True)
        fig.tight_layout()
        fig.savefig('./saved_pngs/covid_2week_peaks_{}by{}_sort_deaths.png'.format(size[0],size[1]))
        fig,axes = plot_deaths_state_grid(death_df[~death_df['state'].isin(exclude_states)].reset_index(drop=True),num=7,add_lines=False,figsize=size)
        axes[0].set_title("Covid 19 Cases and Death Peaks By State",fontsize=12,fontweight='bold',wrap=True)
        fig.tight_layout()
        fig.savefig('./saved_pngs/covid_1week_peaks_{}by{}_sort_deaths.png'.format(size[0],size[1]))
    test_sizes_region = [(15,15),(10,10),(10,20)]
    death_df = prep_data_region()

    for size in test_sizes_region:
        fig,axes = plot_deaths_state_grid(death_df,geo='Region',add_lines=False,figsize=size)
        axes[0].set_title("Covid 19 Cases and Death Peaks Region",fontsize=12,fontweight='bold',wrap=True)
        fig.tight_layout()
        fig.savefig('./saved_pngs/covid_2week_peaks_{}by{}_region.png'.format(size[0],size[1]))
        fig,axes = plot_deaths_state_grid(death_df,num=7,geo='Region',add_lines=False,figsize=size)
        axes[0].set_title("Covid 19 Cases and Death Peaks Region",fontsize=12,fontweight='bold',wrap=True)
        fig.tight_layout()
        fig.savefig('./saved_pngs/covid_1week_peaks_{}by{}_region.png'.format(size[0],size[1]))
        
if __name__ == '__main__':
    main()
