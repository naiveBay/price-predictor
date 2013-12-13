import sys
import sqlite3
import json
import math
import numpy as np
import time
#import dataStuff as ds
from random import randint
from copy import deepcopy

#### Some constants to identify particular elements from the Database ##############################
CAT             = 7;  # Category ID column
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

#GENRES;
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

TRAINING_PERC   = 0.7; # Percentage of data set to train for cross validation

ALBUM_ID    = "176985";
CAR_ID      = "10156";
VG_ID       = "139971";
TICKET_ID   = "173634";
conn = sqlite3.connect('record_set.db'); # Connect to the records database

####################################################################################################

## The equivalent of a "main" method
def runScript():
    crossValidate(conn, TRAINING_PERC);

## Uses cross-validation for training and testing
#  @param  {SQLLite3Connection} conn
#  @param  {Number}             p (percentage of data to hold for training)
#  @return {void}
def crossValidate(conn, p):
    [X, Y] = generateDataMatrices(conn);
    Xtrain = [];
    Ytrain = [];
    Xtest = deepcopy(X);
    Ytest = deepcopy(Y);
    m = len(Y);
    numTraining = int(p * m);
    for i in range(numTraining):
        ind = randint(0, len(Xtest)-1);
        Xtrain.append(Xtest.pop(ind));
        Ytrain.append(Ytest.pop(ind));
    # Train on Xtrain
    thetas = trainOnData(Xtrain, Ytrain);
    # Test on Xtest
    testSoftMax(Xtest, Ytest, thetas);

## Trains on a set of data and returns the theta vectors
#  @param  {Number[][]} X
#  @param  {Number[][]} Y
#  @return {Number[][]} The theta vectors
def trainOnData(X, Y):
    Phis = generateProbabilities(Y);
    Mus = generateMeans(X, Y);
    Cov = generateCovarianceMatrix(X, Y, Mus);
    thetas = generateThetaVectors(Phis, Mus, Cov);
    return thetas;

## Test the softmax regression
#  @param {Number[][]} X
#  @param {Number[]}   Y
#  @param {Number[][]} thetas
#  @return {void}
def testSoftMax(X, Y, thetas):
    m = len(Y);
    numCorrect = 0.;
    for i in range(m):
        x = np.append([1], X[i]);
        if(argmaxlikelihood(x, thetas) == Y[i]):
            numCorrect += 1;
    print "Test on Data: Percentage Correct = ", (numCorrect/m)*100, "%";

## Generates the feature vector matrix and associated bin labels ($5 bins)
#  @param  {SQLLite3Connection} conn
#  @return {[Number[][], Number[]]} The feature vector matrix and bin labels i.e. [X, Y]
def generateDataMatrices(conn):
    c = conn.cursor();
    X = []; # The data matrix which will contain feature vectors of our training set
    Y = []; # The end price vector which will contain the end prices (in the $5 bins).
    items = getItems(complete=True);
    for row in items:
        if(row[END_PRICE]):
            if(float(row[END_PRICE]) <= 50):
                Y.append(extractEndPrice(row[END_PRICE]));
                X.append(generateFeatureVector(row));
    return [X, Y];
## Generates the theta vectors
#  @param  {Number[]}   Phis
#  @param  {Number[]}   Mus
#  @param  {Number[][]} Cov
#  @return {Number[][]} The theta vectors corresponding to each bin

def generateThetaVectors(Phis, Mus, Cov):
    thetas = np.zeros((10, getFeatureVectorLength()+1));
    invCov = np.linalg.inv(Cov);
    for j in range(len(Phis)):
        thetas[j][0] = math.log(Phis[j]) - 0.5*np.dot(np.dot(np.transpose(Mus[j]), invCov), Mus[j]);
        thetas[j][1:] = np.dot(np.transpose(invCov), Mus[j]);
    return thetas;

## Generates a vector corresponding to the probability of end price occurence (the Phi values)
#  @param  {Number[]} Y
#  @return {Number[]} The probabilities of each end price
def generateProbabilities(Y):
    Phis = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    m = len(Y);
    for num in Y:
        Phis[num] += 1./m;
    return Phis;

## Generates the 2-d array of vector means. Note that this returns an array of 9 vector means.
#  @param  {Number[][]} X
#  @param  {Number[]} Y
#  @return {Number[][]} The array of vector means
def generateMeans(X, Y):
    numBins = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    Mus = np.zeros((10, getFeatureVectorLength()));
    for i in range(len(Y)):
        numBins[Y[i]] += 1;
        Mus[Y[i]] = np.add(Mus[Y[i]], X[i]);
    for i in range(10):
        Mus[i] = Mus[i] * (1./numBins[i]);
    return Mus;

## Generates the covariance matrix associated with our data
#  @param  {Number[][]} X
#  @param  {Number[]}   Y
#  @param  {Number[][]} Mus
#  @return {Number[][]} The covariance matrix
def generateCovarianceMatrix(X, Y, Mus):
    m = len(Y);
    feature_vec_length = getFeatureVectorLength();
    Cov = np.zeros((feature_vec_length, feature_vec_length));
    for i in range(m):
        Cov = np.add(Cov, np.outer(X[i]-Mus[Y[i]], X[i]-Mus[Y[i]]) * (1./m));
    return Cov;

## Generates a feature vector from a row of the database (Only use this to generate feature vectors)
#  Dependent on multiple helper functions used for specific numerical extraction in the data.
# @param  {String[]} the row from the database
# @return {Number[]} A numerical feature vector from this row, specifically: (UPDATE THIS IF NECESSARY)
#                    [starttime, conditionID, feedbackscore, returnsaccepted, shippingprice,
#                     startprice] --> n = 6
def generateFeatureVector(row):
    return [#extractStartTime(row[START_TIME]),
            #extractConditionID(row[CONDITION_ID]),
            #extractFeedbackScore(row[FEEDBACK_SCORE], row[FEEDBACK_PERC]),
            #extractReturnsAccepted(row[RETURNS]),
            #extractShipping(row[SHIPPING_PRICE]),
            extractStartPrice(row[START_PRICE]),
            #timeStampDifference(row[START_TIME],row[END_TIME]),      #aka auction duration
            #extractGenreID(row[ITEM_SPECS])];
            extractHitCountSlope(row[HIT_COUNTS],row[START_TIME],row[END_TIME])];

## Extracts the start time of the item auction from the start time stamp
# @param  {String} timeString
# @return {Number} A number from 0-23 corresponding to the hour of the start of the auction
def extractStartTime(timeString):
    return float(timeString[11:13]);

## Extracts the condition id of the item. If unknown, returns 0.
#  @param  {String} conditionid
#  @return {Number} condition ID number
def extractConditionID(conditionid):
    if(is_number(conditionid)):
        return float(conditionid);
    else:
        return 0;

## Extracts the feedback score from the seller score and percentage. Returns the multiplication of
#  the two scores.
#  @param  {String} feedbackscore
#  @param  {String} feedbackperc
#  @return {Number} The feedback score
def extractFeedbackScore(feedbackscore, feedbackperc):
    return float(feedbackscore) * float(feedbackperc);

## Extracts information on whether returns are accepted for this particular item
# @param  {String} returnString
# @return {Number} Boolean with 0 meaning returns are not accepted and 1 if they are.
def extractReturnsAccepted(returnString):
    if returnString == 'Returns Accepted':
        return 1;
    else:
        return 0;

## Extracts the shipping price
#  @param  {String} shippingprice
#  @return {Number} The shipping price (0 if blank)
def extractShipping(shippingprice):
    if shippingprice == '':
        return 0;
    else:
        return float(shippingprice);

## Extracts the start price. Returns 0 if unknown.
#  @param  {String} startprice
#  @return {Number} start price
def extractStartPrice(startprice):
    if(is_number(startprice)):
        return float(startprice);
    else:
        return 0;



## Extracts the end price bin ID #
#  @param  {String} endprice
#  @return {Number} The end price bin # e.g. 0-5, 6-10, ..., 45-50
def extractEndPrice(endprice):
    endpriceint = int(float(endprice));
    if endpriceint == 50:
        return 9;
    else:
        return endpriceint / 5;

## Returns the slope of the hitcounts
# @param {String} hitcountstring
# @param {String} starttimestring
# @param {String} endtimestring
# @return {Number} slope of the hitcount line
def extractHitCountSlope(hitcountsstring,starttimestring,endtimestring):
    hitCounts = hitCountParser(hitcountsstring,starttimestring,endtimestring)
    if hitCounts[2][0] >0:
        #Takes only first three data points. Can later be refined to take data points in first 24/36/48 hours.
        #Forces y-intercept to be 0.
        X = np.transpose(np.matrix([hitCounts[i][0] for i in range(3)]))
        Y = np.transpose(np.matrix([hitCounts[i][1] for i in range(3)]))
 
        ## Uncomment following two lines to fit y-intercept term as well
        ## Will have to modify the return as well...
        #ones = np.transpose(np.matrix(np.ones(len(X))))
        #X = np.concatenate((ones,X),1)

        #Return Normal Equation
        cutoff = 2;
        slope = int(np.linalg.inv(np.transpose(X)*X) * (np.transpose(X)*Y));
        if slope<=cutoff: return slope;
        else: return cutoff;


## Returns the slope of the hitcounts
# @param {String} starttimestring
# @param {String} endtimestring
# @return {Number} duration of auction
def timeStampDifference(starttimestring,endtimestring):
    if (starttimestring=='' or endtimestring==''): return -1;
    else:    
        t1 = time.strptime(starttimestring.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        t2 = time.strptime(endtimestring.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        return (time.mktime(t2)-time.mktime(t1))/60/60/24;    


## Extracts the Genre ID
#  @param  {String}  itemspecs
#  @return {Number}  Genre ID, mapped to integers
#  Will want to add more genres here, just built this for testing!
def extractGenreID(itemspecs):
    itemSpecs = itemSpecParser(itemspecs)
    if "Genre" in itemSpecs.keys(): 
        if itemSpecs["Genre"] == ROCK:          return 1
        elif itemSpecs["Genre"] == JAZZ:        return 2
        elif itemSpecs["Genre"] == BLUES:       return 3
        elif itemSpecs["Genre"] == SOUL:        return 4
        elif itemSpecs["Genre"] == CLASSICAL:   return 5
        elif itemSpecs["Genre"] == REGGAE:      return 6
        else:                                   return 0
    else: return -1

## Parses item spec string
#  @param  {String}  itemspecstring
#  @return {Dict}    dictionary of item specs
def itemSpecParser(itemspecstring):
    itemArray = itemspecstring.replace("'","").replace("{","").replace("}","").replace("[","").replace("]","").split(",");
    #itemArray is now like [x1,y1,x2,y2,x3,y3...]

    for i in range(0,len(itemArray)/2):
        #Next block makes itemArray = [[x1,y1],[x2,y2],...]
        itemArray[i] = ",".join([itemArray[i],itemArray[i+1]]).split(",")
        del itemArray[i+1];

    retDict = {};
    for row in itemArray: 
        if len(row)>0: retDict[row[0]] = row[1];

    return retDict;

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


## Returns the argmax of the theta which maximizes dot(theta, x) for some x
#  @param  {Number[]}   featurevec
#  @param  {Number[][]} thetas
#  @return {Number}     The index of the maximizing theta vector
def argmaxlikelihood(featurevec, thetas):
    maxInd = -1;
    maxVal = -float('Inf');
    for i in range(10):
        val = np.dot(featurevec, thetas[i]);
        if val > maxVal:
            maxInd = i;
            maxVal = val;
    return maxInd;

## Retrieves records from DB and filters based on selections:
#  @param  {Bool}     complete
#  @param  {Bool}     sold
#  @param  {Number}   duration (can be 0 meaning all, 3,5,7,10)
#  @param  {String}   genrestring
#  @return {Array[][]} array of items , each row is an item
def getItems(complete=True,sold="all",duration=0,genre=""):
    db = conn.cursor();  
    qString = "SELECT * FROM training_set";
    if genre!="": qString += " WHERE itemspecs LIKE '%" + genre + "%'";
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
            if ((complete == itemComplete) and (sold == itemSold)): 
                items.insert(0,row)
        else: 
            if ((complete == itemComplete) and (sold == itemSold) and (duration==itemDuration)):
                items.insert(0,row)

    return items

def didItemSell(item):
        bids = hitCountParser(item[BID_COUNTS],item[START_TIME],item[END_TIME])
        if bids[len(bids)-1][1] > 0: return True;
        else:                        return False;

## A quick and dirty trick to get the feature vector length. This is
## so we don't have to manually update COV, thetas, means, vector sizes
## when changing feature vector.
def getFeatureVectorLength():
    c = conn.cursor();
    for row in c.execute('SELECT * FROM training_set LIMIT 1'):
        length = len(generateFeatureVector(row))
    return length


## A quick and dirty check to make sure a string is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    runScript();
