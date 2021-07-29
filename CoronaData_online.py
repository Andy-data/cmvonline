import pandas as pd 
import numpy as np
from datetime import datetime, timedelta, date
from scipy.interpolate import UnivariateSpline
from os import path, mkdir
import sys
import csv
import pickle
from bs4 import BeautifulSoup
from requests import get as req_get

class CoronaData():
    ''' CoronaData class handles data import, data formatting and the relevant calculations
    '''
    def __init__(self):
        self.start_date = datetime(2020, 1, 22)
        self.files = {'JHUGL': 'JHU.dict', 'JHU_US': 'JHU_US.dict', 'RKI': 'RKI.dict',
        'Worldometers': 'Worldometers.dict', 'RKI_Alter_corr': 'RKI_corr.dict',
        'DIVI': 'DIVI.dict'}
        self.local_files_dir = path.join('.', 'local_files')
        self.corona_dict = {}           # This is the central data storage
        self.sources = []               # List of data sources
        self.countries_level1 = []      # List of countries
        self.countries_level2 = []      # List of country parts
        self.limit = 1
        self.time_shift = 10            # Assumed time difference from infection to report
        self.limit_len = 10 #15
        self.show_counties = False
        # self.update_jhu_global_to_file(forced_update = False)
        # self.update_jhu_US_to_file(forced_update = False , show_counties = self.show_counties)
        # self.update_RKI_to_file(forced_update = False)
        # self.update_Worldometer_to_file(forced_update = False)
        # self.update_DIVI_to_file(forced_update = False)
        self.populate_dict()
        
    def populate_dict(self):
        input_dicts = []
        for _, file in self.files.items():
            dict_file = path.join(self.local_files_dir, file)
            try:
                with open(dict_file, 'rb') as f:
                    input_dicts.append(pickle.load(f))
            except:
                continue

        for i in range(len(input_dicts)):
            self.corona_dict = {**self.corona_dict, **input_dicts[i]}

        print(' read total: ',len(self.corona_dict.keys()))
        self.sources = []
        self.countries_level1 = []
        self.countries_level2 = []
        for c in self.corona_dict.keys():
            source, country_level1, country_level2 = c
            self.sources.append(source)
            self.countries_level1.append(country_level1)
            self.countries_level2.append(country_level2)
        self.sources = np.array(self.sources)
        self.countries_level1 = np.array(self.countries_level1)
        self.countries_level2 = np.array(self.countries_level2)
 
    def update_jhu_global_to_file(self, forced_update = False):
        if not path.exists(self.local_files_dir):
                mkdir(self.local_files_dir)
        dict_file = path.join(self.local_files_dir, self.files['JHUGL'])
        if path.isfile(dict_file) and datetime.fromtimestamp(path.getmtime(dict_file)).date() == date.today() and not forced_update:
            return
        url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
        import_df = pd.read_csv(url, error_bad_lines=False).transpose()
        import_df.reset_index(inplace = True)
        import_df.drop([2,3], inplace = True)
        import_df, timescale = self.clean_import_array(import_df, '%m/%d/%y')

        # import data on deaths:
        url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
        import_df_deaths = pd.read_csv(url, error_bad_lines=False).transpose()
        import_df_deaths.reset_index(inplace = True)
        import_df_deaths.drop([2,3], inplace = True)
        import_df_deaths, timescale_deaths = self.clean_import_array(import_df_deaths, '%m/%d/%y')

        if len(timescale) != len(timescale_deaths):
            print('Numbers of entries (infections / deaths) don´t match. Dumping timescales: \n')
            for i in range(max(len(timescale_deaths), len(timescale))):
                print(i, timescale[i], timescale_deaths[i])
        time_minmax = (min(timescale), max(timescale))
        # origin = ['jhu']*(import_df.shape[1]-1)
        countries = import_df.iloc[1,1:]
        regions = import_df.iloc[0,1:]
        countries_with_regions = np.unique(countries[np.where(pd.notnull(regions))[0]])
        for i, region in enumerate(regions):
            if pd.isnull(region):
                regions[i] = countries[i]
        c_dict = {}
        # first for countries with several regions:
        for country in countries_with_regions:
            region = '!_' + country + '_total'
            infs = np.array(import_df.iloc[2:,(np.where(countries == country)[0] + 1)].sum(axis = 1).astype('int32'))
            deaths = np.array(import_df_deaths.iloc[2:,(np.where(countries == country)[0] + 1)].sum(axis = 1).astype('int32'))
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            c_dict[('JHU_GL', country, region)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]

        # Now for all regions:
        for i, region in enumerate(regions):
            country = countries[i]
            # print(country, region)
            infs = np.array(import_df.iloc[2:,i + 1])
            deaths = np.array(import_df_deaths.iloc[2:,i + 1])
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            c_dict[('JHU_GL', country, region)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
        
        with open(dict_file, 'wb') as handle:
            pickle.dump(c_dict, handle)

        print('JHU global: ', len(c_dict.keys()))
        return 

    def update_jhu_US_to_file(self, forced_update = False, show_counties = False):
        if not path.exists(self.local_files_dir):
                mkdir(self.local_files_dir)
        dict_file = path.join(self.local_files_dir, self.files['JHU_US'])
        if path.isfile(dict_file) and datetime.fromtimestamp(path.getmtime(dict_file)).date() == date.today() and not forced_update:
            return
        url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
        import_df = pd.read_csv(url, error_bad_lines=False).transpose()
        import_df.reset_index(inplace = True)
        import_df.drop([0, 1, 2, 3, 4, 7, 8, 9, 10], inplace = True)
        import_df, timescale = self.clean_import_array(import_df, '%m/%d/%y')

        # import data on deaths:
        url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
        import_df_deaths = pd.read_csv(url, error_bad_lines=False).transpose()
        import_df_deaths.reset_index(inplace = True)
        import_df_deaths.drop([0, 1, 2, 3, 4, 7, 8, 9, 10, 11], inplace = True)
        import_df_deaths, timescale_deaths = self.clean_import_array(import_df_deaths, '%m/%d/%y')

        if len(timescale) != len(timescale_deaths):
            print('Numbers of entries (infections / deaths) don´t match. Dumping timescales: \n')
            for i in range(max(len(timescale_deaths), len(timescale))):
                print(i, timescale[i], timescale_deaths[i])
        time_minmax = (min(timescale), max(timescale))
        # origin = ['jhu']*(import_df.shape[1]-1)
        countries = import_df.iloc[1,1:]
        regions = import_df.iloc[0,1:]
        countries_with_regions = np.unique(countries[np.where(pd.notnull(regions))[0]])
        for i, region in enumerate(regions):
            if pd.isnull(region):
                regions[i] = countries[i]
        c_dict = {}
        # first for countries with several regions:
        for country in countries_with_regions:
            region = '!_' + country + '_total'
            infs = np.array(import_df.iloc[2:,(np.where(countries == country)[0] + 1)].sum(axis = 1).astype('int32'))
            deaths = np.array(import_df_deaths.iloc[2:,(np.where(countries == country)[0] + 1)].sum(axis = 1).astype('int32'))
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            if show_counties:
                c_dict[('JHU_US', country, region)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
            c_dict[('JHU_GL', 'US', country)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]

        # Now for all regions if show_counties = True:
        if show_counties:
            for i, region in enumerate(regions):
                country = countries[i]
                # print(country, region)
                infs = np.array(import_df.iloc[2:,i + 1])
                deaths = np.array(import_df_deaths.iloc[2:,i + 1])
                deaths_copy = np.copy(deaths)
                death_rate_stats = self.analyse_correlation(infs, deaths_copy)
                death_rate = death_rate_stats[:,0]
                death_rate_std = death_rate_stats[:,1]
                if np.where(death_rate > 0)[0].shape[0] > 0:
                    death_rate_len = np.max(np.where(death_rate > 0))
                else:
                    death_rate_len = 0
                c_dict[('JHU_US', country, region)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]

        with open(dict_file, 'wb') as handle:
            pickle.dump(c_dict, handle)
        print('JHU US: ', len(c_dict.keys()))
        return 

    def update_RKI_to_file(self, forced_update = False):
        if not path.exists(self.local_files_dir):
            mkdir(self.local_files_dir)
        dict_file = path.join(self.local_files_dir, self.files['RKI'])
        if path.isfile(dict_file) and datetime.fromtimestamp(path.getmtime(dict_file)).date() == date.today() and not forced_update:
            return
        c_dict = {}
        rki_csv_file = path.join(self.local_files_dir, 'RKI_Daten.csv')
        if not path.isfile(rki_csv_file) or datetime.fromtimestamp(path.getmtime(rki_csv_file)).date() != date.today():
            print('loading RKI data...')
            r = req_get('https://opendata.arcgis.com/datasets/dd4580c810204019a7b8eb3e0b329dd6_0.csv')
            with open(rki_csv_file, 'wb') as f:
                f.write(r.content)
            print('RKI data loaded.')

        RKI_df = pd.read_csv(rki_csv_file)
        RKI_df['days_Meldedat']= (((pd.to_datetime(RKI_df['Meldedatum']).dt.tz_localize(None))-np.datetime64(self.start_date))/ np.timedelta64(1, 'D')).astype(int)
        RKI_df['days_Refdat']= (((pd.to_datetime(RKI_df['Refdatum']).dt.tz_localize(None))-np.datetime64(self.start_date))/ np.timedelta64(1, 'D')).astype(int)
        RKI_df['Leerzeile'] = '!_Alle'
        # Altersgruppen in Bundesland
        RKI_df_cases = RKI_df[RKI_df.NeuerFall.isin([0,1])]
        RKI_df_cases_pivot = pd.pivot_table(RKI_df_cases, values='AnzahlFall', index=['days_Meldedat'], columns=['Bundesland', 'Leerzeile'], 
                aggfunc=np.sum).fillna(0)
        RKI_df_deaths = RKI_df[RKI_df.NeuerTodesfall.isin([0,1])]
        RKI_df_deaths_pivot = pd.pivot_table(RKI_df_deaths, values='AnzahlTodesfall', index=['days_Meldedat'], columns=['Bundesland', 'Leerzeile'], 
                aggfunc=np.sum).fillna(0)
        RKI_infs, timescale_infs = self.clean_RKI_array(RKI_df_cases_pivot)
        RKI_deaths, timescale_deaths = self.clean_RKI_array(RKI_df_deaths_pivot, refscale = timescale_infs)
        time_minmax = (min(timescale_infs), max(timescale_infs))

        RKI_index = RKI_infs.columns
        for land_level1, land_level2 in RKI_index[1:]:
            infs = np.array(RKI_infs[land_level1][land_level2]).astype(int)
            deaths = np.array(RKI_deaths[land_level1][land_level2].astype(int))
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            if land_level2 == '!_Alle':
                land_level_alter = '!_Alle_age'
                land_level_region = '!_Alle_reg'
            else:
                land_level_alter = land_level2
                land_level_region = land_level2
            c_dict[('RKIMA', land_level1, land_level_alter)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
            c_dict[('RKIMR', land_level1, land_level_region)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
        
        #*****************************************************
        # Deutschland gesamt Altersgruppen & Region Meldedatum
        #*****************************************************
        RKI_df_cases = RKI_df[RKI_df.NeuerFall.isin([0,1])]
        RKI_df_cases_pivot = pd.pivot_table(RKI_df_cases, values='AnzahlFall', index=['days_Meldedat'], columns=['Leerzeile', 'Altersgruppe'], 
                aggfunc=np.sum).fillna(0)
        RKI_df_deaths = RKI_df[RKI_df.NeuerTodesfall.isin([0,1])]
        RKI_df_deaths_pivot = pd.pivot_table(RKI_df_deaths, values='AnzahlTodesfall', index=['days_Meldedat'], columns=['Leerzeile', 'Altersgruppe'], 
                aggfunc=np.sum).fillna(0)
        RKI_infs, timescale_infs = self.clean_RKI_array(RKI_df_cases_pivot)
        RKI_deaths, timescale_deaths = self.clean_RKI_array(RKI_df_deaths_pivot, refscale = timescale_infs)
        time_minmax = (min(timescale_infs), max(timescale_infs))

        RKI_index = RKI_infs.columns
        for land_level1, land_level2 in RKI_index[1:]:
            infs = np.array(RKI_infs[land_level1][land_level2]).astype(int)
            deaths = np.array(RKI_deaths[land_level1][land_level2].astype(int))
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            c_dict[('RKIMA', '!_Deutschland', land_level2)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
        infs = np.sum(np.array(RKI_infs)[:,1:], axis = 1)
        deaths = np.sum(np.array(RKI_deaths)[:,1:], axis = 1)
        deaths_copy = np.copy(deaths)
        death_rate_stats = self.analyse_correlation(infs, deaths_copy)
        death_rate = death_rate_stats[:,0]
        death_rate_std = death_rate_stats[:,1]
        if np.where(death_rate > 0)[0].shape[0] > 0:
            death_rate_len = np.max(np.where(death_rate > 0))
        else:
            death_rate_len = 0
        c_dict[('RKIMA', '!_Deutschland', '!_Alle_age')] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
        c_dict[('RKIMR', '!_Deutschland', '!_Alle_reg')] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]
  
        #*******************************
        ## Altersgruppen nach Meldedatum
        #*******************************
        RKI_df_cases = RKI_df[RKI_df.NeuerFall.isin([0,1])]
        RKI_df_cases_pivot = pd.pivot_table(RKI_df_cases, values='AnzahlFall', index=['days_Meldedat'], columns=['Bundesland', 'Altersgruppe'], 
                aggfunc=np.sum).fillna(0)
        RKI_df_deaths = RKI_df[RKI_df.NeuerTodesfall.isin([0,1])]
        RKI_df_deaths_pivot = pd.pivot_table(RKI_df_deaths, values='AnzahlTodesfall', index=['days_Meldedat'], columns=['Bundesland', 'Altersgruppe'], 
                aggfunc=np.sum).fillna(0)
        RKI_infs, timescale_infs = self.clean_RKI_array(RKI_df_cases_pivot)
        RKI_deaths, timescale_deaths = self.clean_RKI_array(RKI_df_deaths_pivot, refscale = timescale_infs)
        time_minmax = (min(timescale_infs), max(timescale_infs))

        RKI_index = RKI_infs.columns
        for land_level1, land_level2 in RKI_index[1:]:
            infs = np.array(RKI_infs[land_level1][land_level2].astype(int))
            if (land_level1, land_level2) not in RKI_deaths.columns:
                deaths = np.arange(infs.shape[0])
            else:
                deaths = np.array(RKI_deaths[land_level1][land_level2].astype(int))
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            c_dict[('RKIMA', land_level1, land_level2)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]

        #**********************************
        ## Altersgruppen nach Referenzdatum
        #**********************************
        # not in use yet
        # RKI_df_cases = RKI_df[RKI_df.NeuerFall.isin([0,1]) & RKI_df.IstErkrankungsbeginn == 1]
        # RKI_df_cases_pivot = pd.pivot_table(RKI_df_cases, values='AnzahlFall', index=['days_Refdat'], columns=['Bundesland', 'Altersgruppe'], 
        #         aggfunc=np.sum).fillna(0)
        # RKI_df_deaths = RKI_df[RKI_df.NeuerTodesfall.isin([0,1])]
        # RKI_df_deaths_pivot = pd.pivot_table(RKI_df_deaths, values='AnzahlTodesfall', index=['days_Refdat'], columns=['Bundesland', 'Altersgruppe'], 
        #         aggfunc=np.sum).fillna(0)
        # RKI_infs, timescale_infs = self.clean_RKI_array(RKI_df_cases_pivot)
        # RKI_deaths, timescale_deaths = self.clean_RKI_array(RKI_df_deaths_pivot, refscale = timescale_infs)
        # time_minmax = (min(timescale_infs), max(timescale_infs))

        # RKI_index = RKI_infs.columns
        # for land_level1, land_level2 in RKI_index[1:]:
        #     infs = np.array(RKI_infs[land_level1][land_level2].astype(int))
        #     if (land_level1, land_level2) not in RKI_deaths.columns:
        #         deaths = np.arange(infs.shape[0])
        #     else:
        #         deaths = np.array(RKI_deaths[land_level1][land_level2].astype(int))
        #     deaths_copy = np.copy(deaths)
        #     death_rate_stats = self.analyse_correlation(infs, deaths_copy)
        #     death_rate = death_rate_stats[:,0]
        #     death_rate_std = death_rate_stats[:,1]
        #     if np.where(death_rate > 0)[0].shape[0] > 0:
        #         death_rate_len = np.max(np.where(death_rate > 0))
        #     else:
        #         death_rate_len = 0
        #     c_dict[('RKI_RefDat_Alter', land_level1, land_level2)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]

        #****************
        # Regionen Meldedatum
        #*****************
        RKI_df_cases = RKI_df[RKI_df.NeuerFall.isin([0,1])]
        RKI_df_cases_pivot = pd.pivot_table(RKI_df_cases, values='AnzahlFall', index=['days_Meldedat'], columns=['Bundesland', 'Landkreis'], 
                aggfunc=np.sum).fillna(0)
        RKI_df_deaths = RKI_df[RKI_df.NeuerTodesfall.isin([0,1])]
        RKI_df_deaths_pivot = pd.pivot_table(RKI_df_deaths, values='AnzahlTodesfall', index=['days_Meldedat'], columns=['Bundesland', 'Landkreis'], 
                aggfunc=np.sum).fillna(0)
        RKI_infs, timescale_infs = self.clean_RKI_array(RKI_df_cases_pivot)
        RKI_deaths, timescale_deaths = self.clean_RKI_array(RKI_df_deaths_pivot, refscale = timescale_infs)
        time_minmax = (min(timescale_infs), max(timescale_infs))

        RKI_index = RKI_infs.columns
        for land_level1, land_level2 in RKI_index[1:]:
            infs = np.array(RKI_infs[land_level1][land_level2].astype(int))
            if (land_level1, land_level2) not in RKI_deaths.columns:
                deaths = np.arange(infs.shape[0])
            else:
                deaths = np.array(RKI_deaths[land_level1][land_level2].astype(int))
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            c_dict[('RKIMR', land_level1, land_level2)] = [infs, deaths, death_rate,
                                    death_rate_std, death_rate_len, time_minmax]

        with open(dict_file, 'wb') as handle:
            pickle.dump(c_dict, handle)
        print('RKI: ', len(c_dict.keys()))

    def update_Worldometer_to_file(self, forced_update = False):
        if not path.exists(self.local_files_dir):
            mkdir(self.local_files_dir)
        dict_file = path.join(self.local_files_dir, self.files['Worldometers'])
        if path.isfile(dict_file) and datetime.fromtimestamp(path.getmtime(dict_file)).date() == date.today() and not forced_update:
            return
        c_dict = {}
        # First: Load list of countries with links 
        # *********************************************
        r = req_get('https://www.worldometers.info/coronavirus/#countries')   
        bsdoc = BeautifulSoup(r.text, "html.parser")
        #wm_table = bsdoc.find(id = "main_table_countries_today")
        wm_tables = bsdoc.find_all('table')
        target_table = wm_tables[0]
        wm_lines = target_table.find_all('tr')
        wm_dict = {}
        for i, wm_line in enumerate(wm_lines[9:-8]):
            wm_cells = wm_line.find_all('td')
            wm_line_data = []
            for j, wm_cell in enumerate(wm_cells):
                #print('Zeile {} Zelle {}: {}'.format(i,j,wm_cell.contents))
                try:
                    if len(wm_cell.contents) == 0:
                        wm_line_data.append('')
                        continue
                except:
                    wm_line_data.append('')
                if j == 0:
                    continue
                if j == 1:
                    try:
                        wm_country = wm_cell.a
                        country = wm_country.contents[0]
                        wm_line_data.append(wm_country['href'])
                    except:
                        try:
                            country = wm_cell.contents[0]
                        except:
                            country = wm_cell.contents
                else:
                    cell_content = wm_cell.contents[0]
                    try: 
                        result = int(cell_content.replace(',',''))
                    except:
                        try:
                            result = int(wm_cell.a.contents[0].replace(',',''))
                        except:
                            result = cell_content
                    wm_line_data.append(result)
            wm_dict[str(country)] = wm_line_data
        wm_countries = []
        for key in wm_dict.keys():
            wm_countries.append(key)
            #print(key, wm_dict[key][0], '\n')
        wm_countries.sort()
        # import only selected country data:
        #***********************************
        for country in ['Germany', 'France', 'Spain', 'USA', 'Sweden', 'Switzerland', 'Netherlands', 'Italy',
        'Belgium', 'Austria', 'UK', 'China', 'Japan', 'Poland', 'Czechia', 'Ireland', 'Portugal', 'Denmark',
        'South Africa']:
            worldometer_path = path.join('https://www.worldometers.info/coronavirus/', wm_dict[country][0])
            print(worldometer_path)
            r = req_get(worldometer_path)
            bsdoc = BeautifulSoup(r.text, "html.parser")
            daily_cases_graph_1 = bsdoc.find_all('script', type="text/javascript")
            for dcg in daily_cases_graph_1:
                b = str(dcg.get_text)
                #print(dcg.get_text)
                if 'graph-deaths-daily' in b:
                    start = b.find("name: 'Daily Deaths'")
                    x_start = b[start:].find('[')
                    x_end = b[start:].find(']')
                    data_deaths = eval(b[x_start+start:x_end+start+1].replace('null', '0'))

                    start = b.find('categ')
                    x_start = b[start:].find('[')
                    x_end = b[start:].find(']')
                    data_x = b[x_start+start:x_end+start+1]
                if 'graph-cases-daily' in b:
                    start = b.find("name: 'Daily Cases'")
                    x_start = b[start:].find('[')
                    x_end = b[start:].find(']')
                    data_cases = eval(b[x_start+start:x_end+start+1].replace('null', '0'))
            timescale = data_x[2:-2].split('","') # split time string into dates, ignoring leading '["' and ending '"]"
            cor_days = []
            for i, cor_date in enumerate(timescale):
                cor_date_date = datetime.strptime(cor_date, '%b %d, %Y')
                cor_days.append((cor_date_date - self.start_date).days)
            cor_days_max = max(cor_days)
            for i, _ in enumerate(cor_days):
                if i == 0:
                    continue
                if cor_days[i] - cor_days[i-1] < 0:
                    cor_days[i] = cor_days[i] + 366

            if list(range(cor_days[0], cor_days[-1] + 1)) == cor_days:
                deaths = np.array([0] * cor_days[0] + data_deaths)
                infs = np.array([0] * cor_days[0] + data_cases)
                cor_days = np.array(list(range(cor_days[0])) + cor_days)
            else:
                pass
            deaths_copy = np.copy(deaths)
            death_rate_stats = self.analyse_correlation(infs, deaths_copy)
            death_rate = death_rate_stats[:,0]
            death_rate_std = death_rate_stats[:,1]
            if np.where(death_rate > 0)[0].shape[0] > 0:
                death_rate_len = np.max(np.where(death_rate > 0))
            else:
                death_rate_len = 0
            time_minmax = (min(cor_days), max(cor_days))
            c_dict[('WDM', country, country)] = [infs, deaths, death_rate, death_rate_std, death_rate_len, time_minmax]

        with open(dict_file, 'wb') as handle:
            pickle.dump(c_dict, handle)
        print('Worldometers: ', len(c_dict.keys()))

    def update_DIVI_to_file(self, forced_update=False):
        if not path.exists(self.local_files_dir):
            mkdir(self.local_files_dir)
        dict_file = path.join(self.local_files_dir, self.files['DIVI'])
        if path.isfile(dict_file) and datetime.fromtimestamp(path.getmtime(dict_file)).date() == date.today() and not forced_update:
            return
        c_dict = {}
        DIVI_df = pd.read_csv('https://diviexchange.blob.core.windows.net/%24web/bundesland-zeitreihe.csv')
        DIVI_df.insert(0, 'Datum_Tag', 'x')
        DIVI_df['Datum_Tag'] = [(datetime.strptime(x[:10],'%Y-%m-%d') - self.start_date).days \
                                    for x in DIVI_df['Datum']]  #(date - self.start_date).days
        DIVI_df.drop(columns='Datum', inplace=True)
        print(DIVI_df.columns)
        DIVI_pivot_df = pd.pivot_table(DIVI_df, 
                    values=['Aktuelle_COVID_Faelle_Erwachsene_ITS', 'Belegte_Intensivbetten_Erwachsene'],
                    index=['Datum_Tag'], 
                    columns=['Bundesland'], 
                    aggfunc=np.sum).fillna(0)
        DIVI_pivot_df.rename(columns={'DEUTSCHLAND': '!_DEUTSCHLAND'}, inplace=True)

        DIVI_pivot_df_clear, timescale = self.clean_RKI_array(DIVI_pivot_df)
        death_rate_len = 0
        leere_liste = np.zeros(len(timescale))
        time_minmax = (min(timescale), max(timescale))
        _, country_list = zip(*DIVI_pivot_df_clear.columns)
        country_list = np.unique(list(country_list[1:]))
        for country in country_list:
            c_dict[('z_DIVI_Covid_intensiv', country, country)] = \
                            [DIVI_pivot_df_clear.loc[:, ('Aktuelle_COVID_Faelle_Erwachsene_ITS', country)],
                            DIVI_pivot_df_clear.loc[:, ('Belegte_Intensivbetten_Erwachsene', country)], 
                            leere_liste, leere_liste, death_rate_len, time_minmax]
        with open(dict_file, 'wb') as handle:
            pickle.dump(c_dict, handle)
        print('DIVI: ', len(c_dict.keys()))  

    def clean_RKI_array(self, import_df, refscale = [0, 0]):
        import_df.reset_index(inplace = True)
        cor_days = (import_df.values[:,0]).astype('int')
        
        # fill missing values rows
        import_df_data = import_df.iloc[2:,:]
        import_df['day_nr'] = cor_days
        # fill in dates with no report
        null_list = [0]*import_df.shape[1]
        last_date = max(max(refscale) + 1, max(cor_days) + 1)
        missing_dates = np.setdiff1d(list(range(last_date)), cor_days)
        null_df = pd.DataFrame([null_list]*len(missing_dates), columns = import_df.columns, index = missing_dates)
        null_df['day_nr'] = missing_dates
        import_df =  import_df.append(null_df)
        import_df.sort_values('day_nr', inplace = True)
        # drop rows before start_date
        import_df = import_df[import_df['day_nr'] >= 0]
        timescale = import_df['day_nr']
        # column 'day_nr' is not needed any more:
        import_df.drop(['day_nr'], axis = 1, inplace = True)
        # add header and data:

        return import_df, timescale

    def clean_import_array(self, import_df, dateformat):
        timescale = import_df.values[2:,0]
        cor_days = []
        for i, cor_date in enumerate(timescale):
            date = datetime.strptime(cor_date, dateformat)
            cor_days.append((date - self.start_date).days)
        # fill missing values rows
        import_df_header = import_df.iloc[:2,:]
        import_df_data = import_df.iloc[2:,:].copy(deep=True)
        import_df_data.iloc[:, 1:] = import_df_data.iloc[:, 1:].diff()
        import_df_data.iloc[0, 1:] = 0
        import_df_data['day_nr'] = cor_days
        # fill in dates with no report
        null_list = [0]*import_df_data.shape[1]
        missing_dates = np.setdiff1d(list(range(max(cor_days)+1)), cor_days)
        null_df = pd.DataFrame([null_list]*len(missing_dates), columns = import_df_data.columns, index = missing_dates)
        null_df['day_nr'] = missing_dates
        import_df_data =  import_df_data.append(null_df)
        import_df_data.sort_values('day_nr', inplace = True)
        # drop rows before start_date
        import_df_data = import_df_data[import_df_data['day_nr'] >= 0]
        timescale = import_df_data['day_nr']
        # column 'day_nr' is not needed any more:
        import_df_data.drop(['day_nr'], axis = 1, inplace = True)
        # add header and data:
        import_df = import_df_header.append(import_df_data)

        return import_df, timescale

    def analyse_correlation(self, c_i, c_d):
        # c_i: 1-dim array of infected per day
        # c_d: 1-dim array of deaths per day
        offset = 100  # only the first offset days are considered for analysis
        c_d[offset:]=0 # ignore the rest
        num_entries = c_i.shape[0]
        correl_results = np.zeros((num_entries, 4))
        for shift in range(offset): #num_entries
            c_d1 = c_d
            if shift >0:
                c_d1 = np.roll(c_d1,-shift)
                c_d1[-shift:]=0
            temp_i = []
            temp_d = []
            for i,_ in enumerate(c_i):
                if c_i[i] > self.limit and c_d1[i] > self.limit:
                    temp_i.append(np.log(c_i[i]))
                    temp_d.append(np.log(c_d1[i]))
            temp_i = np.array(temp_i)
            temp_d = np.array(temp_d)
            diff = temp_i-temp_d
            c_mean = np.mean(diff)
            c_std = np.std(diff)
            c_var = np.var(diff)
            if not np.isnan(c_mean) and not np.isnan(c_std) and not np.isnan(c_var) and len(temp_i) > self.limit_len:
                correl_results[shift,0] = np.exp(-c_mean)
                correl_results[shift,1] = c_std
                correl_results[shift,2] = c_var
                correl_results[shift,3] = len(temp_i)
        return correl_results

    def find_mins(self, series_of_values):
        # all_data = True: return all values in the necessary format
        LIMFACTOR = 1.5
        rising = True
        list_mins = []
        prev_val = series_of_values[0]
        #mins_counter = 0
        for i in range(1,series_of_values.shape[0]):
            #print('Start: i {} prev_val {}, series_of_values[i] {} rising {}'.format(i, prev_val[0], series_of_values[i][0], rising ))
            if series_of_values[i] > prev_val:
                if rising == False and prev_val != 0:       # ignore zeros
                    list_mins.append([i-1,prev_val])
                rising = True
            else: 
                if series_of_values[i] > 0:
                    rising = False
            prev_val = series_of_values[i]        
        list_mins = np.array(list_mins, dtype = 'float')
        if list_mins.size != 0:
            list_mins = list_mins[np.argsort(list_mins, axis=0)[:,1]]
            list_mins = list_mins[np.where(np.array(list_mins[:,1]) < LIMFACTOR*list_mins[0,1])]
        return list_mins

    def remove_weekly(self, x, y, weekdays, correct_weeks = 6, spline_s = 1, spline_k = 5):
        '''remove_weekly removes periodic variations on weekly time scale.
        x: time scale,
        y: values,
        weekdays: weekday corresponding to x encoded as int,
        correct_weeks: total number of weeks to take into account for correction,
        spline_s: control parameter for spline (the smaller the less precise),
        spline_k: polynomial degree of spline.'''

        if len(list(x)) != len(list(y)) or len(list(y)) != len(list(weekdays)):
            print('x, y and weekdays have to have the same dimension!')
            return
        # y as np-array
        y = np.array(y, dtype = 'float')
        # correct_region in days
        correct_region = 7 * correct_weeks
        # start where y>0
        start_index = next((i for i, x in enumerate(y) if x), None)
        inf_time = x[start_index:]
        inf_weekdays = weekdays[start_index:]
        # replace values <=0 by 0.1 to avoid problems on log scale and transform to log scale
        inf_log = np.log(np.where(y > 0.0, y, 0.1)[start_index:])

        # Define spline spl
        if len(inf_time) < 40:
            # only a few data points, use data for spline without further treatment
            spl = UnivariateSpline(inf_time, inf_log, s=20, k=5)
        else:
            # create a reduced timescale with only one point per week
            spl_time = []
            spl_inf_log = []
            # spl_time is a reduced time scale with oly one point per week,
            # spl_inf_log contains the corresponding y values averaged over one week, on log scale
            for i in range(3,len(inf_time)-3, 7):
                spl_time.append(inf_time[i])
                spl_inf_log.append(np.log(np.mean(np.exp(inf_log[i-3:i+4]))))

            try:
                spl = UnivariateSpline(spl_time, spl_inf_log, s = spline_s, k = spline_k)
            except:
                # Something went wrong, most probably due to inappropriate parameters  spline_s and spline_k
                # use safe standard parameters without averaging
                spl = UnivariateSpline(inf_time, inf_log, s=20, k=5)

        # calculate spline values for original time scale:
        inf_log_spline = spl(inf_time)
        # res_spline: residuals (deviations of data from spline) on log scale
        res_spline = inf_log - inf_log_spline
        # create correct_day_indices as array of "weekdays"
        correct_day_indices = np.arange(0,7)
        if len(inf_time) < 3 * correct_region:
            # length of inf_time is less than 3 * correct_region, so
            # calculate weekday-dependent correction globally:
            print("standard correction\n")
            # correct_residuals is a list of the median values of the residuals
            # for every weekday
            correct_residuals = [np.median(res_spline[np.where(weekdays[start_index:] == correct_day_indices[i])]) \
                                 for i in range(len(correct_day_indices))]
            # correction will be a numpy array containing the correction values
            # for every day in inf_time
            correction = np.zeros(len(inf_time))
            for i, t in enumerate(inf_time):
                if np.isnan(inf_weekdays[i]):
                    # in case of any problem
                    correction[i] = 0
                    print("isnan-Schleife!")
                else:
                    correction[i] = correct_residuals[int(inf_weekdays[i])]
        else:
            # Here, correction is calculated from a limited time range around
            # the respective date. Thus, the algorithm can adopt to changes in
            # weekly reporting strategies.

            # initialize correction array with 3's
            # will be overwritten, but will be visible if not
            correction = np.ones(len(inf_time)) * 3
            # use standard correction (see above) for start and end regions:
            # start region:         
            res_spline_tmp = res_spline[:correct_region]
            weekdays_tmp = inf_weekdays[:correct_region]
            correct_residuals = [np.median(res_spline_tmp[np.where(weekdays_tmp == correct_day_indices[i])]) for i in range(len(correct_day_indices))]
            for i in range(correct_region):
                correction[i] = correct_residuals[int(inf_weekdays[i])]
            # end region:
            res_spline_tmp = res_spline[-correct_region:]
            weekdays_tmp = inf_weekdays[-correct_region:]
            correct_residuals = [np.median(res_spline_tmp[np.where(weekdays_tmp == correct_day_indices[i])]) for i in range(len(correct_day_indices))]
            for i in range(len(inf_time) - correct_region, len(inf_time)):
                correction[i] = correct_residuals[int(inf_weekdays[i])]
            # intermediate region:
            correct_region_half = int(correct_region / 2)
            # for every point from the middle of start region to the middle of th eend region
            # correction is calculated "manually" as median of the residuals on the respective weekday
            # in a time range of +/- half the correct_region
            for i in range(correct_region_half, len(inf_time) - correct_region_half):
                res_spline_tmp = res_spline[i - correct_region_half:i + correct_region_half]
                weekdays_tmp = inf_weekdays[i - correct_region_half:i + correct_region_half]
                correction[i] =  np.median(res_spline_tmp[np.where(weekdays_tmp == inf_weekdays[i])])
        # smoothing by a running average with n=3 (+/- one neighbour)
        # add 1 point at both ends on a temporary array
        inf_corr_0 = np.zeros(len(inf_log) + 2)
        inf_corr_0[1:-1] = np.exp(inf_log - correction)
        inf_corr_0[0] = inf_corr_0[1]
        inf_corr_0[-1] = inf_corr_0[-2]
        inf_log_corr = np.zeros(len(inf_log))
        for i in range(1, len(inf_corr_0) - 1):
            inf_log_corr[i-1] = np.log(np.mean(inf_corr_0[i-1:i+2]))

        # inf_time: time in days, starting with 1st non-zero value of y
        # inf_log: log(y) corresponding to inf_time
        # inf_log_corr: inf_log corrected 
        # correction: correction on log scale, corresponding to inf_time
        # inf_weekdays: corresponding weekdays to inf_time
        # correct_day_indices: [0,1,2,3,4,5,6]
        # correct_residuals: correction per weekday, len = 7
        # res_spline: Deviation from spline on log scale, corresponding to inf_time
        # inf_log_spline: spline corresponding to inf_time
        return inf_time, inf_log, inf_log_corr, correction, inf_weekdays, correct_day_indices, correct_residuals, res_spline, inf_log_spline

    def export_current_curve(self, index, spline_s, spline_k, correct_weeks, R_time, R_infs):
        if not path.exists(self.local_files_dir):
            mkdir(self.local_files_dir)
        source, country_level1, country_level2 = index
        csvfile = path.join(self.local_files_dir, '_'.join([date.today().strftime('%y%m%d'), source, country_level1, country_level2, \
            's', str(spline_s), 'k', str(spline_k), 'range', str(correct_weeks), '.csv']))
        infs, deaths, _, _, _, time_minmax = self.corona_dict[index]
        timescale = np.arange(time_minmax[0], time_minmax[1] + 1)
        weekdays = np.array([(self.start_date + timedelta(days = int(i))).weekday() for i in timescale])
        time_1, inf_log, inf_log_corr, correction, weekday, correct_day_indices, correct_residuals, res_spline, inf_log_spline = \
                                        self.remove_weekly(timescale, infs, weekdays, correct_weeks, spline_s = spline_s, spline_k = spline_k)
        time_2, death_log, death_log_corr, corr_deaths, _, _, _, _, deaths_log_spline = \
                                        self.remove_weekly(timescale, deaths, weekdays, correct_weeks, \
                                        spline_s = spline_s, spline_k = spline_k)
        inf_log_corr = np.hstack((np.zeros(len(infs) - len(inf_log_corr)), inf_log_corr))
        death_log_corr = np.hstack((np.zeros(len(infs) - len(death_log_corr)), death_log_corr))
        with open(csvfile, 'w') as csv_f:
            csv_writer = csv.writer(csv_f, delimiter = ';', lineterminator = '\n')
            for i in range(1, len(timescale)):
                time_output = datetime.strftime(self.start_date + timedelta(days = int(timescale[i])), '%d.%m.%Y')
                csv_writer.writerow([timescale[i], time_output,  infs[i], deaths[i], int(np.exp(inf_log_corr[i])), int(np.exp(death_log_corr[i])), int(R_infs[int(10*(i-1))])])


if __name__ == '__main__':
    cordat = CoronaData()


    sys.exit(0)