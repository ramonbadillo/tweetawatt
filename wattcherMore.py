#!/usr/bin/env python
import serial, time, datetime, sys
from xbee import xbee

#import api to Post to the server
from apiElectro import apiElectro


#for read the settings file
import os
import ConfigParser
import logging
from logging import config as _config
import httplib

_config.fileConfig('logging.conf', defaults={'logfilename': 'watts.log'})
logging.debug('Started')
configFile = 'settings.cfg'
##### Read the settings file and assign to the variable

configParser = ConfigParser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(__file__), configFile )
configParser.read(configFilePath)

urlWebApp = configParser.get("webAppSettings","urlWebApp")
urlDevices  = urlWebApp + configParser.get("webAppSettings","urlDevices")
urlRecords = urlWebApp + configParser.get("webAppSettings","urlRecords")

username = configParser.get("userSettings","username")
urlUser  = urlWebApp + configParser.get("userSettings","urlUser")

portCOM = configParser.get("desktopAppSettings","port")
baudrate  = configParser.get("desktopAppSettings","baudrate")
timeToMeasure  = int(configParser.get("desktopAppSettings","timeToMeasure"))


CURRENTSENSE = 4       # which XBee ADC has current draw data
VOLTSENSE = 0          # which XBee ADC has mains voltage data
MAINSVPP = 170 * 2     # +-170V is what 120Vrms ends up being (= 120*2sqrt(2))
vrefs = [492, 492, 482, 492, 501, 493, 0, 0, 0] # approx ((2.4v * (10Ko/14.7Ko)) / 3

CURRENTNORM = 15.5  # conversion to amperes from ADC
NUMWATTDATASAMPLES = 1800 # how many samples to watch in the plot window, 1 hr @ 2s samples


# open up the FTDI serial port to get data transmitted to xbee
ser = serial.Serial(port=portCOM, baudrate=int(baudrate))


onlywatchfor = 0
if (sys.argv and len(sys.argv) > 1):
    onlywatchfor = int( sys.argv[1])
print onlywatchfor


# data that we keep track of, the average watt usage as sent in
avgwattdata = [0] * NUMWATTDATASAMPLES # zero out all the data to start
avgwattdataidx = 0 # which point in the array we're entering new data





####### store sensor data and array of histories per sensor
class Fiveminutehistory:
  def __init__(self, sensornum):
      self.sensornum = sensornum
      self.fiveminutetimer = time.time()  # track data over 5 minutes
      self.lasttime = time.time()
      self.cumulativewatthr = 0
      self.cumulativeamp = 0
      self.cumulativevol = 0
      self.cumulativewat = 0
      self.ampN = 0
      self.volN = 0
      self.watN = 0



  def addwatthr(self, deltawatthr):
      self.cumulativewatthr +=  float(deltawatthr)

  def addamp(self, deltaamp):
      self.cumulativeamp +=  float(deltaamp)
      self.ampN += 1

  def addvol(self, deltavol):
      self.cumulativevol +=  float(deltavol)
      self.volN += 1

  def addwat(self, deltawat):
      self.cumulativewat +=  float(deltawat)
      self.watN += 1

  def reset5mintimer(self):
      self.cumulativewatthr = 0
      self.cumulativeamp = 0
      self.cumulativevol = 0
      self.cumulativewat = 0
      self.ampN = 0
      self.volN = 0
      self.watN = 0

      self.fiveminutetimer = time.time()

  def avgwattover5min(self):
      return self.cumulativewatthr

  def avgamp(self):
      return self.cumulativeamp/self.ampN
  def avgvol(self):
      return self.cumulativevol/self.volN
  def avgwat(self):
      return self.cumulativewat /self.watN



  def __str__(self):
      return "[ id#: %d, 5mintimer: %f, lasttime; %f, cumulativewatthr: %f ]" % (self.sensornum, self.fiveminutetimer, self.lasttime, self.cumulativewatthr)


####### array of histories
sensorhistories = []
sensorLastTime ={}

####### retriever
def findsensorhistory(sensornum):
    for history in sensorhistories:
        if history.sensornum == sensornum:
            return history
    # none found, create it!
    history = Fiveminutehistory(sensornum)
    sensorhistories.append(history)
    return history

###### read the settings file and
def getSettings():
    configParser = ConfigParser.RawConfigParser()
    configFilePath = os.path.join(os.path.dirname(__file__), 'settings.cfg')
    configParser.read(configFilePath)

    urlWebApp = configParser.get("webAppSettings","urlWebApp")
    urlDevices  = configParser.get("webAppSettings","urlDevices")
    urlRecords = configParser.get("webAppSettings","urlRecords")


    username = configParser.get("userSettings","username")
    urlUser  = configParser.get("userSettings","urlUser")

    portCOM = configParser.get("desktopAppSettings","port")
    baudrate  = configParser.get("desktopAppSettings","baudrate")
    timeToMeasure  = configParser.get("desktopAppSettings","timeToMeasure")

def restartReader():
    onlywatchfor = 0
    if (sys.argv and len(sys.argv) > 1):
        onlywatchfor = int( sys.argv[1])
    print onlywatchfor


def update_graph():
    global avgwattdataidx, sensorhistories, twittertimer, onlywatchfor

    # grab one packet from the xbee, or timeout
    packet = xbee.find_packet(ser)
    logging.debug('Se ha leido un nuevo paquete del xbee')
    if packet:
        xb = xbee(packet)
        if (onlywatchfor != 0):
            if (xb.address_16 != onlywatchfor):
                return
        logging.debug('llego un paquete del killwatt numero : %s' , str(xb.address_16))

        # we'll only store n-1 samples since the first one is usually messed up
        voltagedata = [-1] * (len(xb.analog_samples) - 1)
        ampdata = [-1] * (len(xb.analog_samples ) -1)
        # grab 1 thru n of the ADC readings, referencing the ADC constants
        # and store them in nice little arrays
        for i in range(len(voltagedata)):
            voltagedata[i] = xb.analog_samples[i+1][VOLTSENSE]
            ampdata[i] = xb.analog_samples[i+1][CURRENTSENSE]


        # get max and min voltage and normalize the curve to '0'
        # to make the graph 'AC coupled' / signed
        min_v = 1024     # XBee ADC is 10 bits, so max value is 1023
        max_v = 0


        voltagedataPablo = voltagedata[:]
        max_v_p = max(voltagedataPablo)
        min_v_p = min(voltagedataPablo)
        valor_int_p = ((max_v_p - min_v_p) / 2) + min_v_p
        for i in range(len(voltagedataPablo)):
            #en la siguiente linea aparece el factor de ajuste proporcionado por expertos de la uaz
            voltagedataPablo[i] = (voltagedataPablo[i] - valor_int_p) * 0.581

        corrientedataPablo = ampdata[:]
        max_c_p = max(corrientedataPablo)
        min_c_p = min(corrientedataPablo)
        valor_intCorriente_p = ((max_c_p - min_c_p) / 2) + min_c_p
        for i in range(len(corrientedataPablo)):
            #en la siguiente linea aparece el factor de ajuste proporcionado por expertos de la uaz
            corrientedataPablo[i] = (corrientedataPablo[i] - valor_intCorriente_p) * 0.062



        for i in range(len(voltagedata)):
            if (min_v > voltagedata[i]):
                min_v = voltagedata[i]
            if (max_v < voltagedata[i]):
                max_v = voltagedata[i]

        # figure out the 'average' of the max and min readings
        avgv = (max_v + min_v) / 2
        # also calculate the peak to peak measurements
        vpp =  max_v-min_v

        for i in range(len(voltagedata)):
            #remove 'dc bias', which we call the average read
            voltagedata[i] -= avgv
            # We know that the mains voltage is 120Vrms = +-170Vpp
            voltagedata[i] = (voltagedata[i] * MAINSVPP) / vpp

        # normalize current readings to amperes
        for i in range(len(ampdata)):
            # VREF is the hardcoded 'DC bias' value, its
            # about 492 but would be nice if we could somehow
            # get this data once in a while maybe using xbeeAPI
            if vrefs[xb.address_16]:
                ampdata[i] -= vrefs[xb.address_16]
            else:
                ampdata[i] -= vrefs[0]
            # the CURRENTNORM is our normalizing constant
            # that converts the ADC reading to Amperes
            ampdata[i] /= CURRENTNORM


        # calculate instant. watts, by multiplying V*I for each sample point
        wattdata = [0] * len(voltagedata)
        for i in range(len(wattdata)):
            wattdata[i] = voltagedataPablo[i] * corrientedataPablo[i]

        # sum up the current drawn over one 1/60hz cycle
        avgamp = 0
        # 16.6 samples per second, one cycle = ~17 samples
        # close enough for govt work :(
        for i in range(17):
            avgamp += corrientedataPablo[i]
        avgamp /= 17.0

        # sum up power drawn over one 1/60hz cycle
        avgwatt = 0
        # 16.6 samples per second, one cycle = ~17 samples
        for i in range(17):
            avgwatt += (wattdata[i])
        avgwatt /= 17.0

        # Add the current watt usage to our graph history
        avgwattdata[avgwattdataidx] = avgwatt
        avgwattdataidx += 1
        if (avgwattdataidx >= len(avgwattdata)):
            # If we're running out of space, shift the first 10% out
            tenpercent = int(len(avgwattdata)*0.1)
            for i in range(len(avgwattdata) - tenpercent):
                avgwattdata[i] = avgwattdata[i+tenpercent]
            for i in range(len(avgwattdata) - tenpercent, len(avgwattdata)):
                avgwattdata[i] = 0
            avgwattdataidx = len(avgwattdata) - tenpercent
        logging.debug('fin del procesamiento de paquete del killwatt numero : %s' , str(xb.address_16))

        # retreive the history for this sensor
        sensorhistory = findsensorhistory(xb.address_16)
        #print sensorhistory

        # add up the delta-watthr used since last reading
        # Figure out how many watt hours were used since last reading
        elapsedseconds = time.time() - sensorhistory.lasttime
        # logging.debug("Antiguo segundos entre envio de xbee = %s" , str(elapsedseconds))
        dwatthr = (avgwatt * elapsedseconds) / (60.0 * 60.0)  # 60 seconds in 60 minutes = 1 hr
        # logging.debug("Antiguo watts hora = %s" , str(dwatthr))
        sensorhistory.lasttime = time.time()
        logging.debug('%s ***** valores killawatt 2 segundos' , "killawatt id = " +str(xb.address_16))
        logging.debug ('watt hora = %s' , str(dwatthr))
        logging.debug ('amp = %s' , str(avgamp))
        logging.debug ('vol = %s' , str(120))
        logging.debug ('watt = %s' , str(avgwatt))
        logging.debug ("---------------------------------")
        sensorhistory.addwatthr(dwatthr)
        sensorhistory.addamp(avgamp)
        sensorhistory.addvol(120)
        sensorhistory.addwat(avgwatt)

        currminute = (int(time.time())/60) % 10
        if ((time.time() - sensorhistory.fiveminutetimer) >= timeToMeasure):
            # Print out debug data, Wh used in last 5 minutes
            avgwattsused = sensorhistory.avgwattover5min()
            logging.debug('%s !!!!!! valores listos para enviarse al servidor' , "killawatt id = " +str(xb.address_16))
            logging.debug ('avg watt hora = %s' , str(avgwattsused))
            logging.debug ('avg amp = %s' , str(sensorhistory.avgwat()))
            logging.debug ('avg vol = %s' , str(sensorhistory.avgvol()))
            logging.debug ('avg watt = %s' , str(sensorhistory.avgwat()))
            logging.debug ("---------------------------------")
            api = apiElectro(urlDevices,urlUser,urlRecords)
            api.postElectroRegistry(sensorhistory.avgwat(),sensorhistory.avgamp(),sensorhistory.avgvol(),str(xb.address_16),avgwattsused,str(xb.address_16))
            print time.strftime("%Y %m %d, %H:%M"),", ",sensorhistory.cumulativewatthr,"Wh = ",avgwattsused," W average"
            print xb.address_16," , ",sensorhistory.cumulativewatthr,"Wh = ",avgwattsused," W average"

            # Reset our 5 minute timer
            sensorhistory.reset5mintimer()


#branch
#Run the function
while True:
    update_graph()
