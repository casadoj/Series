import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from cartopy.feature import ShapelyFeature
from cartopy.io.shapereader import Reader
# from mpl_toolkits.basemap import Basemap, cm
import warnings
warnings.filterwarnings('ignore')

def analisis_calidad(serie, times_res):
    from itertools import groupby
    from datetime import date
    """ Mediante esta función realizamos un análisis de calidad de series
    
    Parameters:
    -----------
    serie: serie de datos que se quiere analizar. Se requiero que el index sea un Datetime
    
    times_res: 1 si son datos diarios, 24 sin son horarias y 144, introducir como Integer
    
    Serie: introducir la serie que se desea analizar"
    
    año_ini: introducir el año inicial a partir del cual se quiere realizar el análisis
    
    Output:
    -------
    n_años_completos: nº de años que contienen datos todos los días
    por_huecos: porcentaje de huecos de la serie en %
    n_años_con_dato: nº de años que contienen datos
    n_meses_completos: número de meses que contienen datos todos los días
    n_dias_completos: en el caso en que la resolución sea horaria, nº de días que contienen datos todos las horas
    año_inicio: año de inicio de la serie
    año_fin: año de fin de la serie """
    
    serie=serie.astype(np.float64)
    año_ini=serie.dropna().index.year[0]
    res=times_res
    data=serie[serie.index.year>=año_ini]
    global n_max_años_consecutivos
    if len(data)==0 or np.isnan(np.nanmax(data))==True:
        n_años_completos=np.nan
        por_huecos=np.nan
        n_años_con_dato=np.nan
        n_meses_completos=np.nan
        n_max_años_consecutivos=np.nan
        n_min_años_consecutivos=np.nan
        año_inicio=np.nan
        año_fin=np.nan
    else:
        año_inicio=np.min(serie.dropna().index.year.values)
        data=serie[serie.index.year>=año_inicio]
        d0 = data.index[0]
        d1 = data.index[-1]
        delta = d1 - d0
        data_0=data.copy()
        data_0[np.isnan(data_0)==False]=1
        data_1=data_0.resample('A').sum()
        data_2=data_0.resample('M').sum()
        porc_dias_meses=data_2.values.T/data_2.index.day.values
        n_años_completos=list(data_1.values).count(365*res)+list(data_1.values).count(366*res)
        por_huecos=(1-len(data.dropna())/delta.days)*100
        n_años_con_dato=np.sum(data_1.values>0)
        n_meses_completos=len(porc_dias_meses[porc_dias_meses==1])
        data_1[data_1<365*res]=np.nan
        data_1[data_1>=365*res]=1
        count_dups = np.array([sum(1 for _ in group) for _, group in groupby(list(data_1.values))])
#         n_min_años_consecutivos=np.min(count_dups)
#         n_max_años_consecutivos=np.max(count_dups)
        año_fin=np.max(serie.dropna().index.year.values)
        if res!=1:
            por_huecos=(1-len(data.dropna())/24)*100
            data_2=data_0.resample('D').sum()
            porc_horas_dias=data_2.values.T/24
            n_dias_completos=len(porc_horas_dias[porc_horas_dias==1])
            return(n_años_completos,por_huecos,n_años_con_dato,n_meses_completos,n_dias_completos,año_inicio,año_fin)
        else:
            return(n_años_completos,por_huecos,n_años_con_dato,n_meses_completos,año_inicio,año_fin)
