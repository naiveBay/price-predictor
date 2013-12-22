import sqlite3
import time

####################################################################################################
## Constants

CAT             = 7;  # Category ID column
TITLE           = 1;  # Title column
BID_COUNTS      = 20; # Bid Count column
END_PRICE       = 23; # End Price column
START_PRICE     = 22; # Start Price column
ITEM_SPECS      = 18; # Item Specs column
GLOBAL_SHIPPING = 15; # Global Shipping column
SHIPPING_PRICE  = 14; # Shipping price column
RETURNS         = 12; # Returns accepted column
FEEDBACK_PERC   = 11; # Seller Feedback Percentage column
FEEDBACK_SCORE  = 10; # Seller Feedback score column
CONDITION_ID    = 9;  # Condition ID column
START_TIME      = 3;  # Start Time column
END_TIME        = 4;  # End time column
HIT_COUNTS      = 21; # Hit counts column
DESCRIPTION     = 16; # Description column

NA              = "";
ROCK            = "Rock";
JAZZ            = "Jazz";
SOUL            = "R&amp;B &amp; Soul";
REGGAE          = "Reggae &amp; Ska";
BLUES           = "Blues";
LATIN           = "Latin";
FOLK            = "Folk";
ELECTRONIC      = "Dance &amp; Electronica";
SOUNDTRACKS     = "Soundtracks &amp; Musicals";
CLASSICAL       = "Classical";
POP             = "Pop"
WORLD           = "World Music";
COUNTRY         = "Country";

####################################################################################################


## Retrieves records from DB and filters based on selections:
#  @param  {Cursor}   db           (SQLite3 cursor)
#  @param  {Bool}     complete
#  @param  {Bool}     sold
#  @param  {Number}   duration (can be 0 meaning all, 3,5,7,10)
#  @param  {String}   genrestring
#  @return {Array[][]} array of items , each row is an item
def getItems(db,complete=True,sold="all",duration=0,genre="",filteritems=True,startprice=[0,99999999],endprice=[0,99999999]):
    qString = "SELECT * FROM training_set";
    #if genre!="": qString += " WHERE itemspecs LIKE '%" + genre + "%'";
    if genre!="": qString += " WHERE itemspecs LIKE '%{''Genre'',''" + genre + "%'";
    items=[];

    for row in db.execute(qString):  
        #Check item completion
        if row[END_PRICE]:  itemComplete = True;
        else:               itemComplete = False;

        #Check if item sold
        bids = hitCountParser(row[BID_COUNTS],row[START_TIME],row[END_TIME])
        if sold == "all":              itemSold = "all";
        elif bids[len(bids)-1][1] > 0: itemSold = True;
        else:                          itemSold = False;

        itemDuration = int(timeStampDifference(row[START_TIME],row[END_TIME]));        

        #Add item to return list if conditions (all but genre) are fulfilled.
        if duration==0:
            if ((complete == itemComplete) and (sold == itemSold) and row[START_PRICE]!="unknown"): 
                if (float(row[START_PRICE])<=startprice[1] and float(row[START_PRICE])>=startprice[0] 
                    and float(row[END_PRICE])<=endprice[1] and float(row[END_PRICE])>=endprice[0] ): items.insert(0,row)
        else: 
            if ((complete == itemComplete) and (sold == itemSold) and row[START_PRICE]!="unknown"): 
                if (float(row[START_PRICE])<=startprice[1] and float(row[START_PRICE])>=startprice[0] 
                    and float(row[END_PRICE])<=endprice[1] and float(row[END_PRICE])>=endprice[0] ): items.insert(0,row)

    if filteritems: filterItems(items);
    return items


## Parses the hit counts, also works for bid counts if you pass bidcountstring for hitcountstring
#  @param  {String}  hitcountsstring
#  @param  {String}  starttimestring
#  @param  {String}  endtimestring
#  @return  {Number[][]} hit counts as a function of time  
def hitCountParser(hitcountsstring,starttimestring,endtimestring):
    itemArray = hitcountsstring.replace("'","").replace("{","").replace("}","").replace("[","").replace("]","").split(",");
    #itemArray is now like [time1,count1,time2,count2,time3,count3...]

    for i in range(0,len(itemArray)/2):
        #Next block makes itemArray = [[time1,count1],[time2,count2],...]
        #Also does some preprocessin: makes numbers -> floats
        itemArray[i] = ",".join([itemArray[i],itemArray[i+1]]).split(",")
        if itemArray[i][1] != '': itemArray[i][1] = float(itemArray[i][1]);
        else: itemArray[i][1] = 0;
        del itemArray[i+1];
    
    #All times in raw format currently. Next block makes times = [0.0,l] where l=length of auction in days 
    duration = timeStampDifference(starttimestring,endtimestring)
    for i in range(0,len(itemArray)):
        itemArray[i][0] = timeStampDifference(starttimestring,itemArray[i][0])

        #If final timestamp is after auction close, change final time stamp to auction close
        if itemArray[i][0] > duration: itemArray[i][0]=duration

    itemArray.insert(0,[0,0])
    return itemArray

## 
# @param {String} starttimestring
# @param {String} endtimestring
# @return {Number} duration of auction
def timeStampDifference(starttimestring,endtimestring):
    if (starttimestring=='' or endtimestring==''): return -1;
    else:    
        t1 = time.strptime(starttimestring.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        t2 = time.strptime(endtimestring.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        return (time.mktime(t2)-time.mktime(t1))/60/60/24;    

## Filters items based on some features:
#  @param  {Array[][]}  items
#  @return {Array[][]}  array of items , each row is an item
def filterItems(items):
    #Discard items based on keywords in text description:
    print "# of items pre filtering: ",len(items)

    badItems = []
    badWords = ["skips","damaged","broken","warped","skip","damage","scuffs","scratches"]

    for row in items:
        textDesc = row[DESCRIPTION];
        for word in badWords:
            if word in textDesc and row not in badItems:
                badItems.append(row)
                
    for row in badItems:
        items.remove(row)

    print "# of items after filtering: ",len(items)
    return items

def didItemSell(item):
        bids = hitCountParser(item[BID_COUNTS],item[START_TIME],item[END_TIME])
        if bids[len(bids)-1][1] > 0: return True;
        else:                        return False;




