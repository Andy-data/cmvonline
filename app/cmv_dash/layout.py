import dash_core_components as dcc
import dash_html_components as html

from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from random import randint

import plotly.graph_objs as go
import plotly.colors

from CoronaData_online import *
from Corona_Rt import *



# define color palette
cor_color = plotly.colors.qualitative.Light24
# define max no. of datasets to display
max_rows = 10

cordat = CoronaData()
Rt = Rt(cordat)

# Define main graph
main_graph = dcc.Graph(id='main_graph',
                       figure = {
                           'data':  [go.Scatter(
                               x=cordat.corona_dict[('WDM', 'Germany', 'Germany')][0],
                               y=cordat.corona_dict[('WDM', 'Germany', 'Germany')][1],
                               mode='lines')],
                           'layout' : go.Layout(title='CoronaMultiView online', yaxis={'type':'log'})},
                       style = {'width':'49%', 'border':'2px black solid', 'borderRadius':5,
                                'display':'inline-block', 'margin': 0})

#****************************************************************************
# define the control block for data selection
# select_data_shadow is a dict containing a copy of the values

source_list = np.unique(cordat.sources)
level1_list = np.unique(cordat.countries_level1[np.where(cordat.sources==source_list[0])])
level2_list = np.unique(cordat.countries_level2[
                            np.where(cordat.sources==source_list[0]) and
                            np.where(cordat.countries_level1==level1_list[0])])
row_height = 26
select_data_block = []
rows = np.arange(0, max_rows)
for row in rows:
    select_data_line = []
    # create checkbutton for 'show'
    select_data_line.append(
        dcc.Checklist(id=f'radio_show_{row}',
                      options=[{'label': ' ', 'value': 0},
                               ],
                      value=[],
                      style = {'width': row_height*0.8, 'height':row_height, 'display':'inline-block',
                               'margin': 0, 'color': 'green', 'background-color': cor_color[row]}))
    select_data_shadow['show'].append([])

    # create dropdown for data source
    select_data_line.append(
        dcc.Dropdown(id=f'drop_source_{row}',
                 options =[{'label': source_list[i], 'value': source_list[i]} for i in range(len(source_list))],
                 value = source_list[0],
                 style = {
                     'width' : 80, 'height' : row_height, 'display' : 'inline-block',
                     'margin': 0, 'padding':0}))
    select_data_shadow['source'].append(source_list[0])

    # create dropdown for level1 selection
    select_data_line.append(
        dcc.Dropdown(id=f'drop_level1_{row}',
                     options =[{'label': level1_list[i], 'value': level1_list[i]} for i in range(len(level1_list))],
                     value = level1_list[0],
                     style = {
                         'width': 150, 'height':row_height, 'display':'inline-block', 'margin': 0}))
    select_data_shadow['level1'].append(level1_list[0])

    # create dropdown for level2 selection
    select_data_line.append(
        dcc.Dropdown(id=f'drop_level2_{row}',
                     options =[{'label': level2_list[i], 'value': level2_list[i]} for i in range(len(level2_list))],
                     value = level2_list[0],
                     style = {
                         'width': 150, 'height':row_height, 'display':'inline-block', 'margin': 0}))
    select_data_shadow['level2'].append(level2_list[0])

    # create dropdown for subset selection
    select_data_line.append(
        dcc.Dropdown(id=f'drop_subset_{row}',
                     options =[{'label': 'inf', 'value': 'inf'},
                               {'label': 'deaths', 'value': 'deaths'}],
                               # {'label': 'incid', 'value': 'incid'},
                               # {'label': 'inc_d', 'value': 'inc_d'}],
                     value = 'inf',
                     style = {
                         'width': 70, 'height':row_height, 'display':'inline-block', 'margin': 0}))
    select_data_shadow['subset'].append('inf')

    # create numeric input for time shift
    select_data_line.append(
        dcc.Input(id=f'in_t_shift_{row}',
                     type = 'number',
                     value = 0,
                     style = {
                         'width': 60, 'height':row_height, 'display':'inline-block', 'margin-bottom': 0}))
    select_data_shadow['t_shift'].append(0)

    # create numeric input for y scaling (i.e. shift in y-direction on log scale)
    select_data_line.append(
        dcc.Input(id=f'in_scale_y_{row}',
                  type = 'number',
                  value = 1,
                  step = 0.1,
                  min = 0,
                  style = {
                      'width': 70, 'height':row_height, 'display':'inline-block', 'margin': 0}))
    select_data_shadow['scale_y'].append(1)


    # create checkbox to indicate removal of weekly artefacts
    select_data_line.append(
        dcc.Checklist(id=f'radio_rm_weekly_{row}',
                      options=[{'label': ' ', 'value': 1},
                               ],
                      value=[1],
                      style = {'width': row_height*0.6, 'height':row_height, 'display':'inline-block',
                               'margin': 0, 'color': 'green'}))
    select_data_shadow['rm_weekly'].append([1])

    # create numeric input for week range to remove weekly artefacts
    select_data_line.append(
        dcc.Input(id=f'in_rm_weeks_{row}',
                  type = 'number',
                  value = 7,
                  min = 1,
                  max = 100,
                  style = {
                      'width': 60, 'height':row_height, 'display':'inline-block', 'margin-bottom': 0}))
    select_data_shadow['rm_weeks'].append(7)

    # combine line to a Div
    select_data_line_div = html.Div(select_data_line, style={
        'border': '2px blue solid', 'margin':0})
    select_data_block.append(select_data_line_div)

layout = html.Div([
    main_graph,
    html.Div(
        select_data_block,
    style = {
    'width': '45%', 'border': '2px red solid', 'borderRadius': 5, 'display':'inline-block'}),
    html.Div(id='trigger_graph_redraw', children='no update', style= {'display': 'none'})]
    )

