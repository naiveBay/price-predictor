import sys
import sqlite3
import json
import math
import numpy as np
import time
import operator
from softmax_V5 import getItems, didItemSell, hitCountParser
from random import random
from copy import deepcopy
from softmax_V5 import timeStampDifference, hitCountParser

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
    crossValidate();

def crossValidate():
    print "Loading items... "
    allItems = getItems(complete=True,genre=ROCK);   #remove genre parameter to search all genres

    trainItems = [];
    testItems = [];

    thresh = 0.85;
    #allItems = allItems[0:1000];
    for i in range(len(allItems)):
        if random() < thresh: trainItems.append(allItems[i]);
        else:                 testItems.append(allItems[i]);   

    print "Items in training set: ",len(trainItems);
    print "Items in testing set: ",len(testItems);

    print "Generating ordered word list ... "
    orderedWordList = generateOrderedWordList(allItems);
    print "Length of word list: ",len(orderedWordList);

    print "Training on data set ..."
    itemTitleList = generateItemTitleList(trainItems,orderedWordList);
    [trainMatrix,trainCategory] = generateMatrixData(orderedWordList,itemTitleList);
    [phi_k_unsold,phi_k_sold] = generatePhiK(trainMatrix,trainCategory);

    print "Preparing test data ... "
    itemTitleList = generateItemTitleList(testItems,orderedWordList);
    [testMatrix,testCategory] = generateMatrixData(orderedWordList,itemTitleList);

    print "Making predictions ... "
    #trainingSetPredictions = makePredictions(trainMatrix,phi_k_sold,phi_k_unsold);
    testingSetPredictions = makePredictions(testMatrix,phi_k_sold,phi_k_unsold);

    #print "Classification error on training set is: ", classificationError(trainingSetPredictions,trainCategory);
    print "Classification error on testing set is: ", classificationError(testingSetPredictions,testCategory);

## Cycles through all items and generates an ordered list of all words found.
#  @param  {list[][]}  items  
#  @return {list[]}    sorted list of all words found  
def generateOrderedWordList(items):  
    ordered_words = {};
    item_title_words = [];

    for row in items:
        for word in row[TITLE].split(" "):
            if len(word)>2:
                if word.lower() in ordered_words.keys(): ordered_words[word.lower()] += 1;
                else: ordered_words[word.lower()] = 1;

    return sorted(ordered_words.keys());
 
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
            if len(word)>2: words.append(orderedWordList.index(word.lower()));
        
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

        phi_k_unsold[word] = float(numeratorUnsold) / float(unsoldWordCnt);
        phi_k_sold[word] = float(numeratorSold) / float(soldWordCnt);

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
