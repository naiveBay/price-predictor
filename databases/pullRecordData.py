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

def getSingleItem(opts,itemNumber,printXMLList=True,textDescription = True):
    ''' This gets the results from a single ebay item. Takes eBay item # as input '''
    
    #Create API object
    api = shopping(debug=False, appid=APPID,
                   config_file='ebay.yaml',certid=CERTID, 
                   devid=DEVID)         
    
    #Define arguments for API call
    if textDescription:
        args = {'ItemID':str(itemNumber),
                'IncludeSelector':'TextDescription,ItemSpecifics,Details,ShippingCosts',
                'outputSelector':'AspectHistogram'}
    else:
        args = {'ItemID':str(itemNumber),
                'IncludeSelector':'Description,ItemSpecifics,Details,ShippingCosts',
                'outputSelector':'AspectHistogram'}

    #API call
    api.execute('GetSingleItem', args)
    responseString = api.response_content()
    
  #  if printXMLList: #For debugging / more info
  #      printXML(responseString)

  
    
    return responseString
    
def searchKeyword(opts,keyword,categoryID,toFile=False,complete=False,fakeResponse=False,user='',reggae=False,sortStartNewest=True,printOutput=False,soldOnly=False,pageNumber=1,parseReturn=False,pagenum=1):
    '''Search by keyword for current listings, completed listings, only listings that sold. Can give fake response for offline debugging.'''

    #Create API object
    api = finding(siteid='EBAY-US', debug=False, 
                  appid=APPID, 
                  config_file=opts.yaml,
                  warnings=True)
    
    if complete: callFunction = 'findCompletedItems'
    else:  callFunction = 'findItemsAdvanced'
    
    searchArgs = {'categoryId' : categoryID,  
    #            'aspectFilter': { 'aspectName' : 'Genre', 'aspectValueName':'Reggae, Ska & Dub'},
                'sortOrder' : 'EndTimeSoonest',
                'outputSelector': 'SellerInfo',
                'outputSelector': 'AspectHistogram',
                'itemFilter': {'name':'ListingType','value':'Auction'},
                'paginationInput': { 'entriesPerPage' : 100, 'pageNumber':pageNumber}}
    if user!='': searchArgs['itemFilter'] = {'name' : 'Seller', 'value':user}
    if soldOnly: searchArgs['itemFilter'] =  {'name': 'SoldItemsOnly', 'value':'true'}
    if reggae: searchArgs['aspectFilter'] =  { 'aspectName' : 'Genre', 'aspectValueName':'Reggae, Ska & Dub'}
    if keyword!='': searchArgs['keywords']= keyword
    if sortStartNewest: searchArgs['sortOrder'] = 'StartTimeNewest'
    if pagenum!=1: searchArgs['paginationInput'] =  {'name':'pageNumber','value':pagenum},

    #Make API call or generate fake response
    if fakeResponse:
        print "Loading fake response..."
        with open('eBayoutputstring.txt') as f: file_lines = f.readlines()
        responseString = file_lines[0]
    else:            
        api.execute(callFunction, searchArgs)
        if api.error(): raise Exception(api.error())
        responseString = api.response_content()

    #Find total number of pages for search result
    totalPages = simpleXmlGet(responseString,'totalPages')

    if printOutput: 
        responseDict = parseXML(responseString)
        for record in responseDict: print record['itemId'],'  ',record['currentUSD'],'  ',record['endTime'],'  ',record['title']
        print '\n','Total pages found = ',totalPages,' ... Total items printed = ', len(responseDict)


    if parseReturn: #For debugging / more info
        return parseXML(responseString)
    else:
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

    #Retrieve all information from the ebay xml string
    itemid = simpleXmlGet(ebayResponse,'ItemID')
    title = simpleXmlGet(ebayResponse,'Title')
    subtitle = simpleXmlGet(ebayResponse,'Subtitle')
    starttime = simpleXmlGet(ebayResponse,'StartTime')
    endtime = simpleXmlGet(ebayResponse,'EndTime')
    timestamp = simpleXmlGet(ebayResponse,'Timestamp')
    categoryidprimary = simpleXmlGet(ebayResponse,'PrimaryCategoryID')
    categoryidsecondary = simpleXmlGet(ebayResponse,'SecondaryCategoryID')
    conditionid = simpleXmlGet(ebayResponse,'ConditionID')
    description = simpleXmlGet(ebayResponse,'Description')
    sellerfeedbackscore = simpleXmlGet(ebayResponse,'FeedbackScore')
    sellerfeedbackpercent = simpleXmlGet(ebayResponse,'PositiveFeedbackPercent') 
    returnpolicy =  simpleXmlGet(ebayResponse,'ReturnsAccepted') 
    topratedlisting = simpleXmlGet(ebayResponse,'TopRatedListing')
    globalshipping = simpleXmlGet(ebayResponse,'GlobalShipping')

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
    description = description.replace("'","''")
    itemspecifics = itemspecifics.replace("'","''")
 
    if simpleXmlGet(ebayResponse,'BidCount')=="0":
        startprice=simpleXmlGet(ebayResponse,'CurrentPrice')
    else:
        startprice='unknown'

    if complete=='true':
        endprice=simpleXmlGet(ebayResponse,'CurrentPrice')
    else: endprice=''

    '''    print 'itemid: ',itemid
    print 'title: ',title
    print 'subtitle: ',subtitle
    print 'starttime: ',starttime
    print 'endtime: ',endtime
    print 'timestamp: ',timestamp
    print 'complete: ',complete
    print 'prim cat: ',categoryidprimary
    print 'sec cat: ',categoryidsecondary
    print 'cond id: ',conditionid
    print 'sellerfeedback score: ',sellerfeedbackscore
    print 'sellerfeedback percent: ',sellerfeedbackpercent
    print 'returns: ',returnpolicy
    print 'toprated: ',topratedlisting
    print 'shipping: ',shippingcost
    print 'global shipping: ',str(globalshipping)
    print 'description: ',description
    print 'picture: ',picture
    print 'item specs: ',itemspecifics
    print 'current price: ',currentprice
    print 'bid count: ',bidcount
    print 'hit count: ',hitcount
    print  simpleXmlGet(ebayResponse,'BidCount')
    print 'start price: '
    print 'end price: '
    '''
    
    query="INSERT INTO training_set VALUES ('"+ itemid + "','" + title + "','" + subtitle + "','" + starttime + "','" + endtime + "','" + timestamp + "','" + complete + "','" + categoryidprimary + "','" + categoryidsecondary + "','" + conditionid + "','" + sellerfeedbackscore + "','" + sellerfeedbackpercent + "','" + returnpolicy + "','" + topratedlisting + "','" + shippingcost + "','" + globalshipping + "','" + description + "','" + picture + "','" + itemspecifics + "','" + currentprice + "','" + bidcount + "','" + hitcount + "','" + startprice + "','" + endprice + "')"

    db.execute(query)
    

def updateDatabaseEntries(db,opts):
    qString = "SELECT * FROM training_set ORDER BY itemid"
    for row in db.execute(qString): 
        print
    

def updateSingleEntry(db,opts,itemid):

    ebayResponse = getSingleItem(opts, itemid)
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

    
    query="UPDATE training_set SET currentprice='"+currentprice+"' WHERE itemid='" + itemid + "'"
    db.execute(query)
    query="UPDATE training_set SET bidcount='"+bidcount+"' WHERE itemid='" + itemid + "'"
    db.execute(query)
    query="UPDATE training_set SET hitcount='"+hitcount+"' WHERE itemid='" + itemid + "'"
    db.execute(query)        
    
    if complete=='true':
        query="UPDATE training_set SET complete='"+complete+"' WHERE itemid='" + itemid + "'"
        db.execute(query)
        query="UPDATE training_set SET endprice='"+simpleXmlGet(ebayResponse,'CurrentPrice')+"' WHERE itemid='" + itemid + "'"
        db.execute(query)

        

def ebayScrape():
    '''Main method'''



    training_set = raw_input("Which set? (1 - training, 2 - reggae, 3 - generalrecords) " )

    if training_set=='1':
        conn = sqlite3.connect('training_set.db')
    elif training_set=='2':
        conn = sqlite3.connect('reggae_set.db')
    elif training_set=='3':
        conn = sqlite3.connect('record_set.db')
    else:
        print "you fucked up, loading training_set.db"
        conn = sqlite3.connect('training_set.db')

    db = conn.cursor()

    toDo='0';
    while toDo != 'q':

        print 
        print "************* Welcome to the eBay reggae python script ****************"
        print
        
        print "What would you like to do?"
        print
        print "1. Current listings"
        print "2. Completed listings"
        print "3. Sold listings"
        print "4. Get single item information"
        print "5. Get listings from single user"
        print "6. Print DB"
        print "7. Update single item info in db"
        print "8. Update all items in db"
        print "9. Add lots of items by category"
        print "10. End all be all adding script"
        print "11. Update reggae"
        print "12. update records"
        print 
        
        toDo = raw_input("Select your option: ")
    
        (opts, args) = init_options()
   
        if toDo in ("1","2","3"):  
            print 
            print "Keyword searches require a category number, here are some common ones:"
            print "Records - 176985"
            print "Concert tickets - 173634"
            print "Sports tickets - 173633"
            print "Cars & Trucks - 6001"
            print "Video Game Consoles - 139971"
            print 

            category = raw_input("What category would you like?: ")
            keywords = raw_input("Search keywords: ")

            if toDo=="1": searchKeyword(opts,keywords,categoryID = category,complete=False,printOutput=True)
            if toDo=="2": searchKeyword(opts,keywords,categoryID = category,complete=True,printOutput=True)
            if toDo=="3": searchKeyword(opts,keywords,categoryID = category,complete=True,soldOnly=True,parseReturn=True)
        elif toDo == ("4"):
            responseString = getSingleItem(opts, raw_input("Item number: "))
            print

            insert = raw_input("Would you like to add this to the db? (y/n): ")
            if insert=='y': insertNewItemIntoDb(db,responseString)
        elif toDo == ("5"):
            print "Suggested users: recordlikedirt, tropicalbeatrecords,marsha1107,joespinner116,missionary.visionary,sounds-of-bulk-mania-musik,ebonygirl,vintageja,remchunes, powell6173,cooltime,archive45,moromoromanmooo,paperstax,wheelandturn,wakethetown"
            searchKeyword(opts,'',user=raw_input("User: "),complete=False,printOutput=True)   

        elif toDo=="6":
            qString = "SELECT * FROM training_set ORDER BY itemid"
            for row in db.execute(qString):   print row[0],row[1]

        elif toDo=="7":
            updateSingleEntry(db,opts,'271300444056')
            
            
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

        elif toDo =="9":

            print 
            print "Keyword searches require a category number, here are some common ones:"
            print "Records - 176985"
            print "Concert tickets - 173634"
            print "Sports tickets - 173633"
            print "Cars & Trucks - 6001"
            print "Musical instruments - 619"
            print "Tablets - 171485"
            print "Video Game Consoles - 139971"
            print 

            category = raw_input("What category would you like?: ")
            keywords = raw_input("Search keywords: ")
            responseString=searchKeyword(opts,keywords,categoryID = category,complete=False,printOutput=True)
            responseDict = parseXML(responseString)
            for item in responseDict:
                
                query="SELECT * FROM training_set WHERE itemid='"+item['itemId']+"'"
                results = list(db.execute(query))
                if len(results)==0:
                    print item['itemId']
                    insertNewItemIntoDb(db,getSingleItem(opts,item['itemId']))


        elif toDo == "10":

            addItemsToDb(db,opts,"173634","phish")
            addItemsToDb(db,opts,"173634","justin timberlake")
            addItemsToDb(db,opts,"173634","pearl jam")
            addItemsToDb(db,opts,"173634","kanye west")
            addItemsToDb(db,opts,"173634","george strait")
            addItemsToDb(db,opts,"173634","rihanna")
            addItemsToDb(db,opts,"173634","flaming lips")
            addItemsToDb(db,opts,"173635","book of mormon")
            
            addItemsToDb(db,opts,"6001","porsche")
            addItemsToDb(db,opts,"6001","ferrari")
            addItemsToDb(db,opts,"6001","bmw")
            addItemsToDb(db,opts,"6001","honda")
            addItemsToDb(db,opts,"6001","mercedes")
            addItemsToDb(db,opts,"6001","subaru")
            addItemsToDb(db,opts,"6001","toyota")
            addItemsToDb(db,opts,"6001","tesla")
            
            addItemsToDb(db,opts,"139971","playstation 4")
            addItemsToDb(db,opts,"139971","nintendo")
            addItemsToDb(db,opts,"139971","sega")
        
            addItemsToDb(db,opts,"171485","ipad air")
            
            addItemsToDb(db,opts,"619","gibson")
            addItemsToDb(db,opts,"619","fender")
            

            

        elif toDo == "11":
            addItemsToDb(db,opts,"176985","wailers",reggaeonly=True)
            addItemsToDb(db,opts,"176985","prince buster",reggaeonly=True)
            addItemsToDb(db,opts,"176985","pat kelly",reggaeonly=True)
            addItemsToDb(db,opts,"176985","maytals",reggaeonly=True)
            addItemsToDb(db,opts,"176985","clarendonians",reggaeonly=True)
            addItemsToDb(db,opts,"176985","alcapone",reggaeonly=True)
            addItemsToDb(db,opts,"176985","aitken",reggaeonly=True)
            addItemsToDb(db,opts,"176985","romeo",reggaeonly=True)
            addItemsToDb(db,opts,"176985","gaylads",reggaeonly=True)
            addItemsToDb(db,opts,"176985","dekker",reggaeonly=True)
            addItemsToDb(db,opts,"176985","dillinger",reggaeonly=True)
            addItemsToDb(db,opts,"176985","melodians",reggaeonly=True)
            addItemsToDb(db,opts,"176985","dunkley",reggaeonly=True)            
            addItemsToDb(db,opts,"176985","edwards",reggaeonly=True) 
            addItemsToDb(db,opts,"176985","eccles",reggaeonly=True) 
            addItemsToDb(db,opts,"176985","ellis",reggaeonly=True) 
            addItemsToDb(db,opts,"176985","blank",reggaeonly=True) 
            addItemsToDb(db,opts,"176985","ethiopians",reggaeonly=True) 
            addItemsToDb(db,opts,"176985","higgs",reggaeonly=True)
            addItemsToDb(db,opts,"176985","holt",reggaeonly=True)
            addItemsToDb(db,opts,"176985","hinds",reggaeonly=True)
            addItemsToDb(db,opts,"176985","london",reggaeonly=True)
            addItemsToDb(db,opts,"176985","morgan",reggaeonly=True)
            addItemsToDb(db,opts,"176985","paragons",reggaeonly=True)
            addItemsToDb(db,opts,"176985","ranking",reggaeonly=True)
            addItemsToDb(db,opts,"176985","smith",reggaeonly=True)
            addItemsToDb(db,opts,"176985","tosh",reggaeonly=True)
            addItemsToDb(db,opts,"176985","trinity",reggaeonly=True)
            addItemsToDb(db,opts,"176985","roy",reggaeonly=True)
            addItemsToDb(db,opts,"176985","wilson",reggaeonly=True)
            addItemsToDb(db,opts,"176985","andy",reggaeonly=True)

            addItemsToDb(db,opts,"176985","perry",reggaeonly=True)
            addItemsToDb(db,opts,"176985","coxsone",reggaeonly=True)
            addItemsToDb(db,opts,"176985","duke reid",reggaeonly=True)
            addItemsToDb(db,opts,"176985","buster",reggaeonly=True)

            addItemsToDb(db,opts,"176985","treasure isle",reggaeonly=True)
            addItemsToDb(db,opts,"176985","blue beat",reggaeonly=True)
            addItemsToDb(db,opts,"176985","studio one",reggaeonly=True)
            addItemsToDb(db,opts,"176985","channel one",reggaeonly=True)
            addItemsToDb(db,opts,"176985","gay feet",reggaeonly=True)
            addItemsToDb(db,opts,"176985","high note",reggaeonly=True)
            addItemsToDb(db,opts,"176985","mafia",reggaeonly=True)

            addItemsToDb(db,opts,"176985","dub",reggaeonly=True)
            addItemsToDb(db,opts,"176985","dubplate",reggaeonly=True)
            addItemsToDb(db,opts,"176985","ska",reggaeonly=True)
            addItemsToDb(db,opts,"176985","rocksteady",reggaeonly=True)
            addItemsToDb(db,opts,"176985","",reggaeonly=True)
            addItemsToDb(db,opts,"176985","",reggaeonly=True,pagenumber=2)



            print "ebony girl"
            addItemsToDb(db,opts,"176985","",reggaeonly=True,usersearch="ebonygirl")
            print "tropical beat"
            addItemsToDb(db,opts,"176985","",reggaeonly=True,usersearch="tropicalbeatrecords")
            print "missionary.visionary"
            addItemsToDb(db,opts,"176985","",reggaeonly=True,usersearch="missionary.visionary")

        elif toDo == "12":
            addItemsToDb(db,opts,"176985","",reggaeonly=False)
            addItemsToDb(db,opts,"176985","",reggaeonly=False,pagenumber=2)
            addItemsToDb(db,opts,"176985","",reggaeonly=False,pagenumber=3)
            addItemsToDb(db,opts,"176985","",reggaeonly=False,pagenumber=4)

        else:
            print "no comprendo"

        conn.commit()

def addItemsToDb(db,opts,category,keywords,reggaeonly=False,usersearch='',pagenumber=1):
    print category, " / ",keywords
   
    responseString=searchKeyword(opts,keywords,categoryID = category,complete=False,printOutput=False,reggae=reggaeonly,user=usersearch,pagenum=pagenumber)
    responseDict = parseXML(responseString)
    i=0
    for item in responseDict:               
        query="SELECT * FROM training_set WHERE itemid='"+item['itemId']+"'"
        results = list(db.execute(query))
        if len(results)==0:
            print item['itemId']
            insertNewItemIntoDb(db,getSingleItem(opts,item['itemId']))
            i+=1

    print category, " / ",keywords,": ",i," added"
    print

def parseSingleItemXML(xmlString):
    root = ET.fromstring(xmlString)

    returnList=[]
    newEntry=dict()
    for i in range(0,len(root)):
        root[i].tag
        for ii in range(0,len(root[i])):
            root[i][ii].tag
            if root[i][ii].tag=='Description':
                newEntry['description'] = root[i][ii].text
            if root[i][ii].tag=='ItemID':
                newEntry['itemId'] = root[i][ii].text
            if root[i][ii].tag=='Title':
                newEntry['title'] = root[i][ii].text
                
            for iii in range(0,len(root[i][ii])):
              print


    returnList.append(newEntry)

    return returnList

def parseXML(xmlString):
    ''' This could be done much better ... '''
    root = ET.fromstring(xmlString)

    returnList=[]
   
    for i in range(0,len(root)):
        for ii in range(0,len(root[i])):
            if root[i][ii].tag=='item':
                newEntry=dict()
                
            for iii in range(0,len(root[i][ii])):
                if root[i][ii][iii].tag=='title':
                    newEntry['title'] = root[i][ii][iii].text
                if root[i][ii][iii].tag=='itemId':
                    newEntry['itemId'] = root[i][ii][iii].text
                if root[i][ii][iii].tag=='globalId':
                    newEntry['globalId'] = root[i][ii][iii].text
                if root[i][ii][iii].tag=='location':
                    newEntry['location'] = root[i][ii][iii].text
                if root[i][ii][iii].tag=='country':
                    newEntry['country'] = root[i][ii][iii].text
                if root[i][ii][iii].tag=='galleryURL':
                    newEntry['galleryURL'] = root[i][ii][iii].text

                for iiii in range(0,len(root[i][ii][iii])):
                    if root[i][ii][iii][iiii].tag=='convertedCurrentPrice':
                        newEntry['currentUSD'] = root[i][ii][iii][iiii].text
                    if root[i][ii][iii][iiii].tag=='startTime':
                        newEntry['startTime'] = root[i][ii][iii][iiii].text
                    if root[i][ii][iii][iiii].tag=='endTime':
                        newEntry['endTime'] = root[i][ii][iii][iiii].text
                    if root[i][ii][iii][iiii].tag=='bidCount':
                        newEntry['bidCount'] = root[i][ii][iii][iiii].text
                    if root[i][ii][iii][iiii].tag=='listingType':
                        newEntry['listingType'] = root[i][ii][iii][iiii].text
                    if root[i][ii][iii][iiii].tag=='sellerUserName':
                        newEntry['sellerUserName'] = root[i][ii][iii][iiii].text

            if root[i][ii].tag=='item':
                returnList.append(newEntry)

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



if __name__ == "__main__":
    ebayScrape()
