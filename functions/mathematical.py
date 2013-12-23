import sys
import sqlite3
import json
import math

## Contains a set of useful mathematical functions.

## Thresholding function. Returns 1 if input is equal to or above the threshold, and 0 if it is
#  below.
#  @param  {Number} y
#  @param  {Number} threshold
#  @return {Number} 0 or 1
def threshold(y, threshold):
    if(y >= threshold):
        return 1;
    else:
        return 0;

## Calculates the logistic function on a number. To avoid an error, returns 0 or 1 for very large
#  negative or positive numbers respectively.
#  @param  {Number} x
#  @return {Number} The result of the logistic function
def sigmoid(x):
    # For precision purposes:
    if(x < -700):
        return 0;
    elif(x > 700):
        return 1;
    return 1/(1+math.exp(-x));

## Calculates the Euclidean squared norm of a vector
#  @param  {Number[]} v
#  @return {Number}
def squaredNorm(v):
    sqn = 0;
    for x in v:
        sqn += x**2;
    return sqn;

## Classification error between two lists.
#  @param  {list[]}  predictions
#  @param  {list[]}  actual
#  @return {float}   classification error
def classificationError(predictions,actual):
    error = 0;
    for item in range(len(predictions)):
        if (predictions[item] != actual[item]): error +=1

    return float(error) / float(len(predictions));

## Similar to python's range, but returns a float range.
#  @param  {float}  x
#  @param  {float}  y
#  @param  {float}  jump
#  @return {list[]} list [x,x+jump,x+2*jump,...,] up to final value < y
def frange(x, y, jump):
    ## Susceptible to small roundoff errors. See mathematical.spec.py.
    x = float(x)
    count = int(math.ceil(y - x)/jump)
    return [x + n*jump for n in range(count)]

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


## Takes bin array and an array prices. Returns array of final price bins.
#  @param  {list[]}  bins  
#  @param  {list[]}  prices  
#  @return {list[]}  binnedPrices
def binListOfPrices(bins,prices):
    binnedPrices = [-1]*len(prices);
    for i_item in range(len(prices)):
        for i in range(len(bins)-1):
            if prices[i_item] >= bins[i] and prices[i_item]<bins[i+1]:
                binnedPrices[i_item] = bins[i];

        if binnedPrices[i_item] == -1: binnedPrices[i_item] = bins[-1];
    return binnedPrices