#!/usr/bin/env python

import os
import sys
import time
import datetime
import threading
import subprocess
from time import sleep
import sqlite3 as lite
from scapy.all import *

freshnessTime = 2

startTime = int(time.time())

con = lite.connect('maclogger.db')


def isTablesExist():
    with con:
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='macs';")
        rows = cur.fetchall()
        return len(rows) > 0

def createTable():
    print "Creating database..."
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE proberequests(id INTEGER PRIMARY KEY  AUTOINCREMENT, essid TEXT NOT NULL UNIQUE, timestamp INTEGER NOT NULL, subtype INTEGER NOT NULL, signalstrength INTEGER NOT NULL, macid INTEGER NOT NULL, FOREIGN KEY(macid) REFERENCES macs(id));")
        cur.execute("CREATE TABLE macs(id INTEGER PRIMARY KEY  AUTOINCREMENT, mac TEXT NOT NULL);")
        cur.execute("CREATE TABLE timestamps(id INTEGER PRIMARY KEY  AUTOINCREMENT, timestamp INTEGER NOT NULL, signalstrength INTEGER NOT NULL, macid INTEGER NOT NULL, FOREIGN KEY(macid) REFERENCES macs(id));")



def getInterfaces():
    res = run('iw dev | grep Interface | cut -f2 | cut -d" " -f2')
    return res.split("\n")[:-1]

def run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    p_status = p.wait()
    (output, err) = p.communicate()
    return output

def isInMonitorMode(interface):
    res = run('iwconfig ' + interface + ' | grep "Mode" | cut -d":" -f2 | cut -d" " -f1 | tr -d "\n" ')
    return res == 'Monitor'

def enableMonitorMode(interface):
    setInterfaceMode(interface, 'monitor')

def setInterfaceMode(interface, mode):
    run('ifconfig ' + interface + ' down')
    run('iwconfig ' + interface + ' mode ' + mode)
    run('ifconfig ' + interface + ' up')

def setInterfaceChannel(interface, channel):
    run('iwconfig ' + interface + ' channel ' + str(channel))

def totalTime(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    output = ""
    if h > 0:
        output += str(h) + "h, "
    output += str(m) + "m, " + str(s) + "s"
    return output
    # return "%d hours, %d minutes, %d seconds" % (h, m, s)

updatedMacs = []
updatedESSIDs = []
def createHandler(con):
    def addMacIfDoesntExist(mac):
        with con:
            cur = con.cursor()
            cur.execute("insert into macs(mac) select \"" + mac + "\" where not exists(select * from macs where mac = \"" + mac + "\");")

    def addTimestamp(mac, signalStrength):
        timestamp = int(time.time())
        with con:
            cur = con.cursor()
            cur.execute("insert into timestamps(timestamp, macid, signalstrength) values (" + str(timestamp) + ", (select id from macs where mac = \"" + mac + "\"), " + str(signalStrength) + ");")
        updatedMacs.append([mac, timestamp])


    def haveWeSeenMacRecently(mac):
        for seenMac in updatedMacs:
            if seenMac[0] == mac:
                if timestampIsRecent(seenMac[1]):
                    return True
                index = updatedMacs.index(seenMac)
                del updatedMacs[index]
        return False

    def haveWeSeenESSIDRecently(essid):
        for seenEssid in updatedESSIDs:
            if seenEssid[0] == essid:
                if timestampIsRecent(seenEssid[1]):
                    return True
                index = updatedESSIDs.index(seenEssid)
                del updatedESSIDs[index]
        return False


    def timestampIsRecent(timestamp):
        now = int(time.time())
        return (timestamp + freshnessTime) > now

    def handle(mac, signalStrength):
        if not haveWeSeenMacRecently(mac):
            addMacIfDoesntExist(mac)
            addTimestamp(mac, signalStrength)

    def handleProbeRequest(mac, essid, subtype, signalStrength):
        s = mac + mac + essid + str(subtype)
        if not haveWeSeenESSIDRecently(s):
            timestamp = int(time.time())
            updatedESSIDs.append([s, timestamp])
            with con:
                cur = con.cursor()
                timestamp = int(time.time())

                cur.execute('INSERT OR IGNORE INTO proberequests (essid, timestamp, subtype, signalstrength, macid) VALUES (?, "' + str(timestamp) + '", ' + str(subtype) + ', ' + str(signalStrength) + ',(select id from macs where mac="'+ mac + '"));', (essid,))

                cur.execute('UPDATE proberequests SET timestamp = ' + str(timestamp) + ', signalstrength=? WHERE essid=? and macid=(select id from macs where mac=?);', (signalStrength, essid, mac,))

    def handlePacket(packet):
        if packet.haslayer(Dot11):
            signalStrength = -(256 - ord(packet.notdecoded[-2:-1]))
            mac = packet.addr2
            if mac is not None and mac is not '00:00:00:00:00:00':
                if len(mac) == 17:
                    handle(mac, signalStrength)
                if packet.type == 0: #and packet.subtype == 4:

#Association request	 	wlan.fc.type_subtype eq 0
#Association response	 	wlan.fc.type_subtype eq 1
#Probe request	 	wlan.fc.type_subtype eq 4
#Probe response	 	wlan.fc.type_subtype eq 5
#Beacon	 	wlan.fc.type_subtype eq 8
#Authentication	 	wlan.fc.type_subtype eq 11
#Deauthentication	 	wlan.fc.type_subtype eq 12

                    #wantedSubtypes = [0, 1, 4, 5, 8, 11, 12]
                    wantedSubtypes = [4]
                    subtype = packet.subtype
                    if subtype in wantedSubtypes:
                        essid = packet.info
                        if essid is not None:
                            if essid is '':
                                essid = '(Broadcast)'
                            handleProbeRequest(mac, essid, subtype, signalStrength)

                print "\rStarted " + totalTime(int(time.time()) - startTime) + " ago. " +  str(len(updatedMacs)) + " unique devices detected. Just detected: " + mac ,
                sys.stdout.flush()

    return handlePacket

def worker(interface, channel, counter=0):
    try:
        counter += 1
        if not isInMonitorMode(interface):
            enableMonitorMode(interface)

        setInterfaceChannel(interface, channel)
        con = lite.connect('maclogger.db')
        sniff(iface=interface, prn=createHandler(con), store=0)
    except Exception as e:
        if counter < 30:
            run("rfkill unblock wifi")
            run("rfkill unblock all")
            worker(interface, channel, counter)
        else:
            print "\nThread on " + interface + " channel " + str(channel) + " threw exception (" + str(e) + "). Was restarted " + str(counter) + " times but still fails"


channelWishlist = [1,6,11,9,3,8,10,5,2,7,12,13,4,14][::-1]

if not isTablesExist():
    createTable()

interfaces = getInterfaces()

counter = 0
for interface in interfaces:
    counter += 1
    channel = channelWishlist.pop()
    print "Starting thread " + str(counter) + " on " + interface + " channel " + str(channel)

    t = threading.Thread(target=worker, args=[interface, channel])
    t.daemon = True
    t.start()

print str(counter) + " threads started."
print "press ctrl-c to stop logging"
print

while True:
    print "\rStarted " + totalTime(int(time.time()) - startTime) + " ago. " +  str(len(updatedMacs)) + " unique devices detected.",
    sys.stdout.flush()
    time.sleep(1)
