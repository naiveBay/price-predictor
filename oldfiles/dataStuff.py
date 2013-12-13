import os,sys
import urllib,urllib2
import os.path
import sqlite3
import time
import operator
#from pylab import *

sys.path.insert(0, '%s/../' % os.path.dirname(__file__))

#SQL ROW INDICES
TITLE = 1;
START_TIME = 3;
END_TIME = 4;
PRIMARY_CAT = 7;
CONDITION_ID = 9;
SELLER_FEEDBACK_SCORE = 10;
SELLER_FEEDBACK_PERCENTAGE = 11;
DESCRIPTION = 16;
ITEM_SPECS = 18;
PRICES = 19;
BIDCOUNTS = 20;
HITCOUNTS = 21;
START_PRICE = 22;
END_PRICE = 23;

#GENRES;
NA = "";
ROCK = "Rock";
JAZZ = "Jazz";
SOUL = "R&amp;B &amp; Soul";
REGGAE = "Reggae &amp; Ska";
BLUES = "Blues";
LATIN = "Latin";
FOLK = "Folk";
ELECTRONIC = "Dance &amp; Electronica";
SOUNDTRACKS = "Soundtracks &amp; Musicals";
CLASSICAL = "Classical";
POP = "Pop"
WORLD = "World Music";
COUNTRY = "Country";


def mainEvent():
    '''Main method'''

    conn = sqlite3.connect('record_set.db')
    db = conn.cursor()

    toDo='0';
    while toDo != 'q':

        print
        print "************* Welcome to the python eBay data analysis script ****************"
        print

        print "What would you like to do?"
        print
        print "1. Plot hitcounts vs time."
        print "2. Plot bidcounts vs time."
        print "3. Plot histograms."
        print "4. Plot prices vs time."
        print "5. Print stats."
        print "6. Some genre statistics (in progress)"
        print

        toDo = raw_input("Select your option: ")

        if toDo == "1":  plotHitCounts(14);
        if toDo == "2":  plotCounts(BIDCOUNTS,4);
        if toDo == "3":
            genre = "";
            priceHistogram("START_PRICE",items="all",genreString=genre);
            priceHistogram("END_PRICE",items="sold",genreString=genre);
            priceHistogram("DIFF_PRICE",items="sold",genreString=genre);
            show()
        if toDo == "4":  plotCounts(PRICES,3);
        if toDo == "5":  printStats();
        if toDo == "6":
            genres = buildGenreDict();
            sorted_genres = sorted(genres.iteritems(), key=operator.itemgetter(1));
            genreNames = [sorted_genres[i][0] for i in range(0,len(sorted_genres))]
            genreCounts = [sorted_genres[i][1] for i in range(0,len(sorted_genres))]

            for item in sorted_genres: print item;

            #how to make histogram of this sorted data with genre labels?
            #  bar(genreNames,genreCounts,align='center')

        else:            print "No comprendo"

        conn.commit()

def getItems(complete=True,sold=False,duration=0,genre=""):
    ''' Searches db file and filters according to parameters
            duration = [0,3,5,7,10]; auction duration in days, 0 = all durations
            genre = see global genre variable names
            '''

    #DB stuff
    conn = sqlite3.connect('record_set.db');
    db = conn.cursor();  qString = "SELECT * FROM training_set ORDER BY itemid";
    items=[];


    for row in db.execute(qString):
        #Check item completion
        if row[END_PRICE]:  itemComplete = True;
        else:               itemComplete = False;

        #Check if item sold
        bids = itemParser(row, row[BIDCOUNTS],BIDCOUNTS)
        if bids[len(bids)-1][1] > 0: itemSold = True;
        else:                        itemSold = False;

        itemDuration = int(timeStampDifference(row[START_TIME],row[END_TIME]));

        #Add item to return list if conditions (all but genre) are fulfilled.
        if duration==0:
            if ((complete == itemComplete) and (sold == itemSold)):
                items.insert(0,row)
        else:
            if ((complete == itemComplete) and (sold == itemSold) and (duration==itemDuration)):
                items.insert(0,row)

    #Now filter by genre if necessary.
    newItems=[];
    if genre!="":
        for row in items:
            itemSpecs = buildItemSpecDict(itemParser(row,row[ITEM_SPECS],ITEM_SPECS,returnType="raw"))
            if "Genre" in itemSpecs.keys(): itemGenre = itemSpecs["Genre"]
            if itemGenre == genre: newItems.insert(0,row);
        items = newItems;

    return items

def itemParser(item,itemString,columnToParse,returnType="days"):
    ''' Parses HITCOUNTS, BIDCOUNTS, PRICES, and ITEM_SPECS.
            item = single row returned from db call
            columnToParse = HITCOUNTS,BIDCOUNTS,PRICES,ITEM_SPECS
            returnType = days --> converts timestamp from HITCOUNTS, BIDCOUNTS, PRICES to float days. Will return error for ITEM_SPECS
                       = anything else returns raw format. Good for ITEM_SPECS.
    '''

    #Start buildling array to return ...
    duration = timeStampDifference(item[START_TIME],item[END_TIME])
    itemArray = itemString.replace("'","").replace("{","").replace("}","").replace("[","").replace("]","").split(",");
    #itemArray is now like [time1,count1,time2,count2,time3,count3...]

    for i in range(0,len(itemArray)/2):
        #Next block makes itemArray = [[time1,count1],[time2,count2],...]
        #Also does some preprocessin: makes numbers -> floats
        itemArray[i] = ",".join([itemArray[i],itemArray[i+1]]).split(",")
        if columnToParse!=ITEM_SPECS:
            if itemArray[i][1] != '': itemArray[i][1] = float(itemArray[i][1]);
            else: itemArray[i][1] = 0;
        del itemArray[i+1];

    #All times in raw format currently. Next block makes times = [0.0,l] where l=length of auction in days
    if returnType == "days":
        for i in range(0,len(itemArray)):
            itemArray[i][0] = timeStampDifference(item[START_TIME],itemArray[i][0])

            #If final timestamp is after auction close, change final time stamp to auction close
            if itemArray[i][0] > duration: itemArray[i][0]=duration

    return itemArray

def timeStampDifference(time1,time2):
    ''' Returns time in days between two timestamps given in eBays format '''
    if (time1=='' or time2==''): return -1;
    else:
        t1 = time.strptime(time1.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        t2 = time.strptime(time2.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        return (time.mktime(t2)-time.mktime(t1))/60/60/24;

def getStartEndPrice(startorend,item):
    ''' Checks for incomplete data. Returns 0 if start price unknown.
        End price should be known for all complete auctions '''

    if startorend=="start": i=START_PRICE;
    else: i=END_PRICE;

    if item[i] == "" or item[i] == "unknown": return 0;
    else: return float(item[i]);

def getGenre(item):
    ''' Returns string with genre for given item. Returns empty string if genre not available '''
    itemSpecs = buildItemSpecDict(itemParser(item,item[ITEM_SPECS],ITEM_SPECS,returnType="raw"))
    if "Genre" in itemSpecs.keys(): return itemSpecs["Genre"]
    else: return ""

def printStats():
    #Counters
    i=0; i_startpricecount=0;
    completed=0; sold=0;
    dur_3days=0; dur_5days=0; dur_7days=0; dur_10days=0; dur_else=0;
    avgstart_all = 0; avgstart_sold = 0; avgend_sold=0;

    #DB stuff
    conn = sqlite3.connect('record_set.db');
    db = conn.cursor();  qString = "SELECT * FROM training_set ORDER BY itemid";

    #Cycle through the db
    for row in db.execute(qString):
        i+=1; i_startpricecount +=1;

        #Check auction completion
        if row[END_PRICE]: completed+=1;

        #Check auction start price
        avgstart_all+=getStartEndPrice("start",row);
        if getStartEndPrice("start",row) == 0:  i_startpricecount-=1;

        #Check if item was sold
        bids = itemParser(row, row[BIDCOUNTS],BIDCOUNTS)
        if bids[len(bids)-1][1] > 0:
            sold+=1;
            avgstart_sold+=getStartEndPrice("start",row);
            avgend_sold+=getStartEndPrice("end",row);

        #Auction duration stuff
        duration = timeStampDifference(row[START_TIME],row[END_TIME])
        if duration == 3: dur_3days+=1;
        elif duration == 5: dur_5days+=1;
        elif duration == 7: dur_7days+=1;
        elif duration == 10: dur_10days+=1;
        else: dur_else+=1;

    #Divide averages out
    avgend_sold=avgend_sold/sold;
    avgstart_sold=avgstart_sold/sold;
    avgstart_all=avgstart_all/i_startpricecount;

    #Print to console
    print "\nTotal auctions in db: ", i;
    print "Completed auctions: ", completed;
    print "Sold auctions: ", sold;
    print "\n3-day auctions: ",dur_3days;
    print "5-day auctions: ",dur_5days;
    print "7-day auctions: ",dur_7days;
    print "10-day auctions: ",dur_10days;
    print "other-day auctions: ",dur_else;
    print "\naverage start price, all records: $",avgstart_all;
    print "average start price, sold records: $",avgstart_sold;
    print "average end price, sold records: $",avgend_sold;

def plotCounts(plotThis=BIDCOUNTS,modNum=5):
    figure(1,figsize=(15, 10), dpi=80)

    i=0
    for row in getItems(complete=True,sold=True,duration=0):
        i+=1;
        if i%modNum==0:
            itemData = itemParser(row,row[plotThis],plotThis,returnType="days");
            itemDataTimes = [itemData[ii][0] for ii in range(0,len(itemData))]
            itemDataCounts = [itemData[ii][1] for ii in range(0,len(itemData))]

            if plotThis==BIDCOUNTS :
                plot(itemDataTimes, itemDataCounts)
                xlabel('Day')
                ylabel('BidCounts')
                title('Bidcounts, Sold Items')
            elif plotThis==PRICES:
                subplot(121);
                plot(itemDataTimes, itemDataCounts);
                xlabel('Day'); ylabel('Price');
                title('Prices, Sold Items');
                axis([0, 10, 0, 300]);
                grid(True); hold(True);
                subplot(122)
                plot(itemDataTimes, itemDataCounts)
                xlabel('Day'); ylabel('Price');
                title('Prices, Sold Items, Rescaled');
                axis([0, 10, 0, 100]);
                grid(True);

    show();

def plotHitCounts(modNum):
    figure(1,figsize=(15, 10), dpi=80)

    i=0
    for row in getItems(complete=True,sold=True,duration=0):
        i+=1;
        if i%modNum==0:
            itemData = itemParser(row,row[HITCOUNTS],HITCOUNTS,returnType="days");
            itemDataTimes = [itemData[ii][0] for ii in range(0,len(itemData))]
            itemDataCounts = [itemData[ii][1] for ii in range(0,len(itemData))]

            subplot(122)
            plot(itemDataTimes, itemDataCounts)
            axis([0, 10, 0, 250])
            xlabel('Day')
            ylabel('Hitcounts')
            title('Hitcounts, Sold Items')
            grid(True)
            hold(True)

    i=0

    for row in getItems(complete=True,sold=False,duration=0):
        i+=1;
        if i%modNum==0:
            itemData = itemParser(row,row[HITCOUNTS],HITCOUNTS,returnType="days");
            itemDataTimes = [itemData[ii][0] for ii in range(0,len(itemData))]
            itemDataCounts = [itemData[ii][1] for ii in range(0,len(itemData))]

            subplot(121)
            plot(itemDataTimes, itemDataCounts)
            axis([0, 10, 0, 250])
            xlabel('Day')
            ylabel('Hitcounts')
            title('Hitcounts, Unsold Items')
            grid(True)
            hold(True)

    show()

def priceHistogram(whichprice,items="all",durationDays=0,genreString=""):
    figure();
    if items=="all":
        items = getItems(complete=True,sold=True,duration=durationDays,genre=genreString)
        items += getItems(complete=True,sold=False,duration=durationDays,genre=genreString)
    elif items=="sold":  items = getItems(complete=True,sold=True,duration=durationDays,genre=genreString)
    else: items = getItems(complete=True,sold=False,duration=durationDays,genre=genreString)


    bins = range(0,200,5)
    counts = [0]*len(bins)
    for row in items:
        if whichprice == "END_PRICE": price = row[END_PRICE];
        elif whichprice == "START_PRICE": price = row[START_PRICE];
        elif whichprice == "DIFF_PRICE":
            if ((row[END_PRICE]!="unknown" and row[END_PRICE]!="") and (row[START_PRICE]!="unknown" and row[START_PRICE]!="")):
                price = float(row[END_PRICE]) - float(row[START_PRICE])
            else: price = 0

        if price!="unknown" and price!="":
            if float(price) <=200-0.5:
                counts[int(floor(float(price)/5))] +=1


    bar(bins,counts,5)

    if whichprice=="END_PRICE":
        title("End Price Histogram")
        ylabel("Counts")
    elif whichprice=="START_PRICE":
        title("Start Price Histogram")
        ylabel("Counts")
    elif whichprice=="DIFF_PRICE":
        title("(End Price - Start Price) Histogram")
        ylabel("Counts")

    xlabel("Prices ($)")

def buildItemSpecDict(itemSpecArray):
    '''Used to convert array of ITEM_SPECS to a dictionary for easy access to Genre, etc'''
    retDict = {};
    for row in itemSpecArray:
        if len(row)>0: retDict[row[0]] = row[1];
    return retDict;

def buildGenreDict():
    ''' Builds a dictionary of genre counts, returns count as a percent '''
    #DB stuff
    conn = sqlite3.connect('record_set.db');
    db = conn.cursor();  qString = "SELECT * FROM training_set ORDER BY itemid";
    genreDict = {};

    #Cycle through the db
    totalCount = 0;
    for row in db.execute(qString):
        totalCount+=1;
        genre = getGenre(row)
        if genre in genreDict.keys(): genreDict[genre]+=1;
        else: genreDict[genre]=1;

    #Convert to percent
    for key in genreDict.keys():
        genreDict[key] = float(genreDict[key])/totalCount*100;

    return genreDict;

if __name__ == "__main__":
    mainEvent()


