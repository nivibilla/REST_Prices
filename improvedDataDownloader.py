# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import requests
import json
import pandas as pd
from tqdm import tqdm
import numpy as np
import datetime
import os
from pathlib import Path

Path("./Data/processed/").mkdir(parents=True, exist_ok=True)


# %%
resolution = 'DAY'

ApiKeys = []
e = open("APIKEYS.txt", "r")
for y in e:
    ApiKeys.append(y.strip())
e.close()

epicList = []
e = open("epics.txt", "r")
for y in e:
    epicList.append(y.strip())
e.close()


username = 'eastwind'
password = 'Eastwind1!'

initialStart = '2015-01-01'
initialEnd = '2021-01-01'


# %%
def createLog():
    print("Creating Log")
    log = []
    for epic in epicList:
        log.append([epic, 'none', 'none'])
    log = pd.DataFrame(log, columns=['name', 'from', 'to'])
    log.to_csv('./log.txt', index=None)

def readLog():
    try:
        log = pd.read_csv('./log.txt', index_col=0)
    except FileNotFoundError:
        createLog()
        return readLog()
    return log

def writeLog(log):
    log.to_csv('./log.txt')


# %%
def login(api):
    try:
        url = 'https://demo-api.ig.com/gateway/deal/session'

        s = requests.Session()
        s.headers = {'Content-Type': 'application/json; charset=UTF-8',
                        'Accept': 'application/json; charset=UTF-8', 'VERSION': '2', 'X-IG-API-KEY': api}
        data = {'identifier': username, 'password': password}
        r = s.post(url, json=data)
        s.headers.update({'X-SECURITY-TOKEN': r.headers['X-SECURITY-TOKEN'], 'CST': r.headers['CST']})
        s.headers.update({'Version': '3'})
    except:
        print(r)
        print(s)
        return
    return s


# %%
def getDF(EPIC, start, end, s):
    try:
        nameURL = 'https://demo-api.ig.com/gateway/deal/markets/' + EPIC

        address = ["https://demo-api.ig.com/gateway/deal/prices/", EPIC, "?resolution=", resolution,
                    "&from=", str(start), "&to=", str(end), "&pageSize=0"]
        URL = ''.join(address)

        prices = s.get(URL)
        prices = prices.text


        nameData = s.get(nameURL)
        nameData = nameData.text

        nameData = json.loads(nameData)
        priceData = json.loads(prices)

        name = nameData['instrument']['marketId']

        if name == None:
            return "failed"

        for price in priceData['prices']:
            price['openPrice'] = price['openPrice']['ask']
            price['closePrice'] = price['closePrice']['ask']
            price['highPrice'] = price['highPrice']['ask']
            price['lowPrice'] = price['lowPrice']['ask']

        df = pd.DataFrame(priceData['prices'])
        df.columns = ['time', 'utcTime', 'open', 'close', 'high', 'low', 'volume']
        df.drop(['utcTime'], axis=1, inplace=True)
        df['time'] = pd.to_datetime(df['time'])
        df['time'] = df.time.dt.strftime('%Y%m%d').astype(int)
        df['name'] = name
        df = df[['name', 'time', 'open', 'high', 'low', 'close', 'volume']]
    except:
        try:
            return "failed"
        except:
            pass
    return df


# %%
def getPriceData(epicList, combined, api, s):
    
    failed = []

    for epic in tqdm(epicList):
        if log.loc[epic]['from'] == "none":
            newdf = getDF(epic, initialStart, initialEnd, s)
            if type(newdf) == str:
                failed.append(epic)
                continue
            else:
                combined = pd.concat([combined, newdf], ignore_index=True).drop_duplicates().reset_index(drop=True)
                log.loc[epic]['from'] = initialStart
                log.loc[epic]['to'] = initialEnd
        else:
            toDate = (datetime.datetime.today() + datetime.timedelta(-1)).strftime("%Y-%m-%d")
            if log.loc[epic]['to'] == toDate:
                continue
            fromDate = pd.to_datetime(log.loc[epic]['to']).strftime("%Y-%m-%d")
            
            newdf = getDF(epic, fromDate, toDate, s)
            if type(newdf) == str:
                failed.append(epic)
                continue
            else:
                combined = pd.concat([combined, newdf], ignore_index=True).drop_duplicates().reset_index(drop=True)
                log.loc[epic]['to'] = toDate
        
    if len(failed) != 0:
        try:
            api = ApiKeys[ApiKeys.index(api) + 1]
            s = login(api)
        except IndexError:
            print("No More API Keys Left To Try")
            writeLog(log)
            return combined, failed

        combined, failed = getPriceData(failed, combined, api, s)
    
    writeLog(log)
    return combined, failed


# %%
def getApiKey():
    api = ApiKeys[0]
    return api

def setup(api):
    s = login(api)

    log = readLog()
    return s, log

def run(api, s, log):
    
    existingProcessedData = os.listdir('./Data/processed/')
    combined = pd.DataFrame(columns=['name', 'time', 'open', 'high', 'low', 'close', 'volume'])
    print("Loading Previously Downloaded Data")
    for path in tqdm(existingProcessedData):
        combined = pd.concat([combined, pd.read_csv('./Data/processed/' + path, names=['name', 'time', 'open', 'high', 'low', 'close', 'volume'])], ignore_index=True).drop_duplicates().reset_index(drop=True)

    combined, failed = getPriceData(epicList, combined, api, s)
    combined.sort_values(by=['time', 'name'], inplace=True)
    combined.reset_index(drop=True, inplace=True)
    days = np.unique(combined.time)

    print("Writing New Data")
    for day in tqdm(days):
        combined[combined.time == day].to_csv('./Data/processed/' + str(day) + '.txt', index=None, header=None)


# %%
api = getApiKey()
s, log = setup(api)


# %%
run(api, s, log)


# %%
api = getApiKey()
run(api, s, log)


