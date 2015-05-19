import json
import urllib2

watts = 100
amp = 100
volts = 100
date = "2015-04-10T21:16:32Z"
idGadget = "http://electrotecnia.herokuapp.com/api/gadgets/1/"
idDev = "http://electrotecnia.herokuapp.com/api/devices/1/"
data = {}

data['watts'] = watts
data['amp'] = amp
data['volts'] = volts
data['date'] = date
data['idGadget'] = idGadget
data['idDev'] = idDev



#json_data = json.dumps(data)


url = 'http://electrotecnia.herokuapp.com/api/registrys/'
req = urllib2.Request(url)
req.add_header('Content-Type','application/json')
jdata = json.dumps(data)

response = urllib2.urlopen(req,jdata)

  File "C:\python27\lib\urllib2.py", line 558, in http_error_default
    raise HTTPError(req.get_full_url(), code, msg, hdrs, fp)
urllib2.HTTPError: HTTP Error 403: FORBIDDEN