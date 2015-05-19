import serial
import time

ser = serial.Serial(port='COM4', baudrate=9600, bytesize=8, parity='N', stopbits=1)

START_IOPACKET   = '0x7e'
SERIES1_IOPACKET = '0x83'


while 1 :

	out = ser.read(88)
    # let's wait one second before reading output (let's give device time to answer)
 	time.sleep(1)
 	while ser.inWaiting() > 0:
 		out = hex(ord(ser.read()))
	if out != '':
		print out
		print type(out)