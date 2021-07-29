from datetime import datetime as dt

from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
import numpy as np


def register_callbacks(app, max_rows):

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

