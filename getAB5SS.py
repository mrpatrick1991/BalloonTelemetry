#!/usr/bin/python
#==============================================================================================================#
#                                                                                                              #
# getAB5SS                                                                                                     #
#                                                                                                              #
# Copyright (C) 2023 Mike Pate - K5MAP                                                                         #
#                                                                                                              #
# This program is free software; you can redistribute it and/or modify                                         #
# it under the terms of the GNU General Public License as published by                                         #
# the Free Software Foundation; either version 2 of the License, or                                            #
# (at your option) any later version.                                                                          #
#                                                                                                              #
# This program is distributed in the hope that it will be useful,                                              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                                               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                                #
# GNU General Public License for more details.                                                                 #
#                                                                                                              #
# You should have received a copy of the GNU General Public License along                                      #
# with this program; if not, write to the Free Software Foundation, Inc.,                                      #
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.                                                  #
#                                                                                                              #
#==============================================================================================================#
#
# if not already installled, use pip to install the following
#
#    pip install ???
#
#==============================================================================================================#
#  Resources
#       Github for AB5SS pico tracker:  ???
#==============================================================================================================#

import logging
import traceback
import urllib.request, urllib.error
import json
import time
import datetime
import math
from socket import *
import pprint

from miscFunctions import *

#--------------------------------------------------------------------------------------------------------------#
def matchAB5SSRecords(jWSPRRec1, jWSPRRec2):
    # determine if 2nd record avilable to process
    logging.info(f" Starting record matching process")
    aResults = []

    print(f"jWSPRRec1 len = {len(jWSPRRec1)}")
    print(f"jWSPRRec2 len = {len(jWSPRRec2)}")

    """
    >>> dicts = [
        { "name": "Tom", "age": 10 },
        { "name": "Mark", "age": 5 },
        { "name": "Pam", "age": 7 },
        { "name": "Dick", "age": 12 }
    ]
    >>> next((item for item in dicts if item["name"] == "Pam"), False)
    {'name': 'Pam', 'age': 7}
    >>> next((item for item in dicts if item["name"] == "Sam"), False)
    False
    >>>

    next((item for item in dicts if item.get("name") and item["name"] == "Pam"), None)
    """
    for i in range(len(jWSPRRec1)):
        if next((item for item in aResults if item['time'] == jWSPRRec1[i]['time']), False) == False:
            aResults.append(jWSPRRec1[i])

    print(f"aResults = {aResults}")
    print(f"aResults len = {len(aResults)}")

    return 


#--------------------------------------------------------------------------------------------------------------#
# Convert callsign of packet #2 into telemetry data
#
#   Grid -  concatenate the grid from the packet (XX99) with the last 2 characters from the 2nd packet callsign
#
#   Channel # - first char of callsign is first digit of channel #; 3rd char of callsign is second digit of channel 
#
#   Speed - ASCII value for 4th char of callsign from 2nd packet; add to ASCII value of "A"; multiple by 5
#
#   Temp - 
#
#   Altitude - take power (dBm) from first packet lookup alt1 in table; take power (dBm) from second packet looking
#              alt2 in table; add both values together to obtain altitude in meters
#
#   Sat status -
#
def decodeCallsign(Packet1, Packet2):
    # use both packets to decode telemetry data
    PowerTable = {
        0: {'alt1' : 0, 'alt2' : 0},
        3: {'alt1' : 1000, 'alt2' : 60},
        7: {'alt1' : 2000, 'alt2' : 120},
        10: {'alt1' : 3000, 'alt2' : 180},
        13: {'alt1' : 4000, 'alt2' : 240},
        17: {'alt1' : 5000, 'alt2' : 300},
        20: {'alt1' : 6000, 'alt2' : 360},
        23: {'alt1' : 7000, 'alt2' : 420},
        27: {'alt1' : 8000, 'alt2' : 480},
        30: {'alt1' : 9000, 'alt2' : 540},
        33: {'alt1' : 10000, 'alt2' : 600},
        37: {'alt1' : 11000, 'alt2' : 660},
        40: {'alt1' : 12000, 'alt2' : 720},
        43: {'alt1' : 13000, 'alt2' : 780},
        47: {'alt1' : 14000, 'alt2' : 840},
        50: {'alt1' : 15000, 'alt2' : 900},
        53: {'alt1' : 16000, 'alt2' : 960},
        57: {'alt1' : 17000, 'alt2' : 0},
        60: {'alt1' : 18000, 'alt2' : 0},
    }
    Callsign1 = "AB5SS"
    sGrid = "EL29"
    Callsign2 = "1Z2RKO"
    Band = 20
    Power1 = 43
    Power2 = 10
    
    # maidenhead grid = EL29KO
    Grid = sGrid + Callsign2[-2:]
    # ???????????????? should last 2 chars be lower case?

    # channel #
    digit1 = int(Callsign2[0]) * 10
    digit2 = int(Callsign2[2])
    Channel = digit1 + digit2

    # speed = 85
    Speed = (ord(Callsign2[3]) - ord("A")) * 5

    # altitude = 13180 (meters)
    Altitude = PowerTable[Power1]['alt1'] + PowerTable[Power2]['alt2']

    # Sat status
    a = ord(Callsign2[1])
    if (a - ord("0")) > 9:
        Sat = chr(((a - 7) % 3) + ord("0"))
    else:
        Sat = chr((a % 3) + ord("0"))

    # temp (celius)
    x = a
    if (x - ord("0")) > 9:
        Temp = (int(((x - ord(Sat) - 7)) / 3) * 5) - 30
    else:
        Temp = (int((x - ord(Sat)) / 3) * 5) - 30

    logging.info(f" Telemetry data:  channel = {Channel}, Grid = {Grid}, Speed = {Speed}, Altitude(m) = {Altitude}, Sat = {Sat}, Temp(c) = {Temp}")

    TelemetryData = {
        "channel" : Channel,
        "grid" : Grid,
        "speed" : Speed,
        "altitude" : Altitude,
        "sat" : Sat,
        "temp" : Temp
    }

    return TelemetryData


#--------------------------------------------------------------------------------------------------------------#
# Convert data to callsign of 2nd packet
#
# 1st char - take the first digit of channel #, convert to int and add ASCII code for 'zero'; then take result and convert back to char
#
# 2nd char
#       if temp minus (-30) / 5
# 
# 3rd char - take remainder of second digit of channel # divided by 10; add ASCII code for 'zero'; convert result back to char
#
# 4th char - if speed greater than 129, assign "Z" else
#       integer of speed / 5 plus ASCII of "A" then convert result back to string      
#
# 5th char - take 5th char of Grid square
#
# 6th char - take 6th char of Grid square
#
def convertCallsign(bCfg):
    gridSquare = "EL29KO"       # !!!!!!!!!!!!!!!!!!!!!!!!
    speed = 89                  # !!!!!!!!!!!!!!!!!!!!!!!!
    temp = 25                   # !!!!!!!!!!!!!!!!!!!!!!!!
    sat = 2                     # !!!!!!!!!!!!!!!!!!!!!!!!
    altitude = 13180            # !!!!!!!!!!!!!!!!!!!!!!!!

    # 1st char
    a = bCfg['channel'][0]      # first digit of channel #
    b = int(a)                  # convert to integer
    c = ord("0")                # convert "zero" to ASCII value
    d = chr(int(a) + ord("0"))
    char1 = d

    # 2nd char
    a = ((int((temp-(-30))/5) *3 ) + sat)
    if a > 9:
        b = ((int((temp-(-30))/5) *3 ) + 7 + sat + ord("0"))
    else:
        b = ((int((temp-(-30))/5) *3 ) + sat + ord("0"))
    char2 = chr(b)

    # 3rd char
    a = bCfg['channel'][1]      # second digit of channel #
    b = int(a)                  # convert to integer
    c = b % 10
    d = chr(c + ord("0"))
    char3 = d

    # 4th char
    if speed > 129:
        char4 = "Z"
    else:
        a = int(speed/5)
        b = chr(a + ord("A"))
        char4 = b

    # 5th char
    char5 = gridSquare[-2]

    # 6th char
    char6 = gridSquare[-1]

    nCallsign = char1 + char2 + char3 + char4 + char5 + char6
    logging.info(f" 2nd packet Callsign = {nCallsign}")

    return nCallsign

#--------------------------------------------------------------------------------------------------------------#
def getAB5SS(bCfg, last_date):
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    wCallsign = bCfg['wsprcallsign']

    """
    Takes a CALLSIGN and gets WSPR spots for that callsign from WSPR Live
    """
    logging.info("#" + ("-"*130))
    logging.info(" Function AB5SS start" )

    #nCallsign = convertCallsign(bCfg)

    query = "SELECT * FROM rx WHERE tx_sign='" + wCallsign + "' AND time > '" + last_date + "' ORDER BY time"
    #query = "SELECT * FROM rx WHERE tx_sign='" + wCallsign + "' AND time > '2022-10-21 00:00:00' AND time < '2022-10-22 00:00:00' ORDER BY time"

    logging.info(" SQL query = " + query )

    url = "https://db1.wspr.live/?query=" + urllib.parse.quote_plus(query + " FORMAT JSON")

    # download contents from wspr.live
    try:
        contents = urllib.request.urlopen(url).read()
    except urllib.error.URLError as erru:
        logging.critical(f" URL error - {erru.reason}" )
        return -1, None
    except urllib.error.HTTPError as errh:
        logging.critical(f" HTTP error - {errh}" )
        return -1, None
    except socket.timeout as errt:
        logging.critical(f" Connection timeout - {errt}" )
        return -1, None
    except:
        logging.critical(f" Unexpected error calling URL - {traceback.format_exc()}" )
        return -1, None

    # check on how many rows returned
    jWsprData = json.loads(contents.decode("UTF-8"))["data"]
    record_count = len(jWsprData)
    logging.info(f" WSPR Live records downloaded = {record_count}" )
    if record_count < 1:
        logging.warning(" Exit function, insufficient WSPR records to process" )
        return 0, None

    pprint.pp(jWsprData)
    print("-"*40)

    callsign = jWsprData[record_count-1]['tx_sign']
    grid = jWsprData[record_count-1]['tx_loc']
    band = jWsprData[record_count-1]['band']
    #query = "SELECT * FROM rx WHERE tx_sign <> '" + callsign + "' AND band=" + str(band) + " AND tx_loc='" + grid + "' AND time > '2022-10-21 00:00:00' AND time < '2022-10-22 00:00:00' ORDER BY time"
    query = "SELECT * FROM rx WHERE tx_sign <> '" + callsign + "' AND band=" + str(band) + " AND tx_loc='" + grid + "' AND time > '" + last_date + "' ORDER BY time"

    logging.info(" SQL query = " + query )

    url = "https://db1.wspr.live/?query=" + urllib.parse.quote_plus(query + " FORMAT JSON")

    # download contents from wspr.live
    try:
        contents = urllib.request.urlopen(url).read()
    except urllib.error.URLError as erru:
        logging.critical(f" URL error - {erru.reason}" )
        return -1, None
    except urllib.error.HTTPError as errh:
        logging.critical(f" HTTP error - {errh}" )
        return -1, None
    except socket.timeout as errt:
        logging.critical(f" Connection timeout - {errt}" )
        return -1, None
    except:
        logging.critical(f" Unexpected error calling URL - {traceback.format_exc()}" )
        return -1, None

    jWsprData2 = json.loads(contents.decode("UTF-8"))["data"]
    record_count = len(jWsprData2)
    logging.info(f" WSPR Live records downloaded = {record_count}" )
    if record_count < 1:
        logging.warning(" Exit function, insufficient matching WSPR records to process" )
        return 0, None

    pprint.pp(jWsprData2)

    # process records downloaded and match
    matchAB5SSRecords(jWsprData, jWsprData2)
    d = decodeCallsign("A", "B")

    return 0