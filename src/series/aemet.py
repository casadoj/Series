from pathlib import Path
from datetime import date
import time
import unicodedata
from typing import Optional, Union, List, Literal, Dict

import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from tqdm.auto import tqdm
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - (%name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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


def elimiar_acentos(str):
    decomposed = unicodedata.normalize('NFKD', str)
    no_accents = ''.join(ch for ch in decomposed if not unicodedata.combining(ch))
    return no_accents


def aemet_estaciones(
        api_key: str,
        id: Optional[Union[str, List[str]]] = None,
        provincia: Optional[Union[str, List[str]]] = None,
        extension: Optional[List[float]] = None,
        proxy: Optional[Dict] = None
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
        proxies=proxy
    )

    if response.ok:
        # URL de descarga de los datos
        data_url = response.json()['datos']
        response_data = requests.get(
            data_url, 
            params={"api_key": api_key}, 
            verify=False,
            proxies=proxy
        )

        if response_data.ok:
            # recoger los datos en un DataFrame
            estaciones = pd.DataFrame(
                response_data.json()
                ).set_index('indicativo')

            # corregir attributos
            estaciones.altitud = estaciones.altitud.astype(int)
            estaciones.latitud = [round(
                dms2dd(lat[:2], lat[2:4], lat[4:6], lat[6]), 6) for lat in estaciones.latitud]
            estaciones.longitud = [round(
                dms2dd(lon[:2], lon[2:4], lon[4:6], lon[6]), 6) for lon in estaciones.longitud]

            # convertir a geoPandas
            estaciones = gpd.GeoDataFrame(
                estaciones,
                geometry=gpd.points_from_xy(estaciones.longitud, estaciones.latitud),
                crs='epsg:4326'
            )

            # aplicar filtros
            if id is not None:
                if isinstance(id, str):
                    id = [id]
                estaciones = estaciones.loc[id]

            if provincia is not None:
                if isinstance(provincia, str):
                    provincia = [provincia]
                provincia = [elimiar_acentos(x).lower() for x in provincia]
                estaciones = estaciones[estaciones.provincia.str.lower().isin(provincia)]

            if extension is not None:
                if len(extension) == 4:
                    bbox = gpd.GeoSeries([box(*extension)], crs='epsg:4326')
                    estaciones = estaciones[estaciones.geometry.within(
                        bbox.iloc[0])]
                else:
                    logging.warning(
                        'El filtro por extensión no pudo ser aplicado por ser incorrecto: [xmin, ymin, xmax, ymax]'
                        )

    if estaciones.empty:
        logging.warning(
            'No hay estaciones que cumplan los criterios de búsqueda')
        return None
    else:
        return estaciones.sort_index(axis=0)


def plot_estaciones(
    geometry,
    save: Union[str, Path] = None,
    **kwargs
):
    """Crea un mapa con las estaciones
    
    Parameters:
    -----------
    geometry: gpd.GeoSeries
        Geometría de las estaciones a representar
    save: str or pathlib.Path (optional)
        Si se proporciona, ruta donde guardar la figura

    Keyword Arguments:
    ------------------
    figsize: tuple (default: (20, 5))
        Tamaño de la figura
    title: str (default: None)
        Título del mapa
    alpha: float (default: 0.7)
        Transparencia de los puntos
    size: int (default: 12)
        Tamaño de los puntos
    color: str (default: 'steelblue')
        Color de los puntos
    """
    
    figsize = kwargs.get('figsize', (20, 5))
    title = kwargs.get('title', None)
    alpha = kwargs.get('alpha', .7)
    size = kwargs.get('size', 12)
    color = kwargs.get('color', 'steelblue')
    
    # configurar el mapa
    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(
        figsize=figsize, 
        subplot_kw={'projection': proj}
    )
    ax.add_feature(
        cfeature.NaturalEarthFeature('physical', 'land', '10m', edgecolor='face', facecolor='wheat'),#'lightgray'),
        alpha=.5,
        zorder=0
    )
    ax.add_feature(
        cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', '10m', edgecolor='lightslategrey', facecolor='none', linewidth=.5),
        alpha=0.7,
        zorder=1
    )
    if 'extent' in kwargs:
        ax.set_extent(kwargs['extent'], crs=proj)
    if title is not None:
        ax.text(.5, 1.125, title, horizontalalignment='center', verticalalignment='bottom', transform=ax.transAxes, fontsize=12)
    ax.axis('off')
    
    # representar las estaciones
    ax.scatter(
        geometry.x,
        geometry.y,
        s=size,
        c=color,
        alpha=alpha,
        zorder=2
    )  

    # guardar
    if save is not None:
        plt.savefig(save, dpi=300, bbox_inches='tight')


def aemet_diarios(
    api_key: str, 
    estacion: str, 
    inicio: date, 
    fin: date,
    proxy: Optional[Dict] = None,
) -> pd.DataFrame:
    """Extrae los datos diarios de la AEMET para una estación y un periodo.
    
    Args:
        api_key (str): llave personal de acceso al OpenData de la AEMET.
        estacion (str): identificador de la estación.
        inicio (date): fecha de inicio del periodo de interés.
        fin (date): fecha de fin del periodo de interés.

    Returns:
        pd.DataFrame: DataFrame con los datos diarios de la estación o None si no hay datos.
    """

    url_aemet = 'https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/'
    time_format = '%Y-%m-%dT%H:%M:%SUTC'

    # Generar periodos mensuales
    batch_dates = pd.date_range(inicio, fin, freq='MS', inclusive='both')
    if batch_dates[-1] != fin:
        batch_dates = batch_dates.append(pd.Index([fin]))

    serie_list = []
    batches = tqdm(
        zip(batch_dates[:-1], batch_dates[1:]), 
        desc='Procesando periodos', 
        total=len(batch_dates)-1
        )
    for i, (st, en) in enumerate(batches):
        if i > 0:
            st += pd.Timedelta(days=1)  # Evitar solapamiento de datos
        
        url = f'{url_aemet}' \
              f'fechaini/{st.strftime(time_format)}/' \
              f'fechafin/{en.strftime(time_format)}/' \
              f'estacion/{estacion}'

        # Implementar reintentos con backoff
        retries = 0
        while retries < 5:  
            response = requests.get(
                url, 
                params={'api_key': api_key}, 
                verify=False,
                proxies=proxy,
            )

            if response.status_code == requests.codes.too_many_requests:  # 429 Error
                wait_time = min(2 ** retries, 60)  # Exponential backoff
                time.sleep(wait_time)
                retries += 1
                continue
            
            if response.status_code != requests.codes.ok:
                logging.error(
                    f'Error {response.status_code}: {response.text}'
                    )
                break

            try:
                data_url = response.json().get('datos')
                if not data_url:
                    logging.warning(
                        f'No se encontró la clave "datos" en la respuesta: {response.json()}'
                        )
                    break
            except Exception as e:
                logging.error(
                    f'Error procesando la respuesta JSON: {e}'
                    )
                break

            # Obtener los datos
            response_data = requests.get(
                data_url, 
                params={'api_key': api_key}, 
                verify=False,
                proxies=proxy
            )

            if response_data.status_code != requests.codes.ok:
                logging.error(
                    f'Error al obtener datos: {response_data.status_code} - {response_data.text}'
                    )
                break

            try:
                df = pd.DataFrame(response_data.json())
                if not df.empty:
                    df.set_index('fecha', inplace=True)
                    df.index = pd.to_datetime(df.index, errors='coerce')
                    serie_list.append(df)
            except Exception as e:
                logging.error(
                    f'Error procesando los datos JSON: {e}'
                    )
            
            break  # Salir del bucle de reintentos si todo fue bien

        time.sleep(60/45)  # Evitar superar el límite de peticiones

    if serie_list:
        # Concatenar y convertir datos
        serie = pd.concat(serie_list).sort_index()

        # Convertir tipos de datos de manera eficiente
        conversion_map = {
            'altitud': 'Int64',  # Pandas nullable integer type
            'tmed': 'float',
            'prec': 'float',
            'tmin': 'float',
            'tmax': 'float',
            'velmedia': 'float',
            'racha': 'float',
            'presMax': 'float',
            'presMin': 'float'
        }

        for col, dtype in conversion_map.items():
            if col in serie.columns:
                serie[col] = pd.to_numeric(serie[col].astype(str).str.replace(',', '.'), errors='coerce').astype(dtype)

        return serie

    logging.WARNING(
        f'No hay datos para la estación {estacion} en el periodo {inicio} - {fin}'
        )
    return None