import sys,os
import sqlite3
import json
import math
import numpy as np
import time
import operator
from random import random
from copy import deepcopy

sys.path.insert(0, '%s/../functions/' % os.path.dirname(os.path.abspath(__file__)))
from dataReading import *
from mathematical import classificationError,frange

####################################################################################################
## Implementation of binomial Naive Bayes, modeled after spam classifier problem from homework.

conn = sqlite3.connect('../databases/record_set.db'); # Connect to the records database
db = conn.cursor();

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

''' Top Genres:
    Not Given  ( 4371 ) 
    Rock  ( 3341 ) 
    R&amp;B &amp; Soul  ( 1115 ) 
    Classical  ( 938 ) 
    Pop  ( 723 ) 
    Jazz  ( 696 ) 
    Country  ( 383 ) 
    Latin  ( 271 ) '''

####################################################################################################

## The equivalent of a "main" method
def runScript():
    toSellOrNotToSell();
    #raw_title();

def raw_title():

    print "Loading items... "
    allItems = getItems(db,complete=True,genre=ROCK);   #remove genre parameter to search all genres

    trainItems = [];
    testItems = [];

    thresh = 0.70;
    #allItems = allItems[0:1000];
    for i in range(len(allItems)):
        if random() < thresh: trainItems.append(allItems[i]);
        else:                 testItems.append(allItems[i]);   

    print "Items in training set: ",len(trainItems);
    print "Items in testing set: ",len(testItems);

    orderedWordList = generateOrderedWordList(allItems);

    print "Training on data set ..."
    itemTitleList = generateItemTitleList(trainItems,orderedWordList);
    [trainMatrix,trainCategory] = generateMatrixData(orderedWordList,itemTitleList);
    [phi_k_unsold,phi_k_sold,p_y0,p_y1] = generatePhiK(trainMatrix,trainCategory);

    printStats(phi_k_sold,phi_k_unsold,orderedWordList)

    title="";
    while title != "n":
        title = raw_input("title: ");

        print "Preparing test data ... "
        itemTitleList = rawTitleToItemTitleList(title,orderedWordList);

        [testMatrix,testCategory] = generateMatrixData(orderedWordList,itemTitleList);

        print "Making predictions ... "
        #trainingSetPredictions = makePredictions(trainMatrix,phi_k_sold,phi_k_unsold);
        [testingSetPredictions,prob_sell,prob_wontSell] = makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1,unknown=0);
        for i in range(len(prob_sell)):
            if testingSetPredictions[i] == -1:
                print prob_sell[i],prob_wontSell[i]

        print prob_sell
        print prob_wontSell

        #print "Classification error on training set is: ", classificationError(trainingSetPredictions,trainCategory);
        print testingSetPredictions
        print "Classification error on testing set is: ", classificationError(testingSetPredictions,testCategory);


def nb_crossValidate():
    print "Loading items... "
    allItems = getItems(db,complete=True,genre=ROCK);   #remove genre parameter to search all genres

    trainItems = [];
    testItems = [];

    thresh = 0.70;
    #allItems = allItems[0:1000];
    for i in range(len(allItems)):
        if random() < thresh: trainItems.append(allItems[i]);
        else:                 testItems.append(allItems[i]);   

    print "Items in training set: ",len(trainItems);
    print "Items in testing set: ",len(testItems);

    orderedWordList = generateOrderedWordList(allItems);

    print "Training on data set ..."
    itemTitleList = generateItemTitleList(trainItems,orderedWordList);
    [trainMatrix,trainCategory] = generateMatrixData(orderedWordList,itemTitleList);
    [phi_k_unsold,phi_k_sold,p_y0,p_y1] = generatePhiK(trainMatrix,trainCategory);

#    for i in range(len(phi_k_sold)):
#        print phi_k_sold[i]*1000-phi_k_unsold[i]*1000
    printStats(phi_k_sold,phi_k_unsold,orderedWordList)

    print "Preparing test data ... "
    itemTitleList = generateItemTitleList(testItems,orderedWordList);
    [testMatrix,testCategory] = generateMatrixData(orderedWordList,itemTitleList);

    print "Making predictions ... "
    #trainingSetPredictions = makePredictions(trainMatrix,phi_k_sold,phi_k_unsold);
    [testingSetPredictions,prob_sell,prob_wontSell] = makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1,unknown=0);
    for i in range(len(prob_sell)):
        if testingSetPredictions[i] == -1:
            print prob_sell[i],prob_wontSell[i]

    print prob_sell
    print prob_wontSell

    #print "Classification error on training set is: ", classificationError(trainingSetPredictions,trainCategory);
    print testingSetPredictions
    print "Classification error on testing set is: ", classificationError(testingSetPredictions,testCategory);


def errorByFeature():
    binSize = 4;
    maxPrice = 50;
    dataSplit = 0.70;

    print "Loading items... "
    allItems                = getItems(db,filteritems=True,complete=True,sold=True,genre=COUNTRY);   
    [trainItems,testItems]  = splitItemSet(allItems,dataSplit);

    bins = generateBinArray(binSize,maxPrice);
    [actualFinalPrice,actualFinalPriceBinned] = getFinalPrices(testItems,bins);

    ##Only have to make these onece
    orderedWordList = generateOrderedWordList(allItems,lengthcutoff=3,frequencycutoff=2);  

    idnum="";
    while idnum!="n":
        idnum = raw_input("idnum: ")
    #    item = 

        itemTitleList = rawTitleToItemTitleList(title)
        [testMatrix,testCategory]   = generateMatrixData(orderedWordList,generateItemTitleList(testItems,orderedWordList));

        predictedFinalPrices = [-1]*len(testItems);
        psold = [];
        punsold = [];
        predict = [];
        for priceCutOff in bins:
            print "Price cut off: ", priceCutOff
            #Have to calculate these at every priceCutOff increment
            [phi_k_unsold,phi_k_sold,p_y0,p_y1]   = trainOnData(trainItems,orderedWordList,priceCutOff);
            #[p_y0,p_y1]  = softenPrior(p_y0,p_y1,1);

            testCategory                = generateTrainCategory(testItems,priceCutOff)            #actual category for testItems
            [testingSetPredictions,prob_sell,prob_wontSell]         = makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1);    #predicted category for testItems [0,1]

            #for i in range(len(prob_sell)):
            #    print prob_sell[i],prob_wontSell[i],testingSetPredictions[i] 

            predict.append(testingSetPredictions[2]);
            psold.append(prob_sell[2]);
            punsold.append(prob_wontSell[2]);

            predictedFinalPrices = updatePredictedFinalPrice(testItems,predictedFinalPrices,testingSetPredictions,priceCutOff,binSize,bins);

            #print predictedFinalPrices;

        for i in range(len(predictedFinalPrices)):
            if predictedFinalPrices[i] == -1: predictedFinalPrices[i] = bins[-1];
            
        for i in range(len(predictedFinalPrices)):
            print i,testItems[i][0],testItems[i][START_PRICE],actualFinalPrice[i],getBinOf(bins,float(testItems[i][START_PRICE])), actualFinalPriceBinned[i],predictedFinalPrices[i],"\t\t",testItems[i][TITLE]
            
        print "Classification error on testing set is: ", classificationError(predictedFinalPrices,actualFinalPriceBinned);

def priorSoftening():
    binSize = 1;
    maxPrice = 50;
    dataSplit = 0.03;

    print "Loading items... "
    allItems                = getItems(db,filteritems=True,complete=True,sold=True,genre=JAZZ);   
    [trainItems,testItems]  = splitItemSet(allItems,dataSplit);

    bins = generateBinArray(binSize,maxPrice);
    [actualFinalPrice,actualFinalPriceBinned] = getFinalPrices(testItems,bins);

    ##Only have to make these onece
    orderedWordList = generateOrderedWordList(allItems,lengthcutoff=3,frequencycutoff=1);  

    [testMatrix,testCategory]   = generateMatrixData(orderedWordList,generateItemTitleList(testItems,orderedWordList));


    priorSoft = [];
    for soft in frange(1,1.0001,0.1):
        predictedFinalPrices = [-1]*len(testItems);
        psold = [];
        punsold = [];
        predict = [];
        for priceCutOff in bins:
            print "Price cut off: ", priceCutOff
            #Have to calculate these at every priceCutOff increment
            [phi_k_unsold,phi_k_sold,p_y0,p_y1]   = trainOnData(trainItems,orderedWordList,priceCutOff);
            [p_y0,p_y1]  = softenPrior(p_y0,p_y1,soft);
            print "p_y0,p_y1: ",p_y0,p_y1

            testCategory                = generateTrainCategory(testItems,priceCutOff)            #actual category for testItems
            [testingSetPredictions,prob_sell,prob_wontSell]         = makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1);    #predicted category for testItems [0,1]


            #for i in range(len(prob_sell)):
            #    print prob_sell[i],prob_wontSell[i],testingSetPredictions[i] 

            predict.append(testingSetPredictions[2]);
            psold.append(prob_sell[2]);
            punsold.append(prob_wontSell[2]);

            predictedFinalPrices = updatePredictedFinalPrice(testItems,predictedFinalPrices,testingSetPredictions,priceCutOff,binSize,bins);

            #print predictedFinalPrices;

        for i in range(len(predictedFinalPrices)):
            if predictedFinalPrices[i] == -1: predictedFinalPrices[i] = bins[-1];
            
        for i in range(len(predictedFinalPrices)):
            print i,testItems[i][0],testItems[i][START_PRICE],actualFinalPrice[i],getBinOf(bins,float(testItems[i][START_PRICE])), actualFinalPriceBinned[i],predictedFinalPrices[i],"\t\t",testItems[i][TITLE]
            
        classError = classificationError(predictedFinalPrices,actualFinalPriceBinned);
        priorSoft.append(classError);
        print "Classification error on testing set is: ", classError;
        print priorSoft






def toSellOrNotToSell():
    ## That is the question. 
    
    print "Loading items... "
    allItems = getItems(db,complete=True,genre=ROCK);   #remove genre parameter to search all genres
    allItems = filterItems(allItems);

    trainItems = [];
    testItems = [];

    thresh = 0.70;
    #allItems = allItems[0:1000];
    for i in range(len(allItems)):
        if random() < thresh: trainItems.append(allItems[i]);
        else:                 testItems.append(allItems[i]);   

    print "Items in training set: ",len(trainItems);
    print "Items in testing set: ",len(testItems);

    orderedWordList = generateOrderedWordList(allItems,frequencycutoff = 4);

    print "Training on data set ..."
    [phi_k_unsold,phi_k_sold,p_y0,p_y1] = trainOnData(trainItems,orderedWordList,0)

    printTopWords(phi_k_sold,phi_k_unsold,orderedWordList)

    print "Preparing test data ... "
    itemTitleList = generateItemTitleList(testItems,orderedWordList);
    [testMatrix,testCategory] = generateMatrixData(orderedWordList,itemTitleList);

    print "Making predictions ... "
    [testingSetPredictions,prob_sell,prob_wontSell] = makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1,uniformPrior=False);
    print "Classification error on testing set is: ", classificationError(testingSetPredictions,testCategory);


def printTopWords(phi_k_sold,phi_k_unsold,orderedWordList):
    rating = [];
    for i in range(len(phi_k_sold)):
        rating.append(np.log(phi_k_sold[i] / phi_k_unsold[i]) ); 

    ratingsSorted =  [orderedWordList[i[0]] for i in sorted(enumerate(rating), key=lambda x:x[1])]
    reverseratingsSorted  =   [orderedWordList[i[0]] for i in sorted(enumerate(rating), key=lambda x:x[1])]
    reverseratingsSorted.reverse();

    print
    print "Highest rated words: ", ratingsSorted[0:30]
    print "Lowest rated: ",reverseratingsSorted[0:30]





def softenPrior(p_y0,p_y1,soften):
    switch=False;
    if p_y0>p_y1:
        temp = p_y1;
        p_y1 = p_y0;
        p_y0 = temp;
        switch = True;

    p_y1 = p_y1*soften;
    p_y0 = 1-p_y1;

    if switch:
        temp = p_y1;
        p_y1 = p_y0;
        p_y0 = temp;

    return p_y0,p_y1;

## Takes array of items and array of bins. Returns actual and binned final prices.
#  @param  {list[][]} testItems
#  @param  {list[]}   predictedFinalPrice  
#  @param  {list[]}   testingSetPredictions  
#  @param  {float}    priceCutOff 
#  @param  {float}    binSize  
#  @param  {list[]}   bins  
#  @return {list[]}   predictedFinalPrice  
def updatePredictedFinalPrice(testItems,predictedFinalPrice,testingSetPredictions,priceCutOff,binSize,bins):
    for i in range(len(testItems)):
        if testingSetPredictions[i]==0 and predictedFinalPrice[i]==-1:
            if priceCutOff-binSize>float(testItems[i][END_PRICE]):
                predictedFinalPrice[i] = priceCutOff-binSize;
            elif priceCutOff-binSize<=float(testItems[i][END_PRICE]):
                predictedFinalPrice[i] = getBinOf(bins,float(testItems[i][END_PRICE]));
                if predictedFinalPrice[i]<0: predictedFinalPrice[i]=0;
    return predictedFinalPrice

## Takes array of items and array of bins. Returns actual and binned final prices.
#  @param  {list[][]} items
#  @param  {list[]}   bins  
#  @return {list[]}   actualFinalPrice  
#  @return {list[]}   actualFinalPriceBinned
def getFinalPrices(items,bins,default=0):
    actualFinalPrice = [];
    for row in items:
        if didItemSell(row): actualFinalPrice.append(float(row[END_PRICE]));
        else:                actualFinalPrice.append(default);
    actualFinalPriceBinned = binnedFinalPrice(bins,actualFinalPrice);

    return actualFinalPrice,actualFinalPriceBinned

## Takes bin array and an float price, returns bin value corresponding to price.
## Eg. getBinOf([0,5,10,15,20],12.22) = 10
#  @param  {list[]}  bins  
#  @param  {float}   price  
#  @return {float}   bin 
def getBinOf(bins,price):
    bin = -1;
    for i in range(len(bins)):
        if bins[i] > price and bin == -1: 
            if i==0:    bin = 0
            else:       bin = bins[i-1];

    if bin == -1: bin = bins[len(bins)-1];
    return bin

## Takes bin size and max value and generates an array of bin values.
#  @param  {int}      binSize 
#  @param  {int}      maxVal 
#  @return {list[]}   arr 
def generateBinArray(binSize,maxVal):
    arr = [];
    for i in range(int(maxVal/binSize)):
        arr.append(binSize*i);
    return arr

## Takes bin array and an array of actual final prices. Returns array of final price bins.
#  @param  {list[]}  bins  
#  @param  {list[]}  actualFinalPrice  
#  @return {list[]}  binnedFinalPrice 
def binnedFinalPrice(bins,actualFinalPrice):
    binnedFinalPrice = [-1]*len(actualFinalPrice);
    for i_item in range(len(actualFinalPrice)):
        for i in range(len(bins)-1):
            if actualFinalPrice[i_item] >= bins[i] and actualFinalPrice[i_item]<bins[i+1]:
                binnedFinalPrice[i_item] = bins[i];

        if binnedFinalPrice[i_item] == -1: binnedFinalPrice[i_item] = bins[-1];
    return binnedFinalPrice

## Takes items to train on, the complete word list, and cut off price for training.
## Returns output of generatePhiK.
#  @param  {list[][]}  trainItems  
#  @param  {list[]}    orderedWordList  
#  @param  {float}     priceCutOff  
#  @return {[list[],list[]]}  generatePhiK 
def trainOnData(trainItems,orderedWordList,priceCutOff):
    itemTitleList               = generateItemTitleList(trainItems,orderedWordList);
    [trainMatrix,trainCategory] = generateMatrixData(orderedWordList,itemTitleList);
    trainCategory               = generateTrainCategory(trainItems,priceCutOff); 
    return generatePhiK(trainMatrix,trainCategory);

## Takes set of items and a threshhold (percent to split)
#  @param  {list[][]}  items  
#  @param  {float}     threshold  
#  @return {[list[],list[]]}  generatePhiK 
def splitItemSet(items,threshold):
    trainItems = [];
    testItems = [];

    for i in range(len(items)):
        if random() < threshold: trainItems.append(items[i]);
        else:                    testItems.append(items[i]);  

    print "Items in training set: ",len(trainItems);
    print "Items in testing set: ",len(testItems);

    return trainItems,testItems

## Cycles through all items and generates an ordered list of all words found.
#  @param  {list[][]}  items  
#  @return {list[]}    sorted list of all words found  
def generateOrderedWordList(items,lengthcutoff=2,frequencycutoff=2):  
    ## !!!!! BE CAREFUL. if frequencycutoff too large, chance that prediction remains -1 and guesses max bin
    print "Generating ordered word list ... "

    ordered_words = {};

    removeWords = ["the","a","an","in","these","those","for","this","that","from","&amp;","&apos;&apos;","there","and"];

    ## Generate a full list of all words and their occurances
    for row in items:
        for word in row[TITLE].split(" "):
            if len(word)>=lengthcutoff:
                if word.lower() in ordered_words.keys(): ordered_words[word.lower()] += 1;
                else: ordered_words[word.lower()] = 1;

    ## Now delete all words that have only one occurance or are in the removeWords array
    newWords = {}
    for k in ordered_words.keys():
        if ordered_words[k]>=frequencycutoff and k not in removeWords: 
            newWords[k] = ordered_words[k]

    print "Length of word list: ",len(newWords);
    return sorted(newWords.keys());



## Each row is an item. First entry in each row is True/False for sold or not. 
## Remaining entries are the indices where of the each word in the title, as
## indexed by orderedWordList.
# param  {list[][]}   items
# param  {list[]}     orderedWordList
# return {list[][]}   item_title_words
def generateItemTitleList(items,orderedWordList):
    item_title_words = [];
    for row in items:
        words = [didItemSell(row)];

        for word in row[TITLE].split(" "):
            if len(word)>2: 
                if orderedWordList.count(word.lower())!=0:
                    words.append(orderedWordList.index(word.lower()));
        
        item_title_words.append(words);

    return item_title_words;

def rawTitleToItemTitleList(title,orderedWordList):
    item_title_words = []
    words = [-1]
    for word in title.split(" "):
        if len(word)>2:
            if orderedWordList.count(word.lower())!=0:
                words.append(orderedWordList.index(word.lower()));
    item_title_words.append(words);
    return item_title_words;

## Matrix data has: 
##  -column for each word in orderedwordslist
##  -row for each item
##  -Each entry is number of times given word occurs in that item's title
# param  {list[]}       orderedWordList
# param  {list[][]}     ItemTitleList
# return {np.array[][]} trainMatrix
# return {np.array[]}   trainCategory 
def generateMatrixData(orderedWordList,itemTitleList):
    trainMatrix = np.zeros((len(itemTitleList),len(orderedWordList)));
    trainCategory = np.zeros(len(itemTitleList));

    for item in range(len(itemTitleList)):
        for word in itemTitleList[item][1:-1]:
            trainMatrix[item][word] += 1;

        if itemTitleList[item][0] == True:    trainCategory[item] = 1;
        else:                                 trainCategory[item] = 0;

    return trainMatrix,trainCategory;

def generateTrainCategory(items,priceCutOff):
    arr = []
    for row in items:
        if float(row[END_PRICE]) >= priceCutOff and didItemSell(row):  arr.append(1);
        else:                                                          arr.append(0);

    return arr

## Percent of occurances of kth word in all words from sold or unsold items.
# param  {np.array[][]}  trainMatrix
# param  {np.array[]}    trainCategory
# return {list[]}        phi_k_unsold
# return {list[]}        phi_k_sold
def generatePhiK(trainMatrix,trainCategory): 

    phi_k_unsold = [0]*trainMatrix.shape[1]
    phi_k_sold = [0]*trainMatrix.shape[1]

    soldWordCnt = 0;        unsoldWordCnt = 0;
    soldItemCnt = 0;        unsoldItemCnt = 0; 

    for i in range(trainMatrix.shape[0]):
        if trainCategory[i]==1:          
            soldWordCnt += np.sum(trainMatrix[i]);
            soldItemCnt += 1;
        else:                     
            unsoldWordCnt += np.sum(trainMatrix[i]);
            unsoldItemCnt += 1;

    for word in range(trainMatrix.shape[1]):
        numeratorSold = 0;    numeratorUnsold = 0;

        for item in range(trainMatrix.shape[0]):
            if trainCategory[item]==1: numeratorSold += trainMatrix[item][word];
            else:                      numeratorUnsold += trainMatrix[item][word];

        #with laplace smoothing
        phi_k_unsold[word] = float(numeratorUnsold+1) / float(unsoldWordCnt+len(phi_k_unsold));
        phi_k_sold[word] = float(numeratorSold+1) / float(soldWordCnt+len(phi_k_sold));

        #without laplace smoothing
        #phi_k_unsold[word] = float(numeratorUnsold) / float(unsoldWordCnt);
        #phi_k_sold[word] = float(numeratorSold) / float(soldWordCnt);

    print "sold %: ", float(soldItemCnt)/float((soldItemCnt+unsoldItemCnt))*100

    p_y0 = float(unsoldItemCnt) / (unsoldItemCnt+soldItemCnt);
    p_y1 = float(soldItemCnt) / (unsoldItemCnt+soldItemCnt);

    return phi_k_unsold, phi_k_sold,p_y0,p_y1

## Make predictions on test data set
# param  {np.array[][]}  testMatrix
# param  {list[]}        phi_k_sold
# param  {list[]}        phi_k_unsold
# return {list[]}        prediction
def makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1,uniformPrior=True,unknown=-1):
    prob_sell = [0]*testMatrix.shape[0];
    prob_wontSell = [0]*testMatrix.shape[0];
    predict = [0]*testMatrix.shape[0];

    for item in range(testMatrix.shape[0]):
        for word in range(testMatrix.shape[1]):
            if testMatrix[item][word] != 0:
                prob_sell[item] += np.log(phi_k_sold[word])*testMatrix[item][word];
                prob_wontSell[item] += np.log(phi_k_unsold[word])*testMatrix[item][word];


    for item in range(testMatrix.shape[0]):
        if uniformPrior:
            pass;
        else:
            prob_sell[item] += np.log(p_y1);
            prob_wontSell[item] += np.log(p_y0);

        if prob_sell[item] > prob_wontSell[item]: predict[item] = 1;
        elif prob_sell[item] < prob_wontSell[item]: predict[item] = 0
        else:                                     predict[item] = unknown;


    return [predict,prob_sell,prob_wontSell];


def printStats(phi_k_sold,phi_k_unsold,orderedWordList):
    sortedWordsSold = [orderedWordList[i[0]] for i in sorted(enumerate(phi_k_sold), key=lambda x:x[1])]
    sortedWordsUnSold = [orderedWordList[i[0]] for i in sorted(enumerate(phi_k_unsold), key=lambda x:x[1])]

    sortedWordTopSold = []
    sortedWordTopUnSold = []
    wordsOnBoth = []
    i = len(sortedWordsSold)-1

    length = 30

    while len(sortedWordTopSold) < length and len(sortedWordTopUnSold) < length and i>=0:
        if len(sortedWordTopSold)< length:
            if sortedWordsSold[i] not in sortedWordTopUnSold: 
                sortedWordTopSold.append(sortedWordsSold[i])
            else: 
                sortedWordTopUnSold.remove(sortedWordsSold[i])
                wordsOnBoth.append(sortedWordsSold[i])

        if len(sortedWordTopUnSold) < length:
            if sortedWordsUnSold[i] not in sortedWordTopSold: 
                sortedWordTopUnSold.append(sortedWordsUnSold[i])
            else: 
                sortedWordTopSold.remove(sortedWordsUnSold[i])
                wordsOnBoth.append(sortedWordsUnSold[i])

        i=i-1;


if __name__ == "__main__":
    runScript();
