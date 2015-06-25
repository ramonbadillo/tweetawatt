import json
import urllib2 #library to POST in the API
import os.path #library to read and delete files
import httplib
from time import gmtime, strftime
from pprint import pprint



devUrl = ""
data = {}
user = ""
recordsUrl = ""
#file name of the lost Data
fname = 'lostData.json'

class apiElectro(object):


    def __init__(self,devUrl,userUrl,recordsUrl):
        super(apiElectro, self).__init__()
        self.devUrl = devUrl
        self.user = userUrl
        self.recordsUrl = recordsUrl



    def postElectroRegistry(self,watts,amp,volts,idKill,kwh,idDev):
        #Create a dictionary
        data['watts'] = watts
        data['kwh'] = kwh
        data['amp'] = amp
        data['volts'] = volts
        data['idKill'] = idKill
        data['timeStampClient'] = strftime("%Y-%m-%d %H:%M:%S", gmtime()) #takes the time of the client and format to post in the API
        data['idDev'] = self.devUrl + idDev + "/"
        data['user'] = self.user


        self.postTo(self.recordsUrl,data)


    def postTo(self,url,data):
        #try to POST in the server
        try:

            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')
            jdata = json.dumps(data)
            response = urllib2.urlopen(req,jdata)


            #check if the file exists, and POST every single item in the Server
            if os.path.isfile(fname):
                if os.path.isfile(fname):
                    #open a file for read
                    file_object = open(fname).read()
                    #Converts the file object in a jsonObject
                    jsonFile = json.loads(file_object)

                    #Iterate the json file for a single item
                    for record in jsonFile:
                        record['realTime'] = "false" #adds the field realTime and sets on FALSE
                        #POST the record in the Server
                        req = urllib2.Request(url)
                        req.add_header('Content-Type','application/json')
                        jdata = json.dumps(record)
                        response = urllib2.urlopen(req,jdata)

                #Delete the file when finish
                os.remove(fname)

        #Catch the exception when the conection doesnt exists
        except  (urllib2.URLError, httplib.HTTPException) as e:
            print e

            jsonFile = []
            if os.path.isfile(fname):

                if os.stat(fname).st_size != 0:
                    #open a file for read
                    file_object = open(fname).read()
                    #Converts the file object in a jsonObject
                    jsonFile = json.loads(file_object)


            #Adds the new record to a lost Data
            jsonFile.append(data)

            # Open a file for writing
            out_file = open(fname,"wb")

            # Save the dictionary into this file
            # (the 'indent=4' is optional, but makes it more readable)
            json.dump(jsonFile,out_file, indent=4)

            # Close the file
            out_file.close()





















#THE END :)
