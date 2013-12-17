import os,sys
import urllib,urllib2
import json
import os.path
import xml.etree.ElementTree as ET
import sqlite3
import ebaysdk
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


#########################################################################################################

## Used to get information for a single given eBay item via its item number.
#  @param  { Dict }     opts, from init_options
#  @param  { Str  }     itemNumber
#  @return { Str  }     XML string output from API call
def getSingleItem(itemNumber):
    ''' This gets the results from a single ebay item. Takes eBay item # as input '''
    
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
    
def searchKeyword(opts,keyword,categoryID,complete=False,reggae=False,printOutput=False,soldOnly=False,pagenum=1):
    '''Search by keyword for current listings, completed listings, only listings that sold.'''

    ## Create API object
    api = finding(siteid='EBAY-US', debug=False, 
                  appid=APPID, 
                  config_file=opts.yaml,
                  warnings=True)
    
    if complete: callFunction = 'findCompletedItems'
    else:  callFunction = 'findItemsAdvanced'
    
    args = {'categoryId' : categoryID,  
                'sortOrder' : 'StartTimeNewest',
                'outputSelector': 'SellerInfo',
                'outputSelector': 'AspectHistogram',
                'itemFilter': {'name':'ListingType','value':'Auction'},
                'paginationInput': { 'entriesPerPage' : 100, 'pageNumber' : pagenum}}
    if soldOnly: args['itemFilter'] = {'name': 'SoldItemsOnly', 'value':'true'}
    if reggae: args['aspectFilter'] = { 'aspectName' : 'Genre', 'aspectValueName':'Reggae, Ska & Dub'}
    if keyword!='': args['keywords'] = keyword

    #Make API call or generate fake response           
    api.execute(callFunction, args)
    responseString = api.response_content()

    if printOutput: 
        totalPages = simpleXmlGet(responseString,'totalPages')
        responseDict = parseXML(responseString)
        for record in responseDict: print record['itemId'],'  ',record['currentUSD'],'  ',record['endTime'],'  ',record['title']
        print '\n','Total pages found = ',totalPages,' ... Total items printed = ', len(responseDict)

    return responseString

def simpleXmlGet(xmlString,query):
    start = xmlString.find('<'+query+'>')
    if start != -1:
        end = xmlString.find('</'+query+'>')
        return xmlString[start+len('<'+query+'>'):end]
    else: 
        opentagstart = xmlString.find('<'+query)
        if opentagstart != -1:
            opentagend = xmlString.find('>',opentagstart)
            end = xmlString.find('</'+query+'>')
            return xmlString[opentagend+1:end]
        else: return ''
            
def parseItemSpecifics(itemSpecificsXml):
    start = 0
    retstring = '['
    while itemSpecificsXml.find('<NameValueList>')!=-1:
        namevaluelist = simpleXmlGet(itemSpecificsXml,'NameValueList')
   
        name = simpleXmlGet(namevaluelist,'Name')
        value = simpleXmlGet(namevaluelist,'Value')
        retstring += "{'"+name+"','"+value+"'},"

        nvend = itemSpecificsXml.find('</NameValueList>')
        itemSpecificsXml = itemSpecificsXml[nvend+len('</NameValueList>'):]

    return retstring[:-1]+']'
    

def insertNewItemIntoDb(db,ebayResponse):
    #need to parse the ebay response for everything i want, set variables, put them into exstring

    root = ET.fromstring(ebayResponse)
    item = root.find('Item')
    #printXML(ebayResponse)
 
    #Retrieve all information from the ebay xml string
    itemid = item.findtext('ItemID','')
    title = item.findtext('Title','').replace("'","''")
    subtitle = item.findtext('Subtitle','').replace("'","''")
    starttime = item.findtext('StartTime','')
    endtime = item.findtext('EndTime','')
    timestamp = root.findtext('Timestamp','')
    categoryidprimary = item.findtext('PrimaryCategoryID','')
    categoryidsecondary = item.findtext('SecondaryCategoryID','')
    conditionid = item.findtext('ConditionID','')
    description = item.findtext('Description','').replace("'","''")
    sellerfeedbackscore = item.find('Seller').findtext('FeedbackScore','')
    sellerfeedbackpercent = item.find('Seller').findtext('PositiveFeedbackPercent','') 
    returnpolicy =  item.find('ReturnPolicy').findtext('ReturnsAccepted','') 
    topratedlisting = item.findtext('TopRatedListing','')
    globalshipping = item.findtext('GlobalShipping','')

    if ebayResponse.find('need more data to calculate shipping cost')!=-1:
        shippingcost=''
    else:
        shippingcost = simpleXmlGet(ebayResponse,'ShippingServiceCost')

    picture = simpleXmlGet(ebayResponse,'PictureURL')
    currentprice = "[{'"+ timestamp + "','" + simpleXmlGet(ebayResponse,'CurrentPrice') + "'}]"
    bidcount = "[{'"+ timestamp + "','" + simpleXmlGet(ebayResponse,'BidCount') + "'}]"
    hitcount = "[{'"+ timestamp + "','" + simpleXmlGet(ebayResponse,'HitCount') + "'}]"
    if simpleXmlGet(ebayResponse,'ItemSpecifics')!=None:
        itemspecifics = parseItemSpecifics(simpleXmlGet(ebayResponse,'ItemSpecifics'))
    else: itemspecifics = None
    if timestamp>endtime: complete = 'true'
    else: complete = 'false'

    #Some items can go straight into the db in this format, others need some work
    currentprice = currentprice.replace("'","''")
    bidcount = bidcount.replace("'","''")
    hitcount = hitcount.replace("'","''")
    itemspecifics = itemspecifics.replace("'","''")
 
    if simpleXmlGet(ebayResponse,'BidCount')=="0":
        startprice=simpleXmlGet(ebayResponse,'CurrentPrice')
    else:
        startprice='unknown'

    if complete=='true':
        endprice=simpleXmlGet(ebayResponse,'CurrentPrice')
    else: endprice=''
    
    query="INSERT INTO training_set VALUES ('"+ itemid + "','" + title + "','" + subtitle + "','" + starttime + "','" + endtime + "','" + timestamp + "','" + complete + "','" + categoryidprimary + "','" + categoryidsecondary + "','" + conditionid + "','" + sellerfeedbackscore + "','" + sellerfeedbackpercent + "','" + returnpolicy + "','" + topratedlisting + "','" + shippingcost + "','" + globalshipping + "','" + description + "','" + picture + "','" + itemspecifics + "','" + currentprice + "','" + bidcount + "','" + hitcount + "','" + startprice + "','" + endprice + "')"

    db.execute(query)
    

def updateSingleEntry(db,opts,itemid):

    ebayResponse = getSingleItem(itemid)
    endtime = simpleXmlGet(ebayResponse,'EndTime')
    timestamp = simpleXmlGet(ebayResponse,'Timestamp') 
    currentprice = ",{'"+ timestamp + "','" + simpleXmlGet(ebayResponse,'CurrentPrice') + "'}]"
    bidcount = ",{'"+ timestamp + "','" + simpleXmlGet(ebayResponse,'BidCount') + "'}]"
    hitcount = ",{'"+ timestamp + "','" + simpleXmlGet(ebayResponse,'HitCount') + "'}]"
    
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
        db.execute("UPDATE training_set SET endprice='"+simpleXmlGet(ebayResponse,'CurrentPrice')+"' WHERE itemid='" + itemid + "'")

        

def ebayScrape():
    '''Main method'''

    (opts, args) = init_options()
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

            if (startat+1000<len(results)):
                results = results[startat:startat+1000]
            else:
                results = results[startat:]
                
            print len(results)

            i = 0
            for row in results:
                i+=1
                print i,len(results)
                
                if row[6]!='true':
                    updateSingleEntry(db,opts,row[0])

        elif toDo == "11":
            addItemsToDb(db,opts,"176985","",reggaeonly=True)
            addItemsToDb(db,opts,"176985","",reggaeonly=True,pagenumber=2)
            addItemsToDb(db,opts,"176985","",reggaeonly=True,pagenumber=3)

        elif toDo == "12":
            addItemsToDb(db,opts,"176985","",reggaeonly=False)
            addItemsToDb(db,opts,"176985","",reggaeonly=False,pagenumber=2)
            addItemsToDb(db,opts,"176985","",reggaeonly=False,pagenumber=3)
            addItemsToDb(db,opts,"176985","",reggaeonly=False,pagenumber=4)

        else:
            print "no comprendo"

        conn.commit()

def addItemsToDb(db,opts,category,keywords,reggaeonly=False,pagenumber=1):
    print category, " / ",keywords
   
    responseString=searchKeyword(opts,keywords, 
                                    categoryID=category,
                                    complete=False,
                                    printOutput=False,
                                    reggae=reggaeonly,
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

def printXML(xmlString):
    ''' This could be done much better ... '''
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

def init_options():
    ''' Straight up copy from eBay-API examples. Necessary for API calls ''' 

    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="Enabled debugging [default: %default]")
    parser.add_option("-y", "--yaml",
                      dest="yaml", default='ebay.yaml',
                      help="Specifies the name of the YAML defaults file. [default: %default]")
    parser.add_option("-a", "--appid",
                      dest="appid", default=None,
                      help="Specifies the eBay application id to use.")

    (opts, args) = parser.parse_args()
    return opts, args

if __name__ == "__main__":
    ebayScrape()
