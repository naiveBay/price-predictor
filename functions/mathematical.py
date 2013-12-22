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
    x = float(x)
    count = int(math.ceil(y - x)/jump)
    return [x + n*jump for n in range(count)]
