import os
import ConfigParser

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



print urlRecords
