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

import uos, machine
from machine import Pin, UART
from utime import sleep_ms
import socket
import ussl
import slimDNS.slimDNS as mdns

print('minime NUBcore 20180912 16:27')

BOT_MODE = False                                    # Set true if the ESP8266 is controlling a bot.
commandString = b'cmd='                             # String that precedes a command in the HTTP request
addr = socket.getaddrinfo('0.0.0.0', 443)[0][-1]    # requests the IP address of the ESP 8266
print('listening on', addr)

s = socket.socket()                                 # TCP Socket used to handle HTTP requests

# Bind the socket to an IP address and TCP port 80
s.bind(addr)

# wrap the socket in a ussl instance to provide TLS/SSL
sec_s = ussl.wrap_socket(s, True, "server.key", "server.crt", ussl.CERT_OPTIONAL, None)


# Start listening on the port
sec_s.listen(1)


led4 = Pin(4, Pin.OUT)
led5 = Pin(5, Pin.OUT)

button0 = Pin(0, Pin.IN)    # has hw PU
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


def callback(p):
    """
    Callback function for Interrupt tied to pressing Button 2.
    Activates Bot Mode, which allows the Nub060 to write to its serial port.  However, this disables REPL over serial.
    :param p: The pin attached to the interrupt.  Passed automatically.
    :return: None
    """
    global BOT_MODE, uart
    if BOT_MODE:
        return

    BOT_MODE = True

    led4.value(1)
    print("BOT MODE 9600bps")
    sleep_ms(1000)
    led4.value(0)
    uos.dupterm(None, 1)    # kill REPL UART
    sleep_ms(1000)
    uart = UART(0, 9600)    # create bot UART
    uart.init(9600, bits=8, parity=None, stop=1)
    led4.value(1)


button2.irq(trigger=Pin.IRQ_FALLING, handler=callback)


def send_command(command):
    """
    Writes the extracted command to the UART serial port.
    :param command: The extracted message that will be sent to the Arduino
    :return: None
    """
    uart.write(command)


def extract_request(request_file):
    """
    Extracts the line containing the GET request from the Raspberry Pi from the request file.
    :param request_file: The file containing the complete HTTP request
    :return: The line containing the HTTP GET request.
    """
    # String of the HTTP request.  Should be the first line of the file.
    request = request_file.readline()
    print(request)

    return request


def extract_command(request_line):
    """
    Extracts the command from the HTTP GET request line.
    :param request_line: The HTTP GET request line.
    :return: The command to forward to the Arduino.
    """
    # Check if this is the GET request and we've received the command string
    if b'GET' in request_line and commandString in request_line:

        """
        Find where the command string and HTTP stuff we don't care about start.
        The command will be between those two.
        """
        cmd_index = request_line.find(commandString)
        http_index = request_line.find(b' HTTP')
        print("cmd_index: " + str(cmd_index))
        print("http_index: " + str(http_index))

        # All hail Slices. The command sits between the end of the command string and the start of the HTTP junk.
        command = request_line[(cmd_index + len(commandString)):http_index]
        print(command)

    else:
        print("Not a valid command line.  Sorry.")

    return command


def soc_request():
    """
    Receives and processes HTTP requests incoming on Port 80
    :return: None
    """
    while True:
        # accept the incoming request
        cl, clientaddr = sec_s.accept()
        print('client connected from', clientaddr)

        # Write the HTTP request into a file so we can access it
        cl_file = cl.makefile('rwb', 0)
        # Extract the HTTP GET request line from the message
        request_line = extract_request(cl_file)
        # Extract the command from the HTTP GET request line
        command = extract_command(request_line)
        # Send the command to the Arduino
        send_command(command)

        # Tell the client something so it will go away
        cl.send(b"OK")

        # Close the file and socket to save memory
        cl_file.close()
        cl.close()
