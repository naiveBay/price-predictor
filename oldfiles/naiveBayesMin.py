import sys
import sqlite3
import json
import math
import numpy as np
import time
import operator
import naiveBayesMCupdateDN as nb
from softmax  import getItems, didItemSell, hitCountParser, timeStampDifference,filterItems
from random import random
from copy import deepcopy

####################################################################################################
## Multi-class binary classification Naive Bayes statistical wrapper
####################################################################################################

## The equivalent of a "main" method
def runScript():
    plotProbs();

def plotProbs():
    binSize = 2;
    maxPrice = 100;
    dataSplit = 0.70;

    allItems                = getItems(complete=True,sold=True,genre=ROCK);   #remove genre parameter to search all genres
    allItems                = filterItems(allItems);

    [trainItems,testItems]  = splitItemSet(allItems,dataSplit);

    bins = generateBinArray(binSize,maxPrice);
    [actualFinalPrice,actualFinalPriceBinned] = getFinalPrices(testItems,bins);

    ##Only have to make these onece
    orderedWordList = generateOrderedWordList(allItems);
    [testMatrix,testCategory]   = generateMatrixData(orderedWordList,generateItemTitleList(testItems,orderedWordList));

    predictedFinalPrices = [-1]*len(testItems);
    psold = [];
    punsold = [];
    predict = [];
    for priceCutOff in bins:
        print "Price cut off: ", priceCutOff
        #Have to calculate these at every priceCutOff increment
        [phi_k_unsold,phi_k_sold,p_y0,p_y1]   = trainOnData(trainItems,orderedWordList,priceCutOff);
        testCategory                = generateTrainCategory(testItems,priceCutOff)            #actual category for testItems
        [testingSetPredictions,prob_sell,prob_wontSell]         = makePredictions(testMatrix,phi_k_sold,phi_k_unsold,p_y0,p_y1);    #predicted category for testItems [0,1]

        predict.append(testingSetPredictions[2]);
        psold.append(prob_sell[2]);
        punsold.append(prob_wontSell[2]);

        predictedFinalPrices = updatePredictedFinalPrice(testItems,predictedFinalPrices,testingSetPredictions,priceCutOff,binSize,bins);

    for i in range(len(predictedFinalPrices)):
        if predictedFinalPrices[i] == -1: predictedFinalPrices[i] = bins[-1];
        
    for i in range(len(predictedFinalPrices)):
        print i,testItems[i][0],testItems[i][START_PRICE],actualFinalPrice[i],getBinOf(bins,float(testItems[i][START_PRICE])), actualFinalPriceBinned[i],predictedFinalPrices[i],"\t\t",testItems[i][TITLE]

    print "Classification error on testing set is: ", classificationError(predictedFinalPrices,actualFinalPriceBinned);


if __name__ == "__main__":
    runScript();
