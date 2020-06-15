# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from sklearn.linear_model import LinearRegression
import plotly.express as px
import math

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


df = pd.read_csv('include/Diagnostics_Runoff_Basin_Scale_km3peryr.csv')

x = df['xanthos'].values.reshape(-1,1)
y = df['VIC_1971-2000'].values.reshape(-1,1)
model = LinearRegression().fit(x, y)
r_sq = model.score(x, y)

fig = px.scatter(df, x="xanthos", y="VIC_1971-2000", trendline="ols")
fig.update_layout(
    title={'text': "Xanthos to VIC Runoff: R=" + str(round(math.sqrt(r_sq), 6)),'y':0.9, 'x':0.5,'xanchor': 'center', 'yanchor': 'top'},
    xaxis_title="Xanthos Runoff (km\N{SUPERSCRIPT THREE}/yr)",
    yaxis_title="VIC Runoff (km\N{SUPERSCRIPT THREE}/yr)"
    # font=dict(
    #     family="Courier New, monospace",
    #     size=18,
    #     color="#7f7f7f"
   # )
)

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
