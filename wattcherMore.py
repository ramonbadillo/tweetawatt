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
logging.error('new logfilename')
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
      segundos = (time.time() - self.fiveminutetimer)
      logging.debug("segundos watts hora = %s" , str(segundos))
      # factor =(60.0 / segundos)
      # logging.debug("factor = %s" , str(factor))
      # creo que ya no es necesario hacer ninguna división los watt hora ya fueron ajustados antes de sumarse
      return self.cumulativewatthr
      # return self.cumulativewatthr * (segundos/3600)
      # return self.cumulativewatthr * factor #(60.0 / (time.time() - self.fiveminutetimer))

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
    if packet:
        xb = xbee(packet)
        #print xb.address_16
        if (onlywatchfor != 0):
            if (xb.address_16 != onlywatchfor):
                return
            #print xb

        # we'll only store n-1 samples since the first one is usually messed up
        voltagedata = [-1] * (len(xb.analog_samples) - 1)
        ampdata = [-1] * (len(xb.analog_samples ) -1)
        # grab 1 thru n of the ADC readings, referencing the ADC constants
        # and store them in nice little arrays
        for i in range(len(voltagedata)):
            voltagedata[i] = xb.analog_samples[i+1][VOLTSENSE]
            ampdata[i] = xb.analog_samples[i+1][CURRENTSENSE]

        #print ampdata

        # get max and min voltage and normalize the curve to '0'
        # to make the graph 'AC coupled' / signed
        min_v = 1024     # XBee ADC is 10 bits, so max value is 1023
        max_v = 0


        voltagedataPablo = voltagedata[:]
        max_v_p = max(voltagedataPablo)
        min_v_p = min(voltagedataPablo)
        #print "maximo voltage " + str(max_v_p)
        #print "mini voltage " + str(min_v_p)
        valor_int_p = ((max_v_p - min_v_p) / 2) + min_v_p
        #print "valor intp " + str(valor_int_p)
        for i in range(len(voltagedataPablo)):
            #print str(i) + "-------------" + str(i)
            voltagedataPablo[i] = (voltagedataPablo[i] - valor_int_p) * 0.581
            #print "voltage antes de elevar " + str(voltagedataPablo[i])
            #voltagedataPablo[i] = voltagedataPablo[i]**(2)
            #print "voltage despues de elevar " + str(voltagedataPablo[i])

        corrientedataPablo = ampdata[:]
        max_c_p = max(corrientedataPablo)
        min_c_p = min(corrientedataPablo)
        #print "maximo voltage " + str(max_v_p)
        #print "mini voltage " + str(min_v_p)
        valor_intCorriente_p = ((max_c_p - min_c_p) / 2) + min_c_p
        #print "valor intp " + str(valor_int_p)
        for i in range(len(corrientedataPablo)):
            #print str(i) + "-------------" + str(i)
            corrientedataPablo[i] = (corrientedataPablo[i] - valor_intCorriente_p) * 0.062
            #print "voltage antes de elevar " + str(voltagedataPablo[i])
            #voltagedataPablo[i] = voltagedataPablo[i]**(2)
            #print "voltage despues de elevar " + str(voltagedataPablo[i])



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

        #print "Voltage, in volts: ", voltagedata
        #print "Current, in amps:  ", ampdata

        # calculate instant. watts, by multiplying V*I for each sample point
        wattdata = [0] * len(voltagedata)
        for i in range(len(wattdata)):
            wattdata[i] = voltagedataPablo[i] * corrientedataPablo[i]
        # comentado por pablo    wattdata[i] = voltagedata[i] * ampdata[i]

        # sum up the current drawn over one 1/60hz cycle
        avgamp = 0
        # 16.6 samples per second, one cycle = ~17 samples
        # close enough for govt work :(
        for i in range(17):
            #avgamp += abs(ampdata[i])
            avgamp += corrientedataPablo[i]
        avgamp /= 17.0

        # sum up power drawn over one 1/60hz cycle
        avgwatt = 0
        # 16.6 samples per second, one cycle = ~17 samples
        for i in range(17):
            avgwatt += (wattdata[i])
        #comentado por pablo    avgwatt += abs(wattdata[i])
        avgwatt /= 17.0




        '''
        avgvoltp = 0
        print avgv /= 17.0 , ""
        for i in range(17):
            avgvoltp += (voltagedataPablo[i])
        #print "sumatoria volt = " + str(avgvoltp)



        avgvoltp /= 17.0
        #avgvoltp = avgvoltp**(.5)
        print  "average voltage Pablo" + str(avgvoltp)
        '''


        # Print out our most recent measurements
        #print xb.xbeeID
        #print voltaje
        #if xb.address_16 is 1:

        #print str(xb.address_16)+"\tCurrent draw, in amperes: "+str(avgamp)

        #print "\tWatt draw, in VA: "+str(avgwatt)
            #print voltagedata



        ##print api = apiElectro("http://electrotecnia.herokuapp.com/api/gadgets/"+str(xb.xbeeID)+"/","http://electrotecnia.herokuapp.com/api/devices/1/")
        ##api.postElectroRegistry(avgwatt,avgamp,100)

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

        # retreive the history for this sensor
        sensorhistory = findsensorhistory(xb.address_16)
        #print sensorhistory

        # add up the delta-watthr used since last reading
        # Figure out how many watt hours were used since last reading
        elapsedseconds = time.time() - sensorhistory.lasttime
        logging.debug("Antiguo segundos entre envio de xbee = %s" , str(elapsedseconds))
        dwatthr = (avgwatt * elapsedseconds) / (60.0 * 60.0)  # 60 seconds in 60 minutes = 1 hr
        logging.debug("Antiguo watts hora = %s" , str(dwatthr))
        sensorhistory.lasttime = time.time()

        timeElapsed = 0
        logging.debug("llaves dentro de sensorLastTime %s" , str(sensorLastTime.keys()))
        if str(xb.address_16) in sensorLastTime:
            tiempo = time.time()
            timeElapsed = tiempo - sensorLastTime[str(xb.address_16)]
            sensorLastTime[str(xb.address_16)] = tiempo
            logging.debug("segundos entre envio de xbee = %s" , str(timeElapsed))
        else:
            timeElapsed = 2
            sensorLastTime[str(xb.address_16)] = time.time()
            logging.debug("segundos entre envio de xbee  con valor default = %s" , str(timeElapsed))
        dwatthr = (avgwatt * timeElapsed) / (60.0 * 60.0)
        logging.debug('%s valores killawatt 2 segundos' , "killawatt id = " +str(xb.address_16))
        logging.debug ('watt hora = %s' , str(dwatthr))
        logging.debug ('amp = %s' , str(avgamp))
        logging.debug ('vol = %s' , str(120))
        logging.debug ('watt = %s' , str(avgwatt))
        logging.debug ("---------------------------------")
        sensorhistory.addwatthr(dwatthr)
        sensorhistory.addamp(avgamp)
        sensorhistory.addvol(120)
        sensorhistory.addwat(avgwatt)






        # Determine the minute of the hour (ie 6:42 -> '42')
        currminute = (int(time.time())/60) % 10
        #currminute = datetime.datetime.now().second
        # print str(datetime.datetime.now().second) + " - " + str(xb.address_16)
        # Figure out if its been five minutes since our last save
        #if (((time.time() - sensorhistory.fiveminutetimer) >= 60.0) and (currminute >= 1)):
        if ((time.time() - sensorhistory.fiveminutetimer) >= timeToMeasure):
            # Print out debug data, Wh used in last 5 minutes

            avgwattsused = sensorhistory.avgwattover5min()
            logging.debug('%s valores listos para enviarse al servidor' , "killawatt id = " +str(xb.address_16))
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

            logging.debug('%s valores reseteados' , "killawatt id = " +str(xb.address_16))
            logging.debug ('cumulative watt hora = %s' , str(sensorhistory.cumulativewatthr))
            logging.debug ('cumulative amp = %s' , str(sensorhistory.cumulativeamp))
            logging.debug ('cumulative vol = %s' , str(sensorhistory.cumulativevol))
            logging.debug ('cumulative watt = %s' , str(sensorhistory.cumulativewat))
            logging.debug ("---------------------------------")


        # We're going to twitter at midnight, 8am and 4pm
        # Determine the hour of the day (ie 6:42 -> '6')
#branch
#Run the function
while True:
    update_graph()
