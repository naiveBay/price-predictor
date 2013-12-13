import sys
import sqlite3
import json
import math
import softmax as sm
import numpy as np
import kmeans as km
import csv
import dataStuff as ds
from random import randint
from copy import deepcopy

#### Some constants to identify particular elements from the Database ##############################
CAT             = 7;  # Category ID column
BIT_COUNT       = 20; # Bit Count column
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

TRAINING_PERC   = 0.7; # Percentage of data set to train for cross validation
NUM_CV          = 10; # Number of times to run cross validation
ALBUM_ID    = "176985";
CAR_ID      = "10156";
VG_ID       = "139971";
TICKET_ID   = "173634";
conn = sqlite3.connect('record_set (2).db'); # Connect to the records database
####################################################################################################

## The equivalent of a "main" method
def runScript():
    [X, Y] = sm.generateDataMatrices(conn);
    X = zeroOutMeans(X);
    X = unitStd(X);
    Cov = generateCovMatrix(X);
    [U,S,V] = np.linalg.svd(Cov);
    print Cov;
    with open('data.csv', 'w') as csvfile:
        writer = csv.writer(csvfile);
        [writer.writerow(r) for r in X];
    file = open('dataLabels.csv', 'w');
    for elem in Y:
        file.write("%s\n" % elem);

## Generates the covariance matrix
#  @param  {Number[][]} X
#  @return {Number[][]} The covariance matrix
def generateCovMatrix(X):
    m = len(X);
    n = len(X[0]);
    Cov = np.zeros((n, n));
    for i in range(m):
        Cov += np.outer(X[i], X[i])/m;
    return Cov;
## Zeroes out the Mean
#  @param  {Number[][]} X
#  @return {Number[][]} The zeroed out array
def zeroOutMeans(X):
    m = len(X);
    n = len(X[0]);
    Xnew = deepcopy(X);
    mu = calculateMean(X);
    for i in range(m):
        Xnew[i] = Xnew[i] - mu;
    return Xnew;

## Standardizes the variance to 1
#  @param  {Number[][]} X
#  @return {Number[][]} The standardized array
def unitStd(X):
    m = len(X);
    n = len(X[0]);
    Xnew = deepcopy(X);
    stddev = root(calculateZeroMeanVariance(X));
    for i in range(m):
        Xnew[i] /= stddev;
    return Xnew;

## Calculate the mean value of an array of vectors
#  @param  {Number[][]} X
#  @return {Number[]}  The mean vector
def calculateMean(X):
    m = len(X);
    n = len(X[0]);
    mu = np.zeros(n);
    for i in range(m):
        mu += X[i];
    return mu/m;

## Calculate the variance vector of an array of vectors (NOTE THIS ASSUMES THE MEAN HAS BEEN ZEROED
#  OUT!!)
#  @param  {Number[][]} X
#  @return {Number[]}   The variance vector
def calculateZeroMeanVariance(X):
    m = len(X);
    n = len(X[0]);
    sigma = np.zeros(n);
    for i in range(m):
        sigma += square(X[i]);
    return sigma/m;

## Calculate the variance vector of an array of vectors
#  @param  {Number[][]} X
#  @return {Number[]}   The variance vector
def calculateVariance(X):
    m = len(X);
    n = len(X[0]);
    mu = calculateMean(X);
    sigma = np.zeros(n);
    for i in range(m):
        sigma += square(X[i]-mu);
    return sigma/m; 

## Helper function that returns the elements of a list squared
#  @param  {Number[]} x
#  @return {Number[]} The squared elements list
def square(x):
    n = len(x);
    sqx = deepcopy(x);
    for i in range(n):
        sqx[i] = x[i]*x[i];
    return sqx;

## Helper function that returns the square roots of the elements of a list
#  @param  {Number[]} x
#  @return {Number[]} The square rooted elements list
def root(x):
    n = len(x);
    sqx = deepcopy(x);
    for i in range(n):
        sqx[i] = math.sqrt(x[i]);
    return sqx;

if __name__ == "__main__":
    runScript();