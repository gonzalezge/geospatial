
# !pip3 install dash
# !pip3 install dash_core_components
# !pip3 install dash_html_components
# !pip3 install dash-bootstrap-components
 # !pip3 install shapely
# !pip3 install pyproj
# !pip3 install folium
# !pip3 install pandas
# !pip3 install requests
# !pip3 install geopy
# !pip3 install geojson
# !pip3 install xlrd
# !pip3 install visdcc
# !pip3 install sklearn
# !pip3 install waitress
import pyproj
from functools import partial
import shapely.geometry
from shapely.ops import transform
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point, MultiPoint
from geopy.distance import great_circle
import folium
import geojson
import json
import pandas as pd
import re
import geopy
import requests
import time
import numpy as np
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN

###### ------ Dash ------ ####
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

import visdcc
from waitress import serve




Lugares_usaquen_sample = pd.read_pickle('Lugares_sample.gzip',compression='gzip')


def Hacer_clusters(Metros):
    ####### ------ Transform coords ------- #########
    coords_to_clusterize = np.array(list(pd.DataFrame(Lugares_usaquen_sample.apply(lambda x: [float(x['Latitude']),float(x['Longitude'])],axis=1))[0]))
    coords_radians = np.radians(coords_to_clusterize)

    # Distancia máxima (1.5 kilómetros en este ejemplo) que los
    # puntos pueden estar el uno del otro para ser considerados un grupo
    Kilometros_cluster = Metros/1000

    #### ----- Radio del mundo ------ ######
    Kilometros_radio_mundo = 6371.0088
    ####### ------- Se calcula el epsilon en radiales ------- ########
    epsilon = Kilometros_cluster/Kilometros_radio_mundo

    ########## ---------- Calcular clusters  --------- ##########
    Clusters =DBSCAN(eps=epsilon,algorithm='ball_tree',metric='haversine',n_jobs=-1).fit(coords_radians)
    #### ------ Se extraen las etiquetas de cada lot, lat ----- ####
    Etiquetas_clusters = Clusters.labels_
    #### ------ Asignar la etiqueta a cada observación ----- ######
    Lugares_usaquen_sample['Grupo'] = Etiquetas_clusters

    ##### -------- Contar el número de observaciones por cluster ------ #####
    Indice_clusters = pd.DataFrame(pd.value_counts(pd.DataFrame(Etiquetas_clusters)[0]).sort_index())[0]


    ### ------- Numero de grupos creados ---- #####
    num_clusters = len(set(Etiquetas_clusters))





    ##### -------- Crear lista con las coordenadas ----- ######
    clusters = pd.Series([coords_to_clusterize[Etiquetas_clusters == n] for n in list(set(Etiquetas_clusters))])

    ####### ------ función para encontrar las coordenadas de los centroides ------- ######
    def Obtener_centro_clusters(cluster):
        ### ------- Encontrar el centroide de la figura ------ #######
        Centroide = MultiPoint(cluster).centroid.coords[0]
        ###### -------- Calcular distancia a un punto real -------- ######
        ##### ----------- Encontrar distancia minima ----- #######
        centermost_point = min(cluster , key=lambda x: great_circle(x , Centroide).m)
        return tuple(centermost_point)



    ###### ------- Calculate centroid ------- #######
    Coordenadas_centroides = list( map(lambda x: Obtener_centro_clusters(x),clusters))
    ### ----- Extraer las latitude y longitudes
    Latitudes = list(map(lambda x: x[0],Coordenadas_centroides))
    Longitudes = list(map(lambda x: x[1],Coordenadas_centroides))
    ### --------- Consolidar dataframe ---- ###
    Centroides_info = pd.DataFrame({'Longitude':Longitudes, 'Latitude':Latitudes})
    ### ------- Buscar información del centroide ------- ####
    Centroides = Centroides_info.apply(lambda row: Lugares_usaquen_sample[(Lugares_usaquen_sample['Latitude']==row['Latitude']) & (Lugares_usaquen_sample['Longitude']==row['Longitude'])].iloc[0], axis=1)
    Centroides = pd.DataFrame(Centroides)





    mapa = folium.Map(location=[Centroides.head(1)['Latitude'].iloc[0],Centroides.head(1)['Longitude'].iloc[0]],zoom_start=13,tiles='cartodbpositron')

    Vector_colores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred','lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']

    ##### ------- Graficar Centroides ------ ######
    for j in range(0,len(Centroides)):
        punto = Centroides.iloc[j]
        folium.Marker(
            [punto['Latitude'],punto['Longitude']],icon=folium.Icon(color=Vector_colores[j], icon='cloud'),tooltip=punto['Nombre']
        ).add_to(mapa)


        ##### ------- Graficar vecinos de los centroides ------ ######
        Vecinos_cluster = Lugares_usaquen_sample[Lugares_usaquen_sample['Grupo'] == punto['Grupo']]

        ##### ------- Excluir al centro ------ ####
        Vecinos_cluster = Vecinos_cluster[Vecinos_cluster['ID'] != punto['ID']]
        for v in range(0,len(Vecinos_cluster)):
            punto_vecino = Vecinos_cluster.iloc[v]
            folium.Marker(
                [punto_vecino['Latitude'],punto_vecino['Longitude']],icon=folium.Icon(color=Vector_colores[j], icon='book'),tooltip=punto_vecino['Nombre']
            ).add_to(mapa)

    return(mapa.get_root().render())





app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

### --- Principal Title --- ###
app.title = 'Universidad de los Andes'
### ---------------- Logo - Image ------------------ ###

Arriba = dbc.NavbarSimple(children=[
html.Img(src='https://www.sketchdrive.com/wp-content/uploads/2019/04/uniandes-logo-about.png',width=200,height=60)],
    brand="Clase 8",
    brand_href="#",
    color="black",
    dark=True,
)



Estilo_arriba_caja = {'textAlign': 'center','height': 30, 'display': 'block', 'margin-left': 'auto','margin-right': 'auto','width': '100%', 'color': '#ffffff',"background-color": '#292929'}
Estilo_caja = {"max-width": "2000px", 'height': 'calc(100vh - 60px)', 'overflowY': 'scroll',"opacity": 0.9, "background-color": "#f5f5f5",'textAlign': 'center'}

Cuerpo = html.Div([dbc.Toast([html.Div([html.P('Bienvenidos a este Dash'),html.Br(),
    dcc.Slider(
    id='Valor_metros',min=100,
    max=1000,
    value=550,
    marks={
        100: {'label': '100 mts', 'style': {'color': '#b93321'}},
        300: {'label': '300 mts', 'style': {'color': '#e05b49'}},
        550: {'label': '550 mts', 'style': {'color': '#f8bf00'}},
        800: {'label': '800 mts', 'style': {'color': '#2c9a42'}},
        1000: {'label': '1000 mts', 'style': {'color': '#0d7722'}}
    },
    included=False),html.Div(id='Resultados_mapa'),visdcc.Run_js(id = 'Correr_java')])],
                    header= 'Análisis de Clusters',header_style = Estilo_arriba_caja,
                   style=Estilo_caja)],style={
            'marginTop': 30,
            'marginBottom': 20,
            'marginLeft': 250,
            'marginRight': 250,
            'padding': 0,'background': "#f5f5f5","opacity": 1,})



######### ---------------- Esto es un callback -------- #######
@app.callback(
    [Output('Resultados_mapa', 'children'),
     Output('Correr_java', 'run')],
    [Input('Valor_metros', 'value')])
def Decision_analisis(Valor_metros):
    java = ''' alert("''' + 'Usted ha seleccionado '+ str(Valor_metros) + ' metros.' +'''"); '''
    mapa = html.Section(
        children=[html.Iframe(id='Mapa_general',srcDoc =  Hacer_clusters(Metros=Valor_metros),height = 850,
            style={'display': 'flex','width': '100%','border': 0,
               'top': 0,
               'left' : 0,
               'bottom': 0,
               'right': 0} )],
        style={
            'padding': 0,
            'margin': 0,'height': 'calc(80vh - 60px)', 'overflowY': 'scroll',
            'borderRadius': 0,
            'border': 'thin lightgrey ridge', 'border-color': '#c7bfbf', 'border-width': '0px','background': '#f5f5f5',"opacity": 0.9
        })

    return(mapa,java)



########## ------------- Abajo ------------- #############
Abajo = html.Div([html.H5(
        children='Todos los derechos - Copyright ©  2020.',
        style={'textAlign': 'center','color': 'black'})])


app.layout = html.Div(children=[Arriba,Cuerpo,Abajo])



############# --------------- Server ----------- #############
serve(app.server,host='127.0.0.1',port=9999) #this connects with the server

######## ------- Desplegar servidor -------- ########
server = create_server(app,threaded=True)
server.run()
