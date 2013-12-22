import sys,os
sys.path.insert(0, '%s/../../functions/' % os.path.dirname(os.path.abspath(__file__)))
from dataScraping import *


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
    '''addNewItems('/home/davidjn/webapps/nbdb/record_set.db',"176985",12)
    addNewItems('/home/davidjn/webapps/nbdb/guitar_set.db',"33034",36)
    addNewItems('/home/davidjn/webapps/nbdb/laptop_set.db',"175672",36)'''

    addNewItems('../../databases/record_set.db',"176985",12)
    addNewItems('../../databases/guitar_set.db',"33034",12)
    addNewItems('../../databases/laptop_set.db',"175672",12)