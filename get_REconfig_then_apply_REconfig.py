#!/usr/bin/env python
#Author = Lee Yeong Hui
 
from pprint import pprint 
from jnpr.junos import Device
from os.path import dirname, join
from lxml import etree
from jnpr.junos.utils.config import Config
import xml.etree.ElementTree as ET
import getpass
import yaml

try:
    userID = raw_input("Enter username: ")
except: 
    userID = input("Enter username: ")
userPW = getpass.getpass("Enter password: ")

# Get relative directory 
currentDir = dirname(__file__)

# Get hosts.yml relative directory 
filePath = join(currentDir, "hosts.yml")

# Read hosts.yml
with open(filePath, 'r') as rd:
	hosts = yaml.load (rd.read())

aListofDevice = []
# Connect to each device to get firewall filter configuration  
for host in hosts: 
    try:
        print('Collecting data on ' + host)
        #use port 22 if 830 does not work/set system services netconf ssh is not configured
        dev = Device(host=host, user=userID, password=userPW, port="22") 
        dev.open()
              
        filter = '<configuration><interfaces><interface><name>lo0</name></interface></interfaces></configuration>'
        loopbackconfigXML = dev.rpc.get_config(options={'database':'committed','format':'xml'}, filter_xml = filter)
        print ('Data collected from ' + host)
        interface = loopbackconfigXML.findall('.//interface')
        
        if len(interface) > 0: 
            filtername = interface[0].find('.//unit/family/inet/filter/input/filter-name').text
            aDevice = {
            'IP' : host, 
            'filterConfigured' : 'Y',
            'filterName' : filtername
            }
            aListofDevice.append(aDevice)
        else:
            filtername = ''
            aDevice = {
            'IP' : host, 
            'filterConfigured' : 'N',
            'filterName' : ''
            }
            aListofDevice.append(aDevice)
        dev.close()
    except Exception as e:
        print (e)

print ('\n\n')
print ('%s\t\t\t%s\t%s' % ('HOST IP', 'RE FILTER CONFIGURED', 'RE FILTER NAME'))
print ('-'*100)
for aDevice in aListofDevice: 
    print ('%s\t\t\t%s\t\t%s' % (aDevice['IP'], aDevice['filterConfigured'], aDevice['filterName']))
print ('\n\n')


# ask for action
user_input = raw_input(
    """Do you want to 
    1. Configure RE protection on devices that do not have filter configured 
    2. Configure & Re-configure RE protection on all devices
    3. Exit 
    (1/2/3): 
    """)

# Get relative directory 
currentDir = dirname(__file__)

# Get hosts.yml relative directory 
filePath = join(currentDir, "setcommands.txt")

# Read setcommands.txt
setcommands = ""
cmd = open(filePath, 'r')
for aLine in cmd: 
    setcommands += aLine

try: 
    if user_input == '1':
        print ('Configuring RE protection on devices that do not have filter configured')
        try:
            for aDevice in aListofDevice: 
                if aDevice['filterConfigured'] == 'N':
                    print('Configuring RE protection on ' + aDevice['IP'])
                    #use port 22 if 830 does not work/set system services netconf ssh is not configured
                    dev = Device(host=aDevice['IP'], user=userID, password=userPW, port="22") 
                    dev.open()
                    cu = Config (dev)
                    #cu.lock()
                    result = cu.load(setcommands, format="set")
                    #cu.pdiff()
                    cu.commit()
                    #cu.unlock()
                    print('Configured RE protection on ' + aDevice['IP'])
                    dev.close()
        except Exception as e:
            print (e)
    elif user_input == '2':
        print ('Configuring & Re-configuring RE protection on all devices')
        try:
            for aDevice in aListofDevice: 
                print('Configuring RE protection on ' + aDevice['IP'])
                #use port 22 if 830 does not work/set system services netconf ssh is not configured
                dev = Device(host=aDevice['IP'], user=userID, password=userPW, port="22") 
                dev.open()
                cu = Config (dev)
                #cu.lock()
                try:
                    cu.load("delete interfaces lo0 unit 0 family inet filter input", format="set")
                    cu.load("delete firewall filter inet filter protect-re", format="set")
                except Exception as e: 
                    pass #do nothing
                result = cu.load(setcommands, format="set")
                #cu.pdiff()
                cu.commit()
                #cu.unlock()
                print('Configured RE protection on ' + aDevice['IP'])
                dev.close()
        except Exception as e:
            print (e)
    else:
        print ('\nThe program was terminated.\n\n')
except Exception as e: 
    print (e)
