from pullRecordData import *

#########################################################################################################

## Using this file requires that the eBay python API is already installed. The APPID, CERTID, and DEVID
## global variables must be updated below with those found in the users eBay developer accounts.

## Update the lines below with the information from your eBay developer account.
APPID = 'DavidNic-a026-403b-ade6-36262dc260a3'
CERTID = '625388f8-ad85-4536-88d8-256113d58703'
DEVID = '8b39a15d-e703-47bf-a7e7-db027f79100d'

## Will be important to check over word list and fix things like " = &quot;. 

#########################################################################################################
    
def updateDb(db_file):
    conn = sqlite3.connect(db_file)
    db = conn.cursor()
    qString = "SELECT * FROM training_set"
    results = list(db.execute(qString))
    for row in results:
        if row[6]!='true':
            updateSingleEntry(db,row[0])
    conn.commit()
    conn.close()

if __name__ == "__main__":
    updateDb('/home/davidjn/webapps/nbdb/record_set.db')
    updateDb('/home/davidjn/webapps/nbdb/guitar_set.db')
    updateDb('/home/davidjn/webapps/nbdb/laptop_set.db')

    #updateDb('record_set.db')
    #updateDb('guitar_set.db')
    #updateDb('laptop_set.db')