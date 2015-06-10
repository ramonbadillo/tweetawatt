import json
import urllib2
from time import gmtime, strftime


devUrl = ""
data = {}
user = ""
recordsUrl = ""

class apiElectro(object):


    def __init__(self,devUrl,userUrl,recordsUrl):
        super(apiElectro, self).__init__()
        self.devUrl = devUrl
        self.user = userUrl
        self.recordsUrl = recordsUrl



    def postElectroRegistry(self,watts,amp,volts,idKill,kwh,idDev):
        data['watts'] = watts
        data['kwh'] = kwh
        data['amp'] = amp
        data['volts'] = volts
        data['idKill'] = idKill
        data['timeStampClient'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        data['idDev'] = self.devUrl + idDev + "/"
        data['user'] = self.user

        self.postTo(self.recordsUrl,data)


    def postTo(self,url,data):

        req = urllib2.Request(url)
        req.add_header('Content-Type','application/json')
        jdata = json.dumps(data)
        response = urllib2.urlopen(req,jdata)
