
# import dash
import dash_core_components as dcc
import dash_html_components as html
# from dash.dependencies import Input, Output
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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = DashProxy(__name__, external_stylesheets=external_stylesheets, prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])

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
select_data_shadow = {'show':[], 'source':[], 'level1':[], 'level2':[], 'subset':[],
                      't_shift':[], 'scale_y':[], 'rm_weekly':[], 'rm_weeks':[]}
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


# ***********************************************************************
# This function handles actions when a "show" checkbox has been changed
# Main tasks: save status to shadow dict
#
# A. Nittke 07/2021
# ***********************************************************************
@app.callback(Output(component_id='trigger_graph_redraw', component_property='children'),
              [Input(component_id=f'radio_show_{row}', component_property='value') for row in range(max_rows)])
def in_show_changed(*values):
    values_bin = checklist2shadow(values)
    shadow_bin = checklist2shadow(select_data_shadow['show'])
    print(np.where(shadow_bin != values_bin))
    select_data_shadow['show'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
# This function handles actions when a "data source" field has been changed
# Main tasks: update level1 dropdowns accordingly and update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id=f'drop_level1_{row}', component_property='options') for row in range(max_rows)] +
              [Output(component_id=f'drop_level1_{row}', component_property='value') for row in range(max_rows)] +
              [Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id=f'drop_source_{row}', component_property='value') for row in range(max_rows)])
def source_changed(*values):
    # detect row which has been changed
    changed_row, = np.where(np.array(values) != np.array(select_data_shadow['source']))
    if changed_row.shape == (0,):
        changed_row = 0
    else:
        changed_row = changed_row[0]

    # save new (theoretical) tuple. If this is not available, lower levels will be set to index 0
    # new_data_tuple = (values[changed_row], select_data_shadow['level1'][row], select_data_shadow['level2'][row])
    # create output list
    level1_out = []
    for i, value in enumerate(list(values)):
        level1_list = np.unique(cordat.countries_level1[np.where(cordat.sources==value)])
        level1_out.append([{'label': level1_list[i], 'value':level1_list[i]} for i in range(len(level1_list))])
    for i, value in enumerate(list(values)):
        if i == changed_row: # and (new_data_tuple not in cordat.corona_dict.keys()):
            level1_out.append(level1_out[i][0]['value'])
        else:
            level1_out.append(select_data_shadow['level1'][i])
    # update shadow dict
    select_data_shadow['source'] = list(values)
    level1_out.append(randint(0, 1e12))
    return level1_out

# ***********************************************************************
# This function handles actions when a "level1" field has been changed
# Main tasks: update level2 dropdowns accordingly and update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id='drop_level2_' + str(row), component_property='options') for row in range(max_rows)] +
              [Output(component_id='drop_level2_' + str(row), component_property='value') for row in range(max_rows)] +
              [Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id='drop_level1_'+str(row), component_property='value') for row in range(max_rows)])
def level1_changed(*values):
    # detect row which has been changed
    changed_row, = np.where(np.array(values) != np.array(select_data_shadow['level1']))
    if changed_row.shape == (0,):
        changed_row = 0
    else:
        changed_row = changed_row[0]

    # save new (theoretical) tuple. If this is not available, lower levels will be set to index 0
    # new_data_tuple = (select_data_shadow['source'][row], values[changed_row], select_data_shadow['level2'][row])

    # create output list
    level2_out = []
    for i, value in enumerate(list(values)):
        level2_list = []
        for j in range(len(cordat.sources)):
            if (cordat.sources[j] == select_data_shadow['source'][i]) and (cordat.countries_level1[j] == value):
                level2_list.append(cordat.countries_level2[j])
        level2_list = np.unique(level2_list)
        level2_out.append([{'label': level2_list[i], 'value':level2_list[i]} for i in range(len(level2_list))])
    for i, value in enumerate(list(values)):
        if i == changed_row: # and (new_data_tuple not in cordat.corona_dict.keys()):
            level2_out.append(level2_out[i][0]['value'])
        else:
            level2_out.append(select_data_shadow['level2'][i])
    # update shadow dict
    select_data_shadow['level1'] = list(values)
    select_data_shadow['level2'] = level2_out[int(len(level2_out)/2):]
    # add a random number for graph trigger
    level2_out.append(randint(0, 1e12))
    return level2_out

# ***********************************************************************
# This function handles actions when a "level2" field has been changed
# Main tasks: update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id=f'drop_level2_{row}', component_property='value') for row in range(max_rows)])
def level2_changed(*values):
    # update shadow dict
    select_data_shadow['level2'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
# This function handles actions when a "subset" field has been changed
# Main tasks: update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id=f'drop_subset_{row}', component_property='value') for row in range(max_rows)])
def subset_changed(*values):
    # update shadow dict
    select_data_shadow['subset'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
# This function handles actions when a "t_shift" field has been changed
# Main tasks: update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id=f'in_t_shift_{row}', component_property='value') for row in range(max_rows)])
def t_shift_changed(*values):
    # update shadow dict
    print(values)
    select_data_shadow['t_shift'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
# This function handles actions when a "scale_y" field has been changed
# Main tasks: update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id=f'in_scale_y_{row}', component_property='value') for row in range(max_rows)])
def scale_y_changed(*values):
    # update shadow dict
    select_data_shadow['scale_y'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
# This function handles actions when a "remove weekly" checkbox has been changed
# Main tasks: save status to shadow dict,
#
# A. Nittke 07/2021
# ***********************************************************************
@app.callback(Output(component_id='trigger_graph_redraw', component_property='children'),
              [Input(component_id=f'radio_rm_weekly_{row}', component_property='value') for row in range(max_rows)])
def rm_weekly_changed(*values):
    values_bin = checklist2shadow(values)
    shadow_bin = checklist2shadow(select_data_shadow['rm_weekly'])
    select_data_shadow['rm_weekly'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
# This function handles actions when a "remove_weeks" field has been changed
# Main tasks: update shadow dict
# A. Nittke 07/2021
# ***********************************************************************
@app.callback([Output(component_id='trigger_graph_redraw', component_property='children')],
              [Input(component_id=f'in_rm_weeks_{row}', component_property='value') for row in range(max_rows)])
def level2_changed(*values):
    # update shadow dict
    print(values)
    select_data_shadow['rm_weeks'] = list(values)
    return randint(0, 1e12)

# ***********************************************************************
#
# This function triggers a graph update
#
# A. Nittke 07/2021
# ***********************************************************************

@app.callback(Output(component_id='main_graph', component_property='figure'),
              [Input(component_id='trigger_graph_redraw', component_property='children')])
def graph_redraw_data(value):
    print(value)
    traces = update_traces()
    layout = update_layout()
    figure =  {'data': traces, 'layout': layout}
    return figure

# ***********************************************************************
#
# This function creates traces from shadow dict data.
#
# A. Nittke 07/2021
# ***********************************************************************
def update_traces():
    traces = []
    for row in range(max_rows):
        # print(f'row {row} {select_data_shadow["show"][row]} {len(select_data_shadow["show"][row])}')
        if len(select_data_shadow['show'][row]) > 0:
            key_tuple = (select_data_shadow['source'][row],
                         select_data_shadow['level1'][row],
                         select_data_shadow['level2'][row])
            scale_y = select_data_shadow['scale_y'][row]
            time_shift = select_data_shadow['t_shift'][row]
            x = np.arange(cordat.corona_dict[key_tuple][5][0], cordat.corona_dict[key_tuple][5][1]+1)

            if select_data_shadow['subset'][row] == 'inf':
                subset_idx = 0
            elif select_data_shadow['subset'][row] == 'deaths':
                subset_idx = 1
            y = cordat.corona_dict[key_tuple][subset_idx]
            if len(select_data_shadow['rm_weekly'][row]) > 0:
                # remove artefacts on weekly basis
                weekdays = np.array([(cordat.start_date + timedelta(days = int(i))).weekday() for i in x])
                rm_weeks = select_data_shadow['rm_weeks'][row]
                result_remove_weekly = cordat.remove_weekly(x, y, weekdays, correct_weeks = rm_weeks,
                                                           spline_s = 0, spline_k = 5)
                x = result_remove_weekly[0]
                y = np.exp(result_remove_weekly[2])
            x = x + time_shift
            y = y * scale_y
            traces.append(go.Scatter(x=x, y=y, mode='lines', line = {'color': cor_color[row]}))
    return traces

# ***********************************************************************
#
# This function creates traces from shadow dict data.
#
# A. Nittke 07/2021
# ***********************************************************************
def update_layout():
    layout = go.Layout(title='CoronaMultiView online',
                       yaxis={'type':'log', 'title': 'No of cases'},
                       xaxis={'title': 'Days after 22.01.2020'},
                       showlegend=False,
                       titlefont={'size': 30}
                       )
    return layout


# ***********************************************************************
#
# This function transforms a values list from checklist input to a numpy array
# with 0 (not checked) and 1 (checked)
#
# A. Nittke 07/2021
# ***********************************************************************
def checklist2shadow(values):
    values_bin = []
    for value in values:
        if len(value) == 0:
            values_bin.append(0)
        else:
            values_bin.append(1)
    return np.array(values_bin)


app.layout = html.Div([
    main_graph,
    html.Div(
        select_data_block,
    style = {
    'width': '45%', 'border': '2px red solid', 'borderRadius': 5, 'display':'inline-block'}),
    html.Div(id='trigger_graph_redraw', children='no update', style= {'display': 'none'})]
    )

if __name__ == '__main__':
    app.run_server()
