import pandas as pd
import geopandas as gpd
import requests
import logging
from typing import Optional, Union, List, Literal, Dict
from shapely.geometry import box


def dms2dd(
        degrees: int,
        minutes: int, 
        seconds:int, 
        direction: Literal['N', 'S', 'E', 'W']
        ) -> float:
    """Convierte un valor de latitud o longitud desagregado en grados, minutos y segundos en su valor decimal.
    """
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction in ['W', 'S']:
        dd *= -1
    return dd


def aemet_estaciones(
        api_key: str,
        id: Optional[Union[str, List[str]]] = None,
        provincia: Optional[Union[str, List[str]]] = None,
        extension: Optional[List[float]] = None,
        proxies: Optional[Dict] = None
) -> gpd.GeoDataFrame:
    """Extrae las estaciones disponibles en la API de AEMET y las devuelve en un GeoDataFrame

    Args:
        api_key: string
            API key de AEMET
        id: string o lista de strings (opcional)
            Código de la estación o lista de códigos. Por defecto None y no se aplica este filtro.
        provincia: string o lista de strings (opcional)
            Nombre de la provincia o lista de nombres. Por defecto None y no se aplica este filtro.
        extension: lista de floats (opcional)
            Extensión geográfica de la que extraer las estaciones. Debe tener el formato [xmin, ymin, xmax, ymax]. Por defecto None y no se aplica este filtro.

    Returns:
        geopandas.GeoDataFrame: tabla con las estaciones que cumplen los criterios de búsqueda y sus metadatos (nombre, provincia, altitud, latitud y longitud)
    """

    URL = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"

    # petición a la API de todas las estaciones disponibles
    response = requests.get(
        URL, 
        params={"api_key": api_key}, 
        verify=False,
        proxies=proxies
    )

    if response.ok:
        # URL de descarga de los datos
        data_url = response.json()['datos']
        response_data = requests.get(
            data_url, 
            params={"api_key": api_key}, 
            verify=False,
            proxies=proxies
        )

        if response_data.ok:
            # recoger los datos en un DataFrame
            estaciones = pd.DataFrame(
                response_data.json()).set_index('indicativo')

            # corregir attributos
            estaciones.altitud = estaciones.altitud.astype(int)
            estaciones.latitud = [round(
                dms2dd(lat[:2], lat[2:4], lat[4:6], lat[6]), 6) for lat in estaciones.latitud]
            estaciones.longitud = [round(
                dms2dd(lon[:2], lon[2:4], lon[4:6], lon[6]), 6) for lon in estaciones.longitud]

            # convertir a geoPandas
            estaciones = gpd.GeoDataFrame(estaciones, geometry=gpd.points_from_xy(
                estaciones.longitud, estaciones.latitud), crs='epsg:4326')

            # aplicar filtros
            if id:
                if isinstance(id, str):
                    id = [id]
                estaciones = estaciones.loc[id]

            if provincia:
                if isinstance(provincia, str):
                    provincia = [provincia]
                provincia = [x.lower() for x in provincia]
                estaciones = estaciones[estaciones.provincia.str.lower().isin(
                    provincia)]

            if extension:
                if len(extension) == 4:
                    bbox = gpd.GeoSeries([box(*extension)], crs='epsg:4326')
                    estaciones = estaciones[estaciones.geometry.within(
                        bbox.iloc[0])]
                else:
                    logging.warning(
                        'El filtro por extensión no pudo ser aplicado por ser incorrecto: [xmin, ymin, xmax, ymax]')

    if estaciones.empty:
        logging.warning(
            'No hay estaciones que cumplan los criterios de búsqueda')
        return None
    else:
        return estaciones
