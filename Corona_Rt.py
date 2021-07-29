from datetime import datetime, timedelta, date
import numpy as np
from os import path

class Rt():
    ''' class R handles the time dependent R function and the 
    calculated infections derived from this function '''
    def __init__(self, cordat):
        self.country = ''
        self.gen = 4     # Generation: 4 days
        self.x_max = 1   
        self.last_model_valid = False
        self.last_R_steps = []
        self.R_dict = {}
        self.load_R_table()
        self.cordat = cordat

    def get_R_func(self, country, time_minmax):
        R_model_valid = True
        x_max = time_minmax[1] + 5
        if not (country == self.country and x_max == self.x_max and self.last_model_valid):         # no change, just return data      
            if country in self.R_dict.keys():                              # country in list, create functions
                self.create_func_data(country, x_max)
                self.last_model_valid = True
            else:                                                   # country not in list, create dummy
                R_model_valid = False
                self.last_model_valid = False
                self.time_R = np.arange(1, x_max, 0.1)
                self.R_func = np.ones(10 * (x_max - 1), dtype = 'float')
        return self.time_R, self.R_func, R_model_valid 

    def get_inf_R(self, country, time_minmax):
        R_model_valid = True
        x_max = time_minmax[1] + 5
        if not (country == self.country and x_max == self.x_max and self.last_model_valid):         # no change, just return data      
            if country in self.R_dict:    
                print('country in dict')                          # country in list, create functions
                self.create_func_data(country, x_max)
                self.last_model_valid = True
            else:                                                   # country not in list, create dummy
                R_model_valid = False
                self.last_model_valid = False
                self.time_R = np.arange(1, x_max, 0.1)
                self.infected_R = np.ones(10 * (x_max - 1))
        return self.time_R, self.infected_R, R_model_valid   

    def create_func_data(self, country, x_max):  # get dict entries, calculate R-function, calculate infected
        self.x_max = x_max
        self.country = country
        steps = self.R_dict[country]            # tuples which define steps in R
        int_const = 1.0                         # integration constant
        integration_steps = 100
        R_temp=[]
        switch_r=[]
        for i in range(len(steps)):
            R_temp.append(steps[i][1])
            switch_r.append(steps[i][0])
        if len(switch_r) > 0:
            del switch_r[0]
        switch_r.append(1000)
        R = list(reversed(R_temp))
        switch = list(reversed(switch_r))
        x_for_int = np.arange(1, x_max, 1/integration_steps)   # timescale for integration
        int_func = np.zeros(len(x_for_int))     # empty array for R-function creation
        for i, t in enumerate(x_for_int):
            for j in range(len(switch)):
                    if t < switch[j]:
                        int_func[i] = R[j]
        f_prime = np.log(int_func)/self.gen      # derivation of infected per day on log scale   
        infected_raw = np.zeros(len(f_prime))
        for i, t in enumerate(f_prime):
            if i == 0:
                continue
            else:
                infected_raw[i] = infected_raw[i-1] + (f_prime[i]+f_prime[i-1])/2 * (x_for_int[i]-x_for_int[i-1])
        self.time_R = np.arange(1, x_max, 0.1)
        self.R_func = np.ones(self.time_R.shape[0], dtype = 'float')
        self.infected_R = np.ones(self.time_R.shape[0], dtype = 'float')
        for i in range(len(self.time_R)):
            self.R_func[i] = int_func[int(i*integration_steps/10)]
            self.infected_R[i] = infected_raw[int(i*integration_steps/10)]
        self.infected_R = int_const*np.exp(self.infected_R)         # Store calulated infected in infected_R
        self.last_R_steps = self.R_dict[country] # remember R_steps 

    def update_str(self, R_step_string, country):
        R_clean = ''
        for c in R_step_string:
            if c in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '(', ')', ',', '.', 'e', 'E']: # no need to import re module for this simple task :-)
                R_clean += c
        if R_clean == '':
            return False
        try:
            self.R_dict[country] = eval('[' + R_clean + ']')   
        except:
            return
    
    def save_R_table(self):
        R_table = ''
        for country in self.R_dict.keys():
            R_table += repr(country) + '; ' + str(self.R_dict[country]) + '\n'
        with open('R_table.dict', 'w') as f:
            f.write(R_table)

    def load_R_table(self):
        if not path.exists('R_table.dict'):
            with open('R_table.dict', 'w') as f:
                f.write('("JHU_GL", "Germany", "Germany"); [(0, 1), (25, 2.7), (57, 1.4), (64, 1.05), (71, 0.8), (100, 0.85), (141, 1.8), (149, 0.85), (168, 1.15), (212, 0.9), (221, 1.1), (255, 1.33), (284, 0.98), (312, 1.1), (325, 1.02)]')
        with open('R_table.dict', 'r') as f:
            lines = f.readlines()
        for line in lines:
            country_str, R_steps = line.split(';')
            country = eval(country_str)     # country is now a tuple
            self.update_str(R_steps, country)
        self.country = 'reset_list'

