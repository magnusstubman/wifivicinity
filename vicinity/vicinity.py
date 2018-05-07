#!/usr/bin/env python

import sys
import sqlite3 as lite
import datetime
import manuf
import time
# from manuf import *
# from colr import color

con = lite.connect('../maclogger.db')
now = int(time.time())
macParser = manuf.MacParser()


maxAge = 10 * 6 
maxDevices = 500

def getManuf(mac):
    vendor = macParser.get_all(mac)
    m = vendor.manuf
    c = vendor.comment
    if m is None:
        return "\t"

    if c is None:
        return m

    return m + " (" + c + ")"

def totalTime(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    output = ""
    if h > 0:
        output += str(h) + "h, "
    if m > 0:
        output += str(m) + "m, "

    output += str(s) + "s"
    return output


class c:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def addColors(string, age):
    #g = float(age)/float(maxAge)
    if age < 9:
        return c.BOLD + c.UNDERLINE + string + c.ENDC
        #return c.OKGREEN + string + c.ENDC
    else:
        return string

devices = []
with con:
    cur = con.cursor()

    cur.execute("select max(timestamp), max(signalstrength), mac from timestamps inner join macs on timestamps.macid = macs.id where timestamps.timestamp >= (" + str(now) + " - " + str(maxAge) + ") group by timestamps.macid order by timestamps.signalstrength desc;") # limit " + str(maxDevices) + ";")
    timestampRows = cur.fetchall()

    for index, value in enumerate(timestampRows):
        timestamp = int(value[0])
        strength = int(value[1])
        mac = value[2]

        devices.append([strength, mac, timestamp])

#print("max age: " + str(maxAge) + "s")
#print("max devices: " + str(maxDevices))
print("\n[strength] [mac]      [oui]     [seen]")

now = int(time.time())
counter = 0
for device in devices:
    timestampAge = now - device[2]


    essids = []
    with con:
        cur = con.cursor()

        cur.execute('select * from proberequests where macid = (select id from macs where mac = "' + device[1] + '") order by timestamp desc;')
        essids = cur.fetchall()

    

    if len(essids) > 0:
        for essid in essids:
            if essid[3] == 4:
                print(addColors(str(device[0]) + " " + device[1][:-5] + "xx:xx " + getManuf(device[1]) + "\t" + totalTime(timestampAge) + " ago", timestampAge))
                #print(addColors(str(device[0]) + " " + device[1] + " " + getManuf(device[1]) + "\t" + totalTime(timestampAge) + " ago", timestampAge))
                counter+=1
                    
                # Association request             wlan.fc.type_subtype eq 0
                # Association response            wlan.fc.type_subtype eq 1
                # Probe request           wlan.fc.type_subtype eq 4
                # Probe response          wlan.fc.type_subtype eq 5
                # Beacon          wlan.fc.type_subtype eq 8
                # Authentication          wlan.fc.type_subtype eq 11
                # Deauthentication                wlan.fc.type_subtype eq 12

                types = [(0, 'Association request'),(1,'Association response'), (4,'Probe request'), (5,'Probe response'), (8, 'Beacon'), (11, 'Authentication'),(12, 'Deauthentication')]

                for essid in essids:
                    subtype = ''
                    for t in types:
                        if essid[3] == t[0]:
                            subtype = t[1]
                    #print essid
                    print(addColors("\t" + '(' + subtype + ')\t' + str(essid[4]) + "\tseen " + totalTime(now - essid[2]) + " ago:\t" + essid[1], now - essid[2]))
                print ''
        #        if counter >= maxDevices:
        #            break
                break


