import json
import urllib2
from time import gmtime, strftime


#watts = 100
#amp = 100
#volts = 100
#date = "2015-04-10T21:16:32Z"

idDev = "http://electrotecnia.herokuapp.com/api/devices/1/"
data = {}
user = "http://electrotecnia.herokuapp.com/api/users/1/"


class apiElectro(object):
    
    #idGadget = ""
    #idDev = ""
    #data = {}
    
    def __init__(self,idDev,username):
        super(apiElectro, self).__init__()
        self.idDev = idDev
        
        
    def postElectroRegistry(self,watts,amp,volts,idKill):
        data['watts'] = watts
        data['amp'] = amp
        data['volts'] = volts
        data['idKill'] = idKill
        data['timeStampClient'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        data['idDev'] = idDev
        data['user'] = user

        
        self.postTo('http://electrotecnia.herokuapp.com/api/records/',data)
    
    def postTo(self,url,data):
        #url = 'http://electrotecnia.herokuapp.com/api/registrys/'
        req = urllib2.Request(url)
        req.add_header('Content-Type','application/json')
        jdata = json.dumps(data)
        response = urllib2.urlopen(req,jdata)
        
#api = apiElectro("http://electrotecnia.herokuapp.com/api/gadgets/1/","http://electrotecnia.herokuapp.com/api/devices/1/")
#api.postElectroRegistry(100,100,100)
#print strftime("%Y-%m-%d %H:%M:%S", gmtime())