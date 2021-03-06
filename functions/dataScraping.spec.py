import os,sys
import urllib,urllib2
import os.path
import xml.etree.ElementTree as ET
import sqlite3
import ebaysdk
from ebaysdk import finding,trading,shopping
from copy import *
sys.path.insert(0, '%s/../' % os.path.dirname(__file__))


#########################################################################################################

## Using this file requires that the eBay python API (ebaysdk) is already installed. The APPID, CERTID, 
## and DEVID global variables must be updated below with those found in the users eBay developer 
## accounts.

## Update the lines below with the information from your eBay developer account.
APPID = 'DavidNic-a026-403b-ade6-36262dc260a3'
CERTID = '625388f8-ad85-4536-88d8-256113d58703'
DEVID = '8b39a15d-e703-47bf-a7e7-db027f79100d'

## Will be important to check over word list and fix things like " = &quot;. 

#########################################################################################################

## Used to get information for a single eBay item given its item number.
#  @param  { Str  }     itemNumber
#  @return { Str  }     XML string output from API call
def getSingleItem(itemNumber): 

    ## Create API object
    api = shopping(debug=False, appid=APPID,
                   config_file='ebay.yaml',certid=CERTID, 
                   devid=DEVID)        

    ## Define args for API call. Change TextDescription to Description for full HTML description 
    args = {'ItemID':str(itemNumber), 
            'IncludeSelector':'TextDescription,ItemSpecifics,Details,ShippingCosts',
            'outputSelector':'AspectHistogram'} 
    
    ## Make API call
    api.execute('GetSingleItem', args)

    ## Return XML String
    return api.response_content()  

## Used to query eBay for a keyword search. Returns XML string response.
#  @param  { Str  }     keyword
#  @param  { Str  }     categoryID  (ID number)
#  @param  { Bool }     complete    (returns only items that have completed)
#  @param  { Bool }     reggae      (searches only the reggae genre, requires that categoryID = 176985)
#  @param  { int  }     maxresults  (number of items per page to return; max=100)
#  @param  { int  }     pagenum     (100 items max returned, this chooses which page to return)
#  @return { Str  }     XML string output from API call
def searchKeyword(keyword,categoryID,complete=False,reggae=False,maxresults=100,pagenum=1):
    ## Create API object
    api = finding(siteid='EBAY-US', debug=False, 
                  appid=APPID, 
                  config_file='ebay.yaml',
                  warnings=True)
    
    if complete: callFunction = 'findCompletedItems'
    else:  callFunction = 'findItemsAdvanced'
    
    ## Define args for API call.
    args = {'categoryId' : categoryID,  
                'sortOrder' : 'StartTimeNewest',
                'outputSelector': 'SellerInfo,AspectHistogram',    
                'itemFilter': {'name':'ListingType','value':'Auction'},
                'paginationInput': { 'entriesPerPage' : maxresults, 'pageNumber' : pagenum}}
    if reggae: args['aspectFilter'] = { 'aspectName' : 'Genre', 'aspectValueName':'Reggae, Ska & Dub'}
    if keyword!='': args['keywords'] = keyword

    ## Make API call          
    api.execute(callFunction, args)

    ## Return XML String
    return api.response_content()


## Performs a searchKeyword and adds all items to the db that are not already in the db.
#  @param  { Cursor }   db          (SQLite3 database cursor)
#  @param  { Str  }     category    (category ID number)
#  @param  { Str  }     keyword
#  @param  { Bool }     reggaeonly  (searches only the reggae genre)
#  @param  { int  }     max_results (number of items per page to return; max=100)
#  @param  { int  }     pagenumber  (100 items max returned, this chooses which page to return)
def addItemsToDb(db,category,keywords,reggaeonly=False,max_results=100,pagenumber=1):
    print category, " / ",keywords
   
    responseString=searchKeyword(keywords, 
                                    categoryID=category,
                                    complete=False,
                                    reggae=reggaeonly,
                                    maxresults=max_results,
                                    pagenum=pagenumber)

    responseDict = parseXML(responseString)
    
    i=0
    for item in responseDict:               
        query="SELECT * FROM training_set WHERE itemid='"+item['itemId']+"'"
        results = list(db.execute(query))
        if len(results)==0:
            print item['itemId']
            insertNewItemIntoDb(db,getSingleItem(item['itemId']))
            i+=1

    print category, " / ",keywords,": ",i," added"
    print

## Takes ebay XML string for single item and inserts item into db.
#  @param  { Cursor }   db           (SQLite3 database cursor)
#  @param  { Str  }     ebayResponse (ebay XML string output from getSingleItem function)
def insertNewItemIntoDb(db,ebayResponse):
    root = ET.fromstring(ebayResponse)
    item = root.find('Item')
 
    ## Retrieve all information from the ebay xml string
    itemid                  = item.findtext('ItemID','').encode('utf-8')
    title                   = item.findtext('Title','').replace("'","''").encode('utf-8')
    subtitle                = item.findtext('Subtitle','').replace("'","''").encode('utf-8')
    starttime               = item.findtext('StartTime','').encode('utf-8')
    endtime                 = item.findtext('EndTime','').encode('utf-8')
    timestamp               = root.findtext('Timestamp','').encode('utf-8')
    categoryidprimary       = item.findtext('PrimaryCategoryID','').encode('utf-8')
    categoryidsecondary     = item.findtext('SecondaryCategoryID','').encode('utf-8')
    conditionid             = item.findtext('ConditionID','').encode('utf-8')
    description             = item.findtext('Description','').replace("'","''").encode('utf-8')
    sellerfeedbackscore     = item.find('Seller').findtext('FeedbackScore','').encode('utf-8')
    sellerfeedbackpercent   = item.find('Seller').findtext('PositiveFeedbackPercent','').encode('utf-8')
    returnpolicy            = item.find('ReturnPolicy').findtext('ReturnsAccepted','').encode('utf-8')
    topratedlisting         = item.findtext('TopRatedListing','').encode('utf-8')
    globalshipping          = item.findtext('GlobalShipping','').encode('utf-8')

    if ebayResponse.find('need more data to calculate shipping cost')!=-1:
        shippingcost=''.encode('utf-8')
    else:
        shippingcost = item.find('ShippingCostSummary').findtext('ShippingServiceCost','').encode('utf-8')

    picture = item.findtext('PictureURL','').encode('utf-8')
    currentprice = "[{'"+ timestamp + "','" + item.findtext('CurrentPrice','')  + "'}]"
    bidcount = "[{'"+ timestamp + "','" + item.findtext('BidCount','') + "'}]"
    hitcount = "[{'"+ timestamp + "','" + item.findtext('HitCount','') + "'}]"
    if item.find('ItemSpecifics')!=None:
        itemspecifics = parseItemSpecifics(item.find('ItemSpecifics'))
        itemspecifics = itemspecifics.replace("'","''")
    else: itemspecifics = ""
    if timestamp>endtime: complete = 'true'.encode('utf-8')
    else: complete = 'false'.encode('utf-8')

    if item.findtext('BidCount','')=="0":   startprice=item.findtext('CurrentPrice','').encode('utf-8')
    else:                                   startprice='unknown'.encode('utf-8')
    if complete=='true':                    endprice=item.findtext('CurrentPrice','').encode('utf-8')
    else:                                   endprice=''.encode('utf-8')

    ## Some items can go straight into the db in this format, others need some work
    currentprice = currentprice.replace("'","''").encode('utf-8')
    bidcount = bidcount.replace("'","''").encode('utf-8')
    hitcount = hitcount.replace("'","''").encode('utf-8')
    itemspecifics = itemspecifics.encode('utf-8')


    query="INSERT INTO training_set VALUES ('"+ itemid + "','" + title + "','" + subtitle + "','" + starttime + "','" + endtime + "','" + timestamp + "','" + complete + "','" + categoryidprimary + "','" + categoryidsecondary + "','" + conditionid + "','" + sellerfeedbackscore + "','" + sellerfeedbackpercent + "','" + returnpolicy + "','" + topratedlisting + "','" + shippingcost + "','" + globalshipping + "','" + description + "','" + picture + "','" + itemspecifics + "','" + currentprice + "','" + bidcount + "','" + hitcount + "','" + startprice + "','" + endprice + "')"

    db.execute(query)
    
## Takes ebay item ID that is already in DB and updates time information (hits, bids, price). 
#  @param  { Cursor }   db         (SQLite3 database cursor)
#  @param  { Str  }     itemid     (ebay item ID #)
def updateSingleEntry(db,itemid):
    try: 
        root = ET.fromstring(getSingleItem(itemid))
        item = root.find('Item')

        endtime = item.findtext('EndTime','')
        timestamp = root.findtext('Timestamp','')

        currentprice = ",{'"+ timestamp + "','" + item.findtext('CurrentPrice','') + "'}]"
        bidcount = ",{'"+ timestamp + "','" + item.findtext('BidCount','') + "'}]"
        hitcount = ",{'"+ timestamp + "','" + item.findtext('HitCount','') + "'}]"
            
        if timestamp>endtime: complete = 'true'
        else: complete = 'false'

        query="SELECT * FROM training_set WHERE itemid='"+itemid+"'"
        results = db.execute(query)
        for row in results:
            print row[0]
            currentprice = (row[19][:-1]+currentprice).replace("'","''")
            bidcount = (row[20][:-1]+bidcount).replace("'","''")
            hitcount = (row[21][:-1]+hitcount).replace("'","''")

        db.execute("UPDATE training_set SET currentprice='"+currentprice+"' WHERE itemid='" + itemid + "'")
        db.execute("UPDATE training_set SET bidcount='"+bidcount+"' WHERE itemid='" + itemid + "'")
        db.execute("UPDATE training_set SET hitcount='"+hitcount+"' WHERE itemid='" + itemid + "'")        
        
        if complete=='true':
            db.execute("UPDATE training_set SET complete='"+complete+"' WHERE itemid='" + itemid + "'")
            db.execute("UPDATE training_set SET endprice='"+item.findtext('CurrentPrice','') +"' WHERE itemid='" + itemid + "'")

    except:
        pass


## Takes ebay XML string from searchKeyword and parses XML to return a list of dicts. Each dict is
## an eBay item. 
#  @param  { Str  }         xmlString   
#  @return { List[Dict[]]}  returnList
def parseXML(xmlString):
    root = ET.fromstring(xmlString)
    items = root.find("searchResult").findall("item")

    returnList = []

    for item in items:
        newEntry = dict()
        newEntry['title'] = item.findtext('title','')
        newEntry['itemId'] = item.findtext('itemId','')
        newEntry['globalId'] = item.findtext('globalId','')
        newEntry['location'] = item.findtext('location','')
        newEntry['country'] = item.findtext('country','')
        newEntry['galleryURL'] = item.findtext('galleryURL','')
        newEntry['currentUSD'] = item.find('sellingStatus').findtext('convertedCurrentPrice','')
        newEntry['bidCount'] = item.find('sellingStatus').findtext('bidCount','')
        newEntry['startTime'] = item.find('listingInfo').findtext('startTime','')
        newEntry['endTime'] = item.find('listingInfo').findtext('endTime','')
        newEntry['listingType'] = item.find('listingInfo').findtext('listingType','')

        returnList.append(newEntry);

    return returnList


## Takes an itemspec element tree and generates a formatted string for entry into a db.
## [{'SpecName1','SpecValue1'},{'SpecName2','SpecValue2'},{'SpecName3','SpecValue3'}]
#  @param  { ElementTree }     itemspecET   
#  @return { str }             retstring
def parseItemSpecifics(itemspecET):
    retstring = '[';
    for nameValuePair in itemspecET.findall('NameValueList'):
        retstring += "{'" + nameValuePair.findtext('Name') + "','" + nameValuePair.findtext('Value') +  "'},"
    return retstring[:-1]+']'


## Takes XML string and prints to the console in a neat way. Used for visualizing and
## debugging. Not implemented very well.
#  @param  { str }    xmlString   
def printXML(xmlString):
    root = ET.fromstring(xmlString)

    returnList=[]
   
    for i in range(0,len(root)):
        print root[i].tag,root[i].attrib,root[i].text

        for ii in range(0,len(root[i])):
            print '\t', root[i][ii].tag,root[i][ii].attrib,root[i][ii].text          
                
            for iii in range(0,len(root[i][ii])):
                print '\t\t', root[i][ii][iii].tag,root[i][ii][iii].attrib,root[i][ii][iii].text                   

                for iiii in range(0,len(root[i][ii][iii])):
                    print '\t\t\t',root[i][ii][iii][iiii].tag,root[i][ii][iii][iiii].attrib,root[i][ii][iii][iiii].text


## Main Method  
def ebayScrape():

    conn = sqlite3.connect('record_set.db')
    db = conn.cursor()

    toDo='0';
    while toDo != 'q':

        print
        print "************* Welcome to the eBay Data Scraper script ****************"
        print
        
        print "What would you like to do?"
        print
        print "6. Print DB"
        print "8. Update all items in db"
        print "11. Update reggae"
        print "12. update records"
        print 
        
        toDo = raw_input("Select your option: ")

        if toDo=="6":
            qString = "SELECT * FROM training_set ORDER BY itemid"
            for row in db.execute(qString):   print row[0],row[1]
            
        elif toDo=="8":
            startat = int(raw_input("What number to start at?" ))
            qString = "SELECT * FROM training_set"
            results = list(db.execute(qString))

            #if (startat+1000<len(results)): results = results[startat:startat+1000]
            #else: results = results[startat:]
                
            print len(results)

            i = 0
            for row in results:
                i+=1
                print i,len(results)
                
                if row[6]!='true':
                    updateSingleEntry(db,row[0])

        elif toDo == "11":
            addItemsToDb(db,"176985","",reggaeonly=True)
            addItemsToDb(db,"176985","",reggaeonly=True,pagenumber=2)
            addItemsToDb(db,"176985","",reggaeonly=True,pagenumber=3)

        elif toDo == "12":
            addItemsToDb(db,"176985","",reggaeonly=False)
            addItemsToDb(db,"176985","",reggaeonly=False,pagenumber=2)
            addItemsToDb(db,"176985","",reggaeonly=False,pagenumber=3)
            addItemsToDb(db,"176985","",reggaeonly=False,pagenumber=4)

        else:
            print "no comprendo"

        conn.commit()



if __name__ == "__main__":
    ebayScrape()
