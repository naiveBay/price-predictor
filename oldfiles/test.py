import sys
import sqlite3
import json
import numpy as np

#### Some constants to identify particular elements from the Database ##############################
#np.seterr(all='print');
CAT         = 7;
BIT_COUNT   = 20;
END_PRICE   = 23;
START_PRICE = 22;
ALBUM_ID    = "176985";
CAR_ID      = "10156";
VG_ID       = "139971";
TICKET_ID   = "173634";
conn = sqlite3.connect('record_set.db');
####################################################################################################

## The equivalent of a "main" method
def runScript():
    [Pstartendmat, endPriceCounts] = trainData(); # Train the model on the data
    print Pstartendmat, endPriceCounts;
    # Make predictions... bitch.
    print "How accurate this shit is: ", testData(Pstartendmat, endPriceCounts), "%";
    testEntry(Pstartendmat, endPriceCounts);

## Trains the algorithm on some data
def trainData():
    c = conn.cursor();
    Pstartendmat = np.ones(shape = (10,10));
    endPriceCounts = np.zeros(shape = [10,1]);
    count = 0;
    for row in c.execute('SELECT * FROM training_set'):
        if row[END_PRICE]:
            endprice = float(row[END_PRICE]);
            startprice = float(row[START_PRICE]);
            if endprice <= 50 and startprice <= endprice:
                count += 1;
                if endprice == 50:
                    endprice -= .001;
                if startprice == 50:
                    startprice -= .001;
                endpriceIndex = int(endprice) / 5;
                startpriceIndex = int(startprice) / 5;
                ## Increment probability counts
                Pstartendmat[startpriceIndex][endpriceIndex] += 1;
                endPriceCounts[endpriceIndex] += 1;
    for i in range(0,10):
        for j in range(0,10):
            Pstartendmat[i][j] /= endPriceCounts[i];
    return Pstartendmat, endPriceCounts;

## Tests on the prediction
def testData(Pstartendmat, endPriceCounts):
    c = conn.cursor();
    percentage = 0;
    count = 0;
    for row in c.execute('SELECT * FROM training_set'):
        if row[END_PRICE]:
            endprice = float(row[END_PRICE]);
            startprice = float(row[END_PRICE]);
            if endprice <= 50 and startprice <= endprice:
                count += 1;
                if endprice == 50:
                    endprice -= .001;
                if startprice == 50:
                    startprice -= .001;
                startpriceIndex = int(startprice) / 5;
                endpriceIndex = int(endprice) / 5;
                endPricePredictionIndex = argmaxLikelihood(Pstartendmat[startpriceIndex], endPriceCounts);
                if endpriceIndex == endPricePredictionIndex:
                    percentage += 1;
    return 100*float(percentage) / count;

## Returns the maxmizing argument
def argmaxLikelihood(Prow, endPriceCounts):
    argmaxvalue = 0;
    maxvalue = -float('Inf');
    for i in range(0, len(Prow)):
        val = np.log(endPriceCounts[i]) + np.log(Prow[i]);
        if val > maxvalue:
            maxvalue = val;
            argmaxvalue = i;
    return argmaxvalue;

## Tests an individual entry
def testEntry(Pstartendmat, endPriceCounts):
    startprice = 43.99;
    endprice = 14.51;
    startpriceIndex = int(startprice) / 5;
    endpriceIndex = int(endprice) / 5;
    endPricePredictionIndex = argmaxLikelihood(Pstartendmat[startpriceIndex], endPriceCounts);
    if endPricePredictionIndex == endpriceIndex:
        print "FUCK YEAH", endPricePredictionIndex;
    else:
        print "FAIL", endPricePredictionIndex, endpriceIndex, startpriceIndex;

## A quick and dirty check to make sure a string is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
if __name__ == "__main__":
    runScript();
