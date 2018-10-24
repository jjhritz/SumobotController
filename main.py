"""
@package docstring
Module: main
Project: SumobotController
Description: Driver for the NUBcore #060 ESP8266 that receives commands from the Raspberry Pi

Runs a tiny HTTP server that takes HTTP GET requests from the RasPi, extracts a command, and forwards it via UART
to the Arduino UNO that controls the Zumo Shield.

Date: 10/18/2018
Author: John J. Hritz
Email: john-j-hritz@sbcglobal.net
"""

# minime 'main.py'
# ESP8266 to Arduino Bot remote test

print('minime NUBcore 20180912 16:27')

import uos, machine
from machine import Pin, UART
from time import sleep_ms
import socket

BOT_MODE = False                                    # Set true if the ESP8266 is controlling a bot.
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]     # requests the IP address of the ESP 8266
print('listening on', addr)

s = socket.socket()                                 # TCP Socket used to handle HTTP requests

# Bind the socket to an IP address and TCP port 80
s.bind(addr)

# Start listening on the port
s.listen(1)


led4 = Pin(4, Pin.OUT)
led5 = Pin(5, Pin.OUT)

button0 = Pin(0, Pin.IN) # has hw PU
button2 = Pin(2, Pin.IN, Pin.PULL_UP)

# blink, blink, blink...
led4.value(1)
sleep_ms(20)
led4.value(0)
sleep_ms(80)
led5.value(1)
sleep_ms(20)
led5.value(0)
sleep_ms(80)
led4.value(1)
sleep_ms(20)
led4.value(0)
sleep_ms(80)
led5.value(1)
sleep_ms(20)
led5.value(0)
sleep_ms(80)
led4.value(1)
sleep_ms(20)
led4.value(0)
sleep_ms(80)
led5.value(1)
sleep_ms(20)
led5.value(0)


# Callback function for Interrupt tied to pressing Button 2
def callback(p):
    global BOT_MODE, uart
    if BOT_MODE:
        return

    BOT_MODE = True

    led4.value(1)
    print("BOT MODE 9600bps")
    sleep_ms(1000)
    led4.value(0)
    uos.dupterm(None, 1) # kill REPL UART
    sleep_ms(1000)
    uart = UART(0, 9600) # create bot UART
    uart.init(9600, bits=8, parity=None, stop=1)
    led4.value(1)


button2.irq(trigger=Pin.IRQ_FALLING, handler=callback)


def motor_generic(request):
    """ Writes the extracted command to the UART serial port """
    cmd = request[10:11]
    print(cmd)
    uart.write(cmd)

def extract_request(request_file):
    request = ""  # String of the HTTP request

    # iterate through the file
    with open(request_file) as f:
        for line in f:
            if request == "":
                request = line
            if not line or line == b'\r\n':
                break




def soc_request():
    """ Receives HTTP requests incoming on Port 80 """
    while True:
        # accept the incoming request
        cl, clientaddr = s.accept()
        print('client connected from', clientaddr)

        # Write the HTTP request into a file so we can access it
        cl_file = cl.makefile('rwb', 0)




        """
        while True:
            # read line from file
            line = cl_file.readline()
            if request == "":
                request = line
            if not line or line == b'\r\n':
                break
        """
        motor_generic(request)
        cl.send(b"OK")
        cl.close()
