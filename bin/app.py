import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
import itertools as it
import pandas as pd
import TradeUtils as tu
import GlobalVars as gv
import datetime as dt
  
#X=[]
#Y=[]
#Y=[[] for i in range(4)]
index = it.count()
FN = gv.RptDir+gv.RepFiles['LiveGraph']+dt.datetime.now().strftime('%m%d')+'.csv'
LGData=pd.read_csv(FN, index_col=0)
LGData=LGData[['Stock','Close','MCap','Lot']]; LGData['LTP']=0
SData=pd.DataFrame(columns=LGData['Stock'])
SData.loc[len(SData.index)] = [1, 1.5, 0.7]
print(SData)
app = dash.Dash(__name__)
app.layout = html.Div(
    [dcc.Graph(id = 'live-graph', animate = True),
     dcc.Interval(id = 'graph-update',interval = 5000, n_intervals = 0),])
@app.callback(
    Output('live-graph', 'figure'),[Input('graph-update', 'n_intervals')])
  
def update_graph_scatter(n):
    global LGData, SData
#    print(LGData)
#    LGData=tu.AddLTPToDays(LGData)
    SData.loc[len(SData.index)] = [1, 1.5, 0.7]
#    print(LGData)
    print(SData)
#    print(LGData)
#    for i in range(len(LGData)):
#       Y[i].append(LGData.iloc[i]['DayP'])

#    X.append(X[-1]+1)
#    X.append(next(index))
#    Data=pd.DataFrame({'Stock' : ['NMDC.NS'], 'Close': [173] })
#    Data=tu.AddLTPToDays(Data)
#    print(Data)
#    NewY=Data['DayP'].values[0]+Data['DayP'].values[0]* random.uniform(-0.1,0.1)
#    NewY=Y[-1]+Y[-1] * random.uniform(-0.1,0.1)
#    print(NewY)
#    Y.append(NewY)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=SData['Stock'], y=SData['AUBANK.NS'], name='High'))
    fig.add_trace(go.Scatter(x=SData['Stock'], y=SData['GODREJCP.NS'], name ='Low'))
 
#   data = go.Scatter(x=SData['Stock'],y=SData['AUBANK.NS'],name='Scatter',mode= 'lines+markers')
    return {'data': [fig],
#           'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),yaxis = dict(range = [min(Y),max(Y)]),)}
             'layout' : go.Layout()}

if __name__ == '__main__':
    app.run_server()
#    app.run_server(debug=True, use_reloader=False)