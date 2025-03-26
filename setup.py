from setuptools import setup, find_packages

setup(
    name='series',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy',
        'pandas',
        'geopandas',
        'shapely',
        'requests',
    ],
    author='Jesús Casado Rodríguez',
    author_email='chus.casado.88@gmail.com',
    description='Herramientas para descargar datos hidrometeorológicos',
    keywords='series-temporales hidrologia meteorologia datos aemet',
)