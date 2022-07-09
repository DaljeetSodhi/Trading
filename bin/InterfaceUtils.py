import pandas as pd
import os
import datetime as dt
import GlobalVars as gv
import OtherUtils as ou
import StockUtils as su
import TradeUtils as tu
import GraphUtils as gu

from IPython.display import clear_output

import ipywidgets as widgets
from IPython.display import display

DaysData=IDayData=pd.DataFrame()
LGStock1=LGStock2=LGStock3=LGStock4=LGStock5=''
FnOList = pd.DataFrame()
def StockMenu():
    sub_tab=[widgets.Output() for i in range(5)]
    tab = widgets.Tab(sub_tab)
    tab.set_title(0,"Day"); tab.set_title(1,"LiveGraphs")
    tab.set_title(2,"IntraDay")
    tab.set_title(3,"Graphs"); tab.set_title(4,"Process")
    with sub_tab[0]: DayTab()
    with sub_tab[1]: LiveGraphTab()
    with sub_tab[2]: IDayTab()
    with sub_tab[3]: GraphTab()
    with sub_tab[4]: StrategyTab()
    
    display(tab)       
    return()
    
def DayTab():
    DayP = widgets.Button(description='Process Data');DayP.on_click(DayPClicked) 
    DayS = widgets.Button(description='Stocks to Short');DayS.on_click(DaySClicked) 
    DayL = widgets.Button(description='Stocks to Long');DayL.on_click(DayLClicked) 
    DayA = widgets.Button(description='Add LTP');DayA.on_click(DayAClicked)     
    DayC = widgets.Button(description='Clear');DayC.on_click(DayCClicked)   
    
    DayS.style.button_color = DayL.style.button_color = 'lightgreen'
    DayP.style.button_color = DayA.style.button_color = 'yellow'
    box = widgets.HBox([DayP, DayS, DayL, DayA, DayC]);display(box)
def LiveGraphTab():    
    FN = gv.RptDir+gv.RepFiles['MCap'];
    FnOList=pd.read_csv(FN, index_col=0)
    Stocks = ['']+FnOList['Stock'].tolist()
    
    LGraphSl = widgets.Dropdown(options=Stocks,);LGraphSl.observe(LGraphSlChange)
    LGraphS2 = widgets.Dropdown(options=Stocks,);LGraphS2.observe(LGraphS2Change)
    LGraphS3 = widgets.Dropdown(options=Stocks,);LGraphS3.observe(LGraphS3Change)
    LGraphS4 = widgets.Dropdown(options=Stocks,);LGraphS4.observe(LGraphS4Change)
    LGraphS5 = widgets.Dropdown(options=Stocks,);LGraphS5.observe(LGraphS5Change)
    
    LGraphD = widgets.Button(description='Draw');LGraphD.on_click(LGraphDClicked)      
    box = widgets.HBox([LGraphSl, LGraphS2,LGraphS3,LGraphS4,LGraphS5, LGraphD])
    display(box)
def LGraphSlChange(change):
    global LGStock1
    if change['type'] == 'change' and change['name'] == 'value':
        LGStock1=change['new']
def LGraphS2Change(change):
    global LGStock2
    if change['type'] == 'change' and change['name'] == 'value':
        LGStock2=change['new']
def LGraphS3Change(change):
    global LGStock3
    if change['type'] == 'change' and change['name'] == 'value':
        LGStock3=change['new']
def LGraphS4Change(change):
    global LGStock4
    if change['type'] == 'change' and change['name'] == 'value':
        LGStock4=change['new']
def LGraphS5Change(change):
    global LGStock5
    if change['type'] == 'change' and change['name'] == 'value':
        LGStock5=change['new']

def LGraphDClicked(_):
    global LGStock1,LGStock2,LGStock3,LGStock4,LGStock5
    FN = gv.RptDir+gv.RepFiles['DailyFnO']+dt.datetime.now().strftime('%m%d')+'.csv'
    FnOList=pd.read_csv(FN, index_col=0)
    SL=[LGStock1,LGStock2,LGStock3,LGStock4,LGStock5]
    SL=[x for x in SL if '' != x]
    ToDraw = pd.DataFrame(SL,columns=['Stock'])
    ToDraw = pd.merge(ToDraw, FnOList, on=['Stock'], how='left') 
    print(ToDraw[['Stock', 'MCap','Lot','Close', 'RSI']])
    FN = gv.RptDir+gv.RepFiles['LiveGraph']+dt.datetime.now().strftime('%m%d')+'.csv'
    ToDraw.to_csv(FN) 

def DayPClicked(_):
    global DaysData
    FnO=ou.GetFnOList(); DaysData=tu.AddDaysInfo(FnO)
def DaySClicked(_):
    global DaysData; tu.DisplayData(DaysData, 'Day', 'Short', 6)
def DayLClicked(_):
    global DaysData
    global DaysData; tu.DisplayData(DaysData, 'Day', 'Long', 6)
def DayAClicked(_):
    global DaysData
    clear_output(); DayTab()
    DaysData=tu.AddLTPToDays(DaysData)
    return()
def DayCClicked(_):
    clear_output(); DayTab()
    
def IDayTab():
    IDayP = widgets.Button(description='Process Data');IDayP.on_click(IDayPClicked) 
    IDayS = widgets.Button(description='Stocks to Short');IDayS.on_click(IDaySClicked) 
    IDayL = widgets.Button(description='Stocks to Long');IDayL.on_click(IDayLClicked)   
    IDayC = widgets.Button(description='Clear');IDayC.on_click(IDayCClicked)      

    IDayS.style.button_color = IDayL.style.button_color = 'lightgreen'
    IDayP.style.button_color = 'yellow'

    box = widgets.HBox([IDayP, IDayS, IDayL, IDayC]);display(box)
def IDayPClicked(_):
    global DaysData, IDayData
    TotRecs=DaysData.copy(); IDayData=tu.AddIntraDay(TotRecs, '15m')
def IDaySClicked(_):
    global IDayData; tu.DisplayData(IDayData, 'Intra', 'Short', 3)
def IDayLClicked(_):
    global IDayData; tu.DisplayData(IDayData, 'Intra', 'Long', 3)
def IDayCClicked(_):
    clear_output(); IDayTab()

def GraphTab():    
    Stocks = [f for f in os.listdir(gv.HistDir) if f.endswith('.NS.csv')]
    Stocks = [x[:-4] for x in Stocks]
    GraphSl = widgets.Dropdown(options=Stocks,description='Graph For :',)
    GraphSl.observe(GraphSlChange);
    GraphC = widgets.Button(description='Clear');GraphC.on_click(GraphCClicked)      
    box = widgets.HBox([GraphSl, GraphC]);display(box)

def GraphSlChange(change):
    if change['type'] == 'change' and change['name'] == 'value':
        Stock=change['new']; StockData=pd.read_csv(gv.HistDir+Stock+'.csv', index_col=0)
        gu.DrawGraphs(Stock, StockData)
def GraphCClicked(_):
    clear_output(); GraphTab()
    
def StrategyTab():
    StratP = widgets.Button(description='Process'); StratP.on_click(StratPClicked)     
    StratD = widgets.Button(description='Display');StratD.on_click(StratDClicked) 
    StratC = widgets.Button(description='Clear');StratC.on_click(StratCClicked) 
    
    StratD.style.button_color = 'lightgreen'
    StratP.style.button_color = 'yellow'   
    box = widgets.HBox([StratP, StratD, StratC]);display(box)
    
def StratPClicked(_):
    FnO=ou.GetFnOList()
    MCap=tu.GetMCap(FnO)
    su.ProcessStrategy()
def StratDClicked(_):
    Result=tu.GetListToTrade()
    TotRecs=Result.copy()
    tu.AddLatestToList(TotRecs,Action=0,RSIInterval='15m')   
def StratCClicked(_):
    clear_output(); StrategyTab()
    