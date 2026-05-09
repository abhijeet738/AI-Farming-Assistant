
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def engineer_features(dataframe):
    df_new = dataframe.copy()
    df_new['N_P_ratio'] = df_new['N'] / (df_new['P'] + 1)
    df_new['N_K_ratio'] = df_new['N'] / (df_new['K'] + 1)
    df_new['P_K_ratio'] = df_new['P'] / (df_new['K'] + 1)
    df_new['NPK_total'] = df_new['N'] + df_new['P'] + df_new['K']
    df_new['N_dominant'] = ((df_new['N'] > df_new['P']) & (df_new['N'] > df_new['K'])).astype(int)
    df_new['P_dominant'] = ((df_new['P'] > df_new['N']) & (df_new['P'] > df_new['K'])).astype(int)
    df_new['K_dominant'] = ((df_new['K'] > df_new['N']) & (df_new['K'] > df_new['P'])).astype(int)
    df_new['temp_humidity_index'] = df_new['temperature'] * df_new['humidity'] / 100
    df_new['rainfall_temp_ratio'] = df_new['rainfall'] / (df_new['temperature'] + 1)
    df_new['aridity_index'] = df_new['temperature'] / (df_new['rainfall'] + 1)
    df_new['ph_deviation'] = abs(df_new['ph'] - 7.0)
    df_new['ph_category'] = pd.cut(df_new['ph'], bins=[0,5.5,6.5,7.5,8.5,14], labels=[0,1,2,3,4]).astype(int)
    df_new['rainfall_category'] = pd.cut(df_new['rainfall'], bins=[0,50,100,150,200,300,500], labels=[0,1,2,3,4,5]).astype(int)
    df_new['temp_zone'] = pd.cut(df_new['temperature'], bins=[0,15,25,35,50], labels=[0,1,2,3]).astype(int)
    df_new['tropical_score'] = (MinMaxScaler().fit_transform(df_new[['temperature']])*0.33 + MinMaxScaler().fit_transform(df_new[['humidity']])*0.33 + MinMaxScaler().fit_transform(df_new[['rainfall']])*0.34).flatten()
    npk_scaled = MinMaxScaler().fit_transform(df_new[['N','P','K']])
    df_new['nutrient_score'] = npk_scaled.mean(axis=1)
    return df_new
