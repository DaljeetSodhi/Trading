# -*- coding: utf-8 -*-
"""
Created on Sat Jun 12 14:44:23 2021

@author: dsodh
"""

import time
import itertools as it
import GlobalVars as gv
import TradeUtils as tu
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#FN = gv.RptDir+gv.RepFiles['LiveGraph']+dt.datetime.now().strftime('%m%d')+'.csv'
#LGData=pd.read_csv(FN, index_col=0)
#LGData=LGData[['Stock','Close']]
#LGData=tu.AddLTPToDays(LGData)
#print(LGData)

plt.style.use('fivethirtyeight')

FN = gv.RptDir+gv.RepFiles['LiveGraph']+dt.datetime.now().strftime('%m%d')+'.csv'
LGData=pd.read_csv(FN, index_col=0)
 
x = []
y=[[] for i in range(len(LGData))]

index = it.count()
def lineGrapgh(LGData):
    Color=['green','blue','yellow','red','grey']
    x.append(next(index))
    for i in range(len(LGData)):
        y[i].append(LGData.iloc[i]['DayP'])
    plt.cla()
    for i in range(len(LGData)):
        SText=LGData.iloc[i]['Stock'][:-3]
        SLabel=str(i+1)+':'+SText+':'+str(int(LGData.iloc[i]['Lot']))+':'+str(LGData.iloc[i]['DayOP'])
        plt.plot(x, y[i], label=SLabel,color=Color[i]); plt.legend()
        plt.text(x[-1]-1, y[i][-1],SText)
        plt.axhline(y=LGData.iloc[i]['DayOP'], color=Color[i], linestyle='--')
def animate(i):
    STime=time.time()
    FN = gv.RptDir+gv.RepFiles['LiveGraph']+dt.datetime.now().strftime('%m%d')+'.csv'
    LGData=pd.read_csv(FN, index_col=0)
    LGData=LGData[['Stock','Close','MCap','Lot']]
    LGData=tu.AddLTPToDays(LGData)
    lineGrapgh(LGData)
    Sleep=20-(time.time()-STime)
    if(Sleep<0): Sleep = 0 
    print('zzz...', Sleep); time.sleep(Sleep)
    
ani = FuncAnimation(plt.gcf(), animate, 15000)
plt.tight_layout()
plt.show()