#!/usr/bin/env python
# coding: utf-8

# In[1]:


import time
import datetime
import json
import requests
import math
import numpy as np

import bitmex

import pandas as pd

#Authentication Real Bitmex
key = 'fRKvAJ8h2ydusdLWTqPb_Mxx'
secret = 'nT6WSZuPsNd5q3-DECkHABM5eatoGbQc61mpxnHyUM7yX-dg'

client = bitmex.bitmex(test=False,api_key=key,api_secret=secret)

def run(client, qty_s, qty_l, d_short, d_long):
    while True:
        #ดึงข้อมูล
        #Open Orders
        data_op = client.Order.Order_getOrders(symbol='XBTUSD', reverse=False, filter=json.dumps({"open": True})).result()
        #Last price
        response = requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json() 
        #Trade History
        #Last Buy
        last_buy = client.Execution.Execution_getTradeHistory(symbol = 'XBTUSD', reverse = True, filter=json.dumps({'side': 'Buy'}), count = 1).result()
        #Last Sell
        last_sell = client.Execution.Execution_getTradeHistory(symbol = 'XBTUSD', reverse = True, filter=json.dumps({'side': 'Sell'}), count = 1).result()


        #เอาข้อมูล price, quantity และ direction ใส่ตาราง
        qty = []
        for a in range(len(data_op[0])):
            qty.append(data_op[0][a-1]['orderQty'])

        side = []
        for b in range(len(data_op[0])):
            side.append(data_op[0][b-1]['side'])

        price = []
        for c in range(len(data_op[0])):
            price.append(data_op[0][c-1]['price'])

        orderid = []
        for d in range(len(data_op[0])):
            orderid.append(data_op[0][d-1]['orderID'])

        my_dict = {'Price':price,'Oty':qty,'Direction':side, 'OrderID':orderid}
        df_dict = pd.DataFrame(my_dict)

        #กำหนดค่า Buy = 1 และ Sell = -1
        df_dict['LS'] = np.nan
        df_dict.loc[df_dict.Direction == 'Buy','LS'] = 1
        df_dict.loc[df_dict.Direction == 'Sell','LS'] = -1
        df_dict = df_dict.fillna(method='ffill')

        #Define Parameters
        symbol = 'XBTUSD'

        xbt_ask_price = response[0]['price']
        xbt_bid_price = response[1]['price']

        qty_s = -1
        qty_l = 1

        last_trade_buy = last_buy[0][0]['price']
        last_trade_sell = last_sell[0][0]['price']

        d_short = 25
        d_long = 25

        ls = int(sum(df_dict['LS']))

        count = df_dict['LS'].count()

        text_01 = 'Scenario 01'
        text_02 = 'Scenario 02'
        text_03 = 'Scenario 03'
        text_04 = 'Scenario 04'
        text_05 = 'Scenario 05'
        text_06 = 'Scenario 06'

        #Strategy
        if count <= 2 : #check ว่า order ไม่เกิน 2
            if count !=2 : #จำนวน order ที่เปิดเท่ากับ 2 หรือไม่
                if count == 0 : #มี order เปิดอยู่หรือไม่
                    #ยิง short order ที่ market price
                    client.Order.Order_new(symbol = symbol, 
                                           orderQty = qty_s, 
                                           text = text_01).result()
                    #ตั้ง TP
                    client.Order.Order_new(symbol = symbol, 
                                           orderQty = qty_l, 
                                           price = xbt_bid_price - d_long, 
                                           text = text_01).result()
                    #ตั้ง Pending short ถัดไป
                    client.Order.Order_new(symbol = symbol, 
                                           orderQty = qty_s, 
                                           price = xbt_ask_price + d_short, 
                                           text = text_01).result()
                    print("Scenario 01")
                else : #มีอยู่ 1 order
                    if ls == 1 : #เปิด long order อยู่
                        if xbt_ask_price - last_trade_sell < d_short : #price ไม่ข้าม zone (จุดที่จะ short ถัดไป)
                            #ตั้ง Pending short ถัดไป
                            client.Order.Order_new(symbol = symbol,
                                                   orderQty = qty_s,
                                                   price = last_trade_sell + d_short,
                                                   text = text_03).result()
                            #เลื่อน tp
                            orderid = data_op[0][0]['orderID']
                            client.Order.Order_amend(orderID=orderid,
                                                     price=last_trade_sell - d_long, 
                                                     text = text_03).result()
                            print('Scenario_03')
                        else : #price ข้าม zone (จุดที่จะ short ถัดไป)
                            #ยิง short order ที่ market price
                            client.Order.Order_new(symbol = symbol,
                                                   orderQty = qty_s,
                                                   text = text_04).result()
                            #ตั้ง Pending short ถัดไป
                            client.Order.Order_new(symbol = symbol,
                                                   orderQty = qty_s,
                                                   price = xbt_ask_price + d_short,
                                                   text = text_04).result()
                            #เลื่อน tp
                            orderid = data_op[0][0]['orderID']
                            client.Order.Order_amend(orderID=orderid,
                                                     price=xbt_bid_price - d_long, 
                                                     text = text_04).result()
                            print('Scenario_04')
                    else : #ls == -1; เปิด short order อยู่ 
                        if last_trade_buy - xbt_bid_price < d_long : #price ไม่ข้าม zone (จุดที่จะ long ถัดไป)                    
                            #ตั้ง Pending long ถัดไป
                            client.Order.Order_new(symbol = symbol,
                                                   orderQty = qty_l,
                                                   price = last_trade_buy - d_long,
                                                   text = text_05).result()
                            #เลื่อน tp
                            orderid = data_op[0][0]['orderID']
                            client.Order.Order_amend(orderID=orderid,
                                                     price=last_trade_buy + d_long, 
                                                     text = text_05).result()
                            print('Scenario_05')
                        else : #price ข้าม zone (จุดที่จะ long ถัดไป)
                            #ยิง long order ที่ market price
                            client.Order.Order_new(symbol = symbol,
                                                   orderQty = qty_l,
                                                   text = text_06).result()
                            #ตั้ง pending long ถัดไป
                            client.Order.Order_new(symbol = symbol,
                                                   orderQty = qty_l,
                                                   price = xbt_bid_price - d_long,
                                                   text = text_06).result()
                            #เลื่อน pending short
                            orderid = data_op[0][0]['orderID']
                            client.Order.Order_amend(orderID=orderid,
                                                     price=xbt_ask_price + d_short,
                                                     text = text_06).result()
                            print('Scenario_06')
            else : #มี order เปิดอยู่ 2 order
                if ls != 0 : #มี buy และ sell เท่ากันหรือไม่
                    print("Error : Quantity")
        else :
            print("Error : Order > 2")
        time.sleep(10)


# In[ ]:


run(client,qty_s = -1,qty_l= 1,d_short= 25,d_long=25)

