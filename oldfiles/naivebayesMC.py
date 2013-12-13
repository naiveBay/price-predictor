import sys
import sqlite3
import json
import math
import numpy as np
import time
import operator
from softmax  import getItems, didItemSell, hitCountParser, timeStampDifference,filterItems
from random import random
from copy import deepcopy

####################################################################################################
## Implementation of binomial Naive Bayes, modeled after spam classifier problem from homework.

conn = sqlite3.connect('record_set.db'); # Connect to the records database

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

## The equivalent of a "main" method
def runScript():
    binSizes = [1, 2, 3, 4, 5, 8, 12, 15, 20];
    avgerror = [];
    binSizes = [2];
    SAMPLE_SIZE = 1;
    for i in range(len(binSizes)):
        err = 0;
        for j in range(SAMPLE_SIZE):
            print binSizes[i], j;
            err += crossValidate(binSizes[i])/SAMPLE_SIZE;
        avgerror.append(err);
    print avgerror;
def crossValidate(binSize):
    priceCutOff = 15;
    maxPrice = 200;
    dataSplit = 0.70

    #print "Loading items... "
    allItems                = getItems(complete=True,sold=True);   #remove genre parameter to search all genres
    allItems                = filterItems(allItems);
    [trainItems,testItems]  = splitItemSet(allItems,dataSplit);

    actualFinalPrice = [];
    for row in testItems:
        if didItemSell(row): actualFinalPrice.append(float(row[END_PRICE]));
        else:                actualFinalPrice.append(0);
    
    bins = generateBinArray(binSize,maxPrice);
    actualFinalPriceBinned = binnedFinalPrice(bins,actualFinalPrice);

    ##Only have to make these once
    orderedWordList = generateOrderedWordList(allItems);
    [testMatrix,testCategory]   = generateMatrixData(orderedWordList,generateItemTitleList(testItems,orderedWordList));

    predictedFinalPrice = [-1]*len(testItems);
    for priceCutOff in bins:
        #print "Price cut off: ", priceCutOff
        #Have to calculate these at every priceCutOff increment
        [phi_k_unsold,phi_k_sold]   = trainOnData(trainItems,orderedWordList,priceCutOff);
        testCategory                = generateTrainCategory(testItems,priceCutOff)            #actual category for testItems
        testingSetPredictions       = makePredictions(testMatrix,phi_k_sold,phi_k_unsold);    #predicted category for testItems

        for i in range(len(testItems)):
            if testingSetPredictions[i]==0 and predictedFinalPrice[i]==-1:
                if priceCutOff-binSize>float(testItems[i][END_PRICE]):
                    predictedFinalPrice[i] = priceCutOff-binSize;
                elif priceCutOff-binSize<=float(testItems[i][END_PRICE]):
                    predictedFinalPrice[i] = getBinOf(bins,float(testItems[i][END_PRICE]));
                    if predictedFinalPrice[i]<0: predictedFinalPrice[i]=0;


                #if testItems[i][END_PRICE]>=priceCutOff: predictedFinalPrice[i] = priceCutOff;
                #else: predictedFinalPrice[i] = testItems[i][END_PRICE]; 
    file = open('predictedactualprices.csv', 'w');
    for i in range(len(predictedFinalPrice)):
        if predictedFinalPrice[i] == -1: predictedFinalPrice[i] = bins[-1];
    for item in range(len(predictedFinalPrice)):
        file.write(str(predictedFinalPrice[item])+ ", "+ str(actualFinalPrice[item])+ "\n");
    file.close();
    return classificationError(predictedFinalPrice, actualFinalPriceBinned);
  

    #for i in range(len(predictedFinalPrice)):
        #print testItems[i][START_PRICE],actualFinalPrice[i],getBinOf(bins,float(testItems[i][START_PRICE])), actualFinalPriceBinned[i],predictedFinalPrice[i]



    #print "Making predictions ... "
    #testingSetPredictions       = makePredictions(testMatrix,phi_k_sold,phi_k_unsold);

    #print "Classification error on testing set is: ", classificationError(predictedFinalPrice,actualFinalPriceBinned);

    #print    
    #printStats(phi_k_sold,phi_k_unsold,orderedWordList)

def getBinOf(bins,price):
    bin = -1;
    for i in range(len(bins)):
        if bins[i] >= price and bin == -1: 
            if i==0:
                bin = 0
            else: 
                bin = bins[i-1];

    if bin == -1: bin = bins[len(bins)-1];
    return bin


def generateBinArray(bin,maxval):
    arr = [];
    for i in range(int(maxval/bin)):
        arr.append(bin*i);
    return arr

def binnedFinalPrice(bins,actualFinalPrice):
    binnedFinalPrice = [-1]*len(actualFinalPrice);
    for i_item in range(len(actualFinalPrice)):
        for i in range(len(bins)-1):
            if actualFinalPrice[i_item] >= bins[i] and actualFinalPrice[i_item]<bins[i+1]:
                binnedFinalPrice[i_item] = bins[i];

        if binnedFinalPrice[i_item] == -1: binnedFinalPrice[i_item] = bins[-1];

    return binnedFinalPrice

def trainOnData(trainItems,orderedWordList,priceCutOff):
    itemTitleList               = generateItemTitleList(trainItems,orderedWordList);
    [trainMatrix,trainCategory] = generateMatrixData(orderedWordList,itemTitleList);
    trainCategory               = generateTrainCategory(trainItems,priceCutOff); 
    return generatePhiK(trainMatrix,trainCategory);

def splitItemSet(items,threshold):
    trainItems = [];
    testItems = [];

    for i in range(len(items)):
        if random() < threshold: trainItems.append(items[i]);
        else:                    testItems.append(items[i]);  


    #print "Items in training set: ",len(trainItems);
    #print "Items in testing set: ",len(testItems);

    return trainItems,testItems

## Cycles through all items and generates an ordered list of all words found.
#  @param  {list[][]}  items  
#  @return {list[]}    sorted list of all words found  
def generateOrderedWordList(items):  
    #print "Generating ordered word list ... "

    ordered_words = {};

    removeWords = ["the","a","an","in","these","those","for","this","that"];

    ## Generate a full list of all words and their occurances
    for row in items:
        for word in row[TITLE].split(" "):
            if len(word)>2:
                if word.lower() in ordered_words.keys(): ordered_words[word.lower()] += 1;
                else: ordered_words[word.lower()] = 1;

    ## Now delete all words that have only one occurance or are in the removeWords array
    newWords = {}
    for k in ordered_words.keys():
        if ordered_words[k]>2 and k not in removeWords: 
            newWords[k] = ordered_words[k]

#    return sorted(ordered_words.keys());

    #print "Length of word list: ",len(newWords);
    return sorted(newWords.keys());
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

    #print "sold %: ", float(soldItemCnt)/float((soldItemCnt+unsoldItemCnt))*100

    return phi_k_unsold, phi_k_sold

## Make predictions on test data set
# param  {np.array[][]}  testMatrix
# param  {list[]}        phi_k_sold
# param  {list[]}        phi_k_unsold
# return {list[]}        prediction
def makePredictions(testMatrix,phi_k_sold,phi_k_unsold):
    prob_sell = [0]*testMatrix.shape[0];
    prob_wontSell = [0]*testMatrix.shape[0];
    predict = [0]*testMatrix.shape[0];

    for item in range(testMatrix.shape[0]):
        for word in range(testMatrix.shape[1]):
            if testMatrix[item][word] != 0:
                prob_sell[item] += np.log(phi_k_sold[word])*testMatrix[item][word];
                prob_wontSell[item] += np.log(phi_k_unsold[word])*testMatrix[item][word];


        if prob_sell[item] > prob_wontSell[item]: predict[item] = 1;
        else:                                     predict[item] = 0;

    return predict;

## Classification error on the data set
# param  {list[]}  predictions
# param  {list[]}  actual
# return {float}   classification error
def classificationError(predictions,actual):
    error = 0;
    for item in range(len(predictions)):
        if (predictions[item] != actual[item]): error +=1

    return float(error) / float(len(predictions));

if __name__ == "__main__":
    runScript();
