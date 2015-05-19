import json
import urllib2
from time import gmtime, strftime


#watts = 100
#amp = 100
#volts = 100
#date = "2015-04-10T21:16:32Z"
idGadget = "http://electrotecnia.herokuapp.com/api/gadgets/1/"
idDev = "http://electrotecnia.herokuapp.com/api/devices/1/"
data = {}


class apiElectro(object):
    
    #idGadget = ""
    #idDev = ""
    #data = {}
    
    def __init__(self, idGadget,idDev):
        super(apiElectro, self).__init__()
        self.idGadget = idGadget
        self.idDev = idDev
        
    def postElectroRegistry(self,watts,amp,volts):
        data['watts'] = watts
        data['amp'] = amp
        data['volts'] = volts
        data['date'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        data['idGadget'] = idGadget
        data['idDev'] = idDev
        
        self.postTo('http://electrotecnia.herokuapp.com/api/registrys/',data)
    
    def postTo(self,url,data):
        #url = 'http://electrotecnia.herokuapp.com/api/registrys/'
        req = urllib2.Request(url)
        req.add_header('Content-Type','application/json')
        jdata = json.dumps(data)
        response = urllib2.urlopen(req,jdata)

#api = apiElectro("http://electrotecnia.herokuapp.com/api/gadgets/1/","http://electrotecnia.herokuapp.com/api/devices/1/")
#api.postElectroRegistry(100,100,100)
#print strftime("%Y-%m-%d %H:%M:%S", gmtime())