# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


df = pd.read_csv('include/Diagnostics_Runoff_Basin_Scale_km3peryr.csv')

X = df['xanthos'].values.reshape(-1,1)
y = df['VIC_1971-2000'].values.reshape(-1,1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
regressor = LinearRegression()
regressor.fit(X_train, y_train) #training the algorithm

#To retrieve the intercept:
print(regressor.intercept_)
#For retrieving the slope:
print(regressor.coef_)

y_pred = regressor.predict(X_test)

df.plot(x='xanthos', y='VIC_1971-2000', style='o')
plt.scatter(X_test, y_test,  color='gray')
plt.plot(X_test, y_pred, color='red', linewidth=2)
plt.show()


i: object
app.layout = html.Div([
    dcc.Graph(
        id='x-vs-v',
        figure=dict(data=[
            dict(
                x=df[df['Name'] == i]['xanthos'],
                y=df[df['Name'] == i]['VIC_1971-2000'],
                text=df[df['Name'] == i]['Name'],
                mode='markers',
                opacity=0.7,
                marker={
                    'size': 15,
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=i
            ) for i in df.Name.unique()
        ], layout=dict(
            xaxis={'title': 'Xanthos'},
            yaxis={'title': 'VIC'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        ))
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

# def dump_this():
#     return 0
