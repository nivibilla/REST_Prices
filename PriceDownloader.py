import requests
import csv
from pathlib import Path
from datetime import datetime, timedelta

ApiKeys = []
e = open("APIKEYS.txt", "r")
for y in e:
    ApiKeys.append(y.strip())
e.close()


def processdata():
    Path("./Data/ProcessedForex/").mkdir(parents=True, exist_ok=True)
    Path("./Data/ProcessedFTSE/").mkdir(parents=True, exist_ok=True)
    with open("FOREX.txt", "r") as forex:
        for line in forex:
            with open("./Data/" + line.strip() + ".txt", "r") as forex2:
                for line2 in forex2:
                    split = line2.split(",")
                    date = split[1]
                    with open("./Data/ProcessedForex/FOREX_" + date + ".txt", "a") as forex_processed:
                        forex_processed.write(line2)

    with open("FTSE.txt", "r") as ftse:
        for line in ftse:
            with open("./Data/" + line.strip() + ".txt", "r") as ftse2:
                for line2 in ftse2:
                    split = line2.split(",")
                    date = split[1]
                    with open("./Data/ProcessedFTSE/FTSE_" + date + ".txt", "a") as ftse_processed:
                        ftse_processed.write(line2)


def download(inp, api):
    username = ""
    password = ""
    i = 0
    d = open("DETAILS.txt", "r")
    for z in d:
        if i == 0:
            username = z.strip()
        elif i == 1:
            password = z.strip()
        i += 1
    d.close()

    length = 0
    failed = []
    if username != "" and password != "":
        f = open(inp + ".txt", "r")
        for x in f:
            try:
                fx = x.strip().upper()
                if inp == "FOREX":
                    FX = ["CS.D.", fx, ".TODAY.IP"]
                elif inp == "FTSE":
                    FX = ["KA.D.", fx, ".DAILY.IP"]

                FX_EPIC = ''.join(FX)

                resolution = "DAY"

                last_line = []
                try:
                    with open("./Data/" + fx + ".txt") as inputfile:
                        for line in inputfile:
                            pass
                        last_line = line.split(",")

                    start = datetime.strptime(last_line[1], "%Y%m%d").strftime("%Y-%m-%d")
                except Exception:
                    start = "2015-01-01"

                # currenttime = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
                currenttime = "2018-01-01"

                if currenttime == start:
                    print("No dates to download for!")
                    continue

                print(start)
                print(currenttime)

                address = ["https://demo-api.ig.com/gateway/deal/prices/", FX_EPIC, "?resolution=", resolution,
                           "&from=", str(start), "&to=", str(currenttime), "&pageSize=0"]
                URL = ''.join(address)
                url = 'https://demo-api.ig.com/gateway/deal'
                s = requests.Session()
                s.headers = {'Content-Type': 'application/json; charset=UTF-8',
                             'Accept': 'application/json; charset=UTF-8', 'VERSION': '2', 'X-IG-API-KEY': api}
                data = {'identifier': username, 'password': password}
                r = s.post(url + '/session', json=data)
                s.headers.update({'X-SECURITY-TOKEN': r.headers['X-SECURITY-TOKEN'], 'CST': r.headers['CST']})
                s.headers.update({'Version': '3'})
                r = s.get(url + '/accounts/')
                # CS.D."insert fx here".CFD.IP
                loc = URL  # for the last 10 mins as default
                test = s.get(loc)
                prices = test.text
                PricesError = prices
                i = 0
                prices_start = 0
                prices_end = 0
                while i < len(prices):
                    if prices[i] == "[":
                        prices_start = i + 1
                    if prices[i] == "]":
                        prices_end = i + 2
                    i += 1

                prices = prices[prices_start:prices_end]
                i = 0
                prices_split = []

                while i < len(prices):
                    if prices[i] == "}":
                        if prices[i + 1] == "," or prices[i + 1] == "]":
                            if prices[i + 2] == "{" or prices[i + 2] == ",":
                                prices_split.append(i + 1)
                    i += 1

                prices_per_min = []
                i = 1
                prices_per_min.append(prices[1:prices_split[0] - 1])
                while i < len(prices_split):
                    prices_per_min.append(prices[prices_split[i - 1] + 2:prices_split[i] - 1])
                    i += 1

                i = 0
                j = 0
                prices_nested = []
                for x in prices_per_min:
                    prices_nested.append(x.split(","))
                toDelete = [1, 3, 4, 6, 7, 9, 10, 12, 13]
                for a in prices_nested:
                    for x in toDelete:
                        del a[x]
                        z = 0
                        while z < len(toDelete):
                            toDelete[z] = toDelete[z] - 1
                            z += 1
                    toDelete = [1, 3, 4, 6, 7, 9, 10, 12, 13]

                firstnum = 0
                lastnum = 0
                time = 0
                highprice = 0
                openprice = 0
                closeprice = 0
                lowprice = 0
                lasttraded = 0
                for a in prices_nested:
                    index = prices_nested.index(a)
                    for x in a:
                        test1 = x[1]
                        test2 = x[2]
                        if test1 == "s" and "U" not in x:
                            time = x[16:26].replace("/", "")
                        elif test1 == "o":
                            openprice = x[19:26]
                        elif test1 == "c":
                            closeprice = x[20:27]
                        elif test1 == "h":
                            highprice = x[19:26]
                        elif test1 == "l" and test2 == "o":
                            lowprice = x[18:25]
                        elif test1 == "l" and test2 == "a":
                            lasttraded = x[19:22]
                    prices_nested[index] = [fx, time, openprice, highprice, lowprice, closeprice, lasttraded]

                name = [fx, ".txt"]
                NAME = ''.join(name)
                with open("./Data/" + NAME, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(prices_nested)
                print(fx + " Downloaded")
            except Exception:
                failed.append(fx)
                print(fx + " is not supported or Exceeded Historical Data Allowance")
                print(PricesError)
                print("")
            length += 1
        f.close()
        if len(failed) != 0:
            print("List of failed Stocks: ", failed)
            print("failed " + str(len(failed)) + " out of " + str(length))
            try:
                download(inp, ApiKeys[ApiKeys.index(api) + 1])
            except IndexError:
                print("No more api keys to try, exiting")
                exit()
    else:
        print("Insert your IG details in the DETAILS.txt and APIKEYS.txt")


download("FOREX", ApiKeys[0])
# download("FTSE", ApiKeys[0])

input2 = ""
while input2 == "":
    input2 = input(
        "type 'process' if processing is needed. Delete files before doing so. otherwise type 'quit' and press Enter: ")
    if input2 == "process":
        processdata()
