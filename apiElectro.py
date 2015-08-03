import json
import urllib2 #library to POST in the API
import os.path #library to read and delete files
import httplib
from time import gmtime, strftime
import logging
from socket import error as SocketError
from datetime import datetime
from pytz import timezone


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
        data['timeStampClient'] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()) #takes the time of the client and format to post in the API
        logging.debug("timeStamp enviado al servidor %s ", data['timeStampClient'] )
        data['idDev'] = self.devUrl + idDev + "/"
        data['user'] = self.user


        self.postTo(self.recordsUrl,data)


    def postTo(self,url,data):
        #try to POST in the server
        try:
            logging.debug('Inicia el posteo al servidor')

            req = urllib2.Request(url)
            req.add_header('Content-Type','application/json')
            jdata = json.dumps(data)
            response = urllib2.urlopen(req,jdata)
            logging.debug('finalizo el posteo del valor estandar el posteo al servidor')


            #check if the file exists, and POST every single item in the Server
            if os.path.isfile(fname):
                logging.debug('Inicia la busqueda del archivo de datos perdidos')
                if os.path.isfile(fname):
                    #open a file for read
                    logging.debug('Se encontro el archivo de datos perdidos')
                    file_object = open(fname).read()
                    #Converts the file object in a jsonObject
                    jsonFile = json.loads(file_object)
                    logging.debug('Se cargaron en memoria los archivos de datos perdidos')

                    #Iterate the json file for a single item
                    for record in jsonFile:
                        record['realTime'] = "false" #adds the field realTime and sets on FALSE
                        #POST the record in the Server
                        req = urllib2.Request(url)
                        req.add_header('Content-Type','application/json')
                        jdata = json.dumps(record)
                        response = urllib2.urlopen(req,jdata)
                        logging.debug('Se envia al servidor un registro de datos perdidos')

                #Delete the file when finish
                logging.debug('Se va a borrar el archivo de datos perdidos')
                os.remove(fname)
                logging.debug('El archivo de datos perdidos ha sido borrado')

        #Catch the exception when the conection doesnt exists
        except  (urllib2.URLError, httplib.HTTPException, SocketError) as e:
            logging.error('error al postear al servidor, %s',str(e))

            jsonFile = []
            logging.debug('Inicia proceso de guardado de datos en archivo temporal')
            if os.path.isfile(fname):

                if os.stat(fname).st_size != 0:
                    logging.debug('Se encontro un archivo con datos ya existentes, se va a cargar')
                    #open a file for read
                    file_object = open(fname).read()
                    #Converts the file object in a jsonObject
                    jsonFile = json.loads(file_object)

            logging.debug('Se van a agregar datos al archivo')
            #Adds the new record to a lost Data
            jsonFile.append(data)


            # Open a file for writing
            out_file = open(fname,"wb")

            # Save the dictionary into this file
            # (the 'indent=4' is optional, but makes it more readable)
            logging.debug('Se va a escribir el archivo con datostemporales')
            json.dump(jsonFile,out_file, indent=4)

            # Close the file
            logging.debug('se va a cerrar el archivo con datos temporales')
            out_file.close()
            logging.debug('se ha cerrado el archivo con datos temporales')





















#THE END :)
