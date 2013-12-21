import os,sys
import urllib,urllib2
import json
import os.path
import xml.etree.ElementTree as ET
import sqlite3
import ebaysdk
from pullRecordData import *
from ebaysdk import finding,trading,shopping
from copy import *
from optparse import OptionParser
sys.path.insert(0, '%s/../' % os.path.dirname(__file__))


#########################################################################################################


## Using this file requires that the eBay python API is already installed. The APPID, CERTID, and DEVID
## global variables must be updated below with those found in the users eBay developer accounts.

## Update the lines below with the information from your eBay developer account.
APPID = 'DavidNic-a026-403b-ade6-36262dc260a3'
CERTID = '625388f8-ad85-4536-88d8-256113d58703'
DEVID = '8b39a15d-e703-47bf-a7e7-db027f79100d'

## Will be important to check over word list and fix things like " = &quot;. 

#########################################################################################################

def addNewItems(db_file,category,results):
    conn = sqlite3.connect(db_file)
    #conn = sqlite3.connect('record_set.db')
    db = conn.cursor()
    addItemsToDb(db,category,"",max_results=results)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    #addNewItems('/home/davidjn/webapps/nbdb/record_set.db',"176985",12)
    #addNewItems('/home/davidjn/webapps/nbdb/guitar_set.db',"33034",12)

    addNewItems('record_set.db',"176985",12)
    addNewItems('guitar_set.db',"33034",12)

    #addNewItems('record_set.db',"176985",12)
    #addNewItems('guitar_set.db',"33034",12)


