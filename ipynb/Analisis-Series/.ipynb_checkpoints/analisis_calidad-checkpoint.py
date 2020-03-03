# _Autor:_    __Salavador Navas__
# _Revisión:_ __03/03/2020__

import numpy as np
import pandas as pd
from itertools import groupby
from datetime import date
import calendar


def analisis_calidad(serie, res):
    """Análisis de la calidad de una serie temporal
    
    Parameters:
    -----------
    serie:             pandas.Series. Serie de datos que se quiere analizar. El índice debe ser de tipo Datetime
    res:               integer. Resolución temporal de la serie en nº de pasos temporales por día: 1, diaria; 24 horaria; 144, diezminutal; ...
    
    Output:
    -------
    n_años_completos:  int. Nº de años que contienen datos todos los días
    por_huecos:        float. % de huecos de la serie
    n_años_con_dato:   int. Nº de años que contienen datos
    n_meses_completos: int. Nº de meses que contienen datos todos los días
    n_dias_completos:  int. En el caso en que la resolución sea horaria, nº de días que contienen datos todos las horas
    año_inicio:        int. Año de inicio de la serie
    año_fin:           int. Año de fin de la serie
    """

    serie = serie.astype(np.float64)
    
    # primer y último paso temporal con dato
    start, end = serie.first_valid_index(), serie.last_valid_index()
    delta = end - start
    año_inicio, año_fin = start.year, end.year
    data = serie.loc[start:end]

    # global n_max_años_consecutivos # importar la variable global 'n_max_años_consecutivos'
    
    if (len(data) == 0) or (np.isnan(data).all()): # la serie está vacía
        por_huecos = np.nan
        n_años_con_dato = np.nan
        n_años_completos = np.nan
        n_meses_completos = np.nan
#         n_max_años_consecutivos = np.nan
#         n_min_años_consecutivos = np.nan
    else:
        # % de huecos
        por_huecos = (1 - data.count() / (delta.days * res)) * 100

        # DISPONIBILIDAD ANUAL DE DATOS
        dataA = data.resample('A').count()
        # nº años con dato
        n_años_con_dato = (dataA > 0).sum()
        # nº años completos
        daysYear = np.array([366 if calendar.isleap(year) else 365 for year in dataA.index.year ])
        n_años_completos = (dataA == daysYear * res).sum()

        # DISPONIBILIDAD MENSUAL DE DATOS
        dataM = data.resample('M').count()
        # nº meses completos
        n_meses_completos = (dataM == dataM.index.day).sum()
        
#         dataA[dataA < 365 * res] = np.nan
#         dataA[dataA >= 365 * res] = 1
#         count_dups = np.array([sum(1 for _ in group) for _, group in groupby(list(data_1.values))])
#         n_min_años_consecutivos = np.min(count_dups)
#         n_max_años_consecutivos = np.max(count_dups)

    if res > 1: # resolución superior a la diaria
        # DISPONIBILIDAD DIARIA DE DATOS
        dataD = data.resample('D').count()
        # nº de días completos>
        n_dias_completos = (dataD == res).sum()
        return n_años_completos, por_huecos, n_años_con_dato, n_meses_completos, n_dias_completos, año_inicio, año_fin
    else:
        return n_años_completos, por_huecos, n_años_con_dato, n_meses_completos, año_inicio, año_fin
