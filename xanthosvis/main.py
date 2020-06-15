# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import plotly.express as px
import plotly.graph_objects as go


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


df = pd.read_csv('include/Diagnostics_Runoff_Basin_Scale_km3peryr.csv')

fig = px.scatter(df, x="xanthos", y="VIC_1971-2000",  trendline="ols")

app.layout = html.Div([
    dcc.Graph(
        id='life-exp-vs-gdp',
        figure=fig
    )
])
if __name__ == '__main__':
    app.run_server(debug=True)

# def dump_this():
#     return 0
