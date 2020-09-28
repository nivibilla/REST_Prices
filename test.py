import requests



s = requests.Session()
s.headers = {'Content-Type': 'application/json; charset=UTF-8',
             'Accept': 'application/json; charset=UTF-8', 'VERSION': '2', 'X-IG-API-KEY': "db54fdb1f919d3a75304c3ac1c0c0b4953fb86a4"}
data = {'identifier': "eastwind", 'password': "Eastwind1!"}
url = 'https://demo-api.ig.com/gateway/deal'
r = s.post(url + '/session', json=data)
s.headers.update({'X-SECURITY-TOKEN': r.headers['X-SECURITY-TOKEN'], 'CST': r.headers['CST']})
s.headers.update({'Version': '3'})

URL = "https://demo-api.ig.com/gateway/deal/markets/IX.D.FTSE.DAILY.IP"
test = s.get(URL)

print(test.text)