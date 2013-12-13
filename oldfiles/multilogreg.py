import sys
import sqlite3
import json
import math
import numpy as np
import softmax as sm
import kmeans as km
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

NUM_CLASSIFIERS = 10;   # Number of binary classifiers to use
SPACING         = 5;    # Spacing (in dollars) between classifiers
ALPHA           = 1e-12; # Learning Rate
THRESHOLD_RATE  = .01;  # Threshold Rate for Gradient ascent
TRAINING_PERC   = 0.7;  # Percentage of data set to train for cross validation
NUM_CV          = 10;   # Number of times to run cross validation
MAX_ITERS       = 100;  # Max iterations in gradient ascent
ALBUM_ID    = "176985";
CAR_ID      = "10156";
VG_ID       = "139971";
TICKET_ID   = "173634";
conn = sqlite3.connect('record_set.db'); # Connect to the records database
####################################################################################################
## Functional Description:
# This script will run a multi-class logistic regression on the data. In other words, it will run
# 'l' logistic regressions to test whether an item's final price will be above or below a certain
# price, rather than seeing whether the price will land in a particular bin. Therefore, it will use
# logistic regression to solve for the 'l' classifiers by training on a percentage of the data, and
# then it will test on the rest.

## The equivalent of a "main" method
def runScript():
    crossValidate(conn, TRAINING_PERC);

## Uses cross-validation for training and testing
#  @param  {SQLLite3Connection} conn
#  @param  {Number}             p (percentage of data to hold for training)
#  @return {Number}             The percentage of correctly predicted data.
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
    Xtrain = addOnes(Xtrain);
    Xtest  = addOnes(Xtest);
    # Train on Xtrain
    thetas = trainOnData(Xtrain, Ytrain, NUM_CLASSIFIERS, SPACING);
    print thetas;
    # Test on Xtest
    return test(Xtest, Ytest, thetas);

## Generates the feature vector matrix and associated bin labels ($5 bins)
#  @param  {SQLLite3Connection} conn
#  @return {[Number[][], Number[]]} The feature vector matrix and bin labels i.e. [X, Y]
def generateDataMatrices(conn):
    c = conn.cursor();
    X = []; # The data matrix which will contain feature vectors of our training set
    Y = []; # The end price vector which will contain the end prices (in the $5 bins).
    for row in c.execute('SELECT * FROM training_set'):
        if(row[END_PRICE]):
            if(float(row[END_PRICE]) <= 50):
                Y.append(row[END_PRICE]);
                X.append(sm.generateFeatureVector(row));
    return [X, Y];

## Trains on a set of data and returns the theta vectors
#  @param  {Number[][]} X
#  @param  {Number[]}   Y
#  @param  {Number}     L
#  @param  {Number}     spacing
#  @return {Number[][]} The theta vectors
def trainOnData(X, Y, L, spacing):
    m = len(X);
    n = len(X[0]);
    thetas = np.zeros((L, n));
    for i in range(L):
        thresh = (i+1)*spacing;
        thetas[i] = calculateOptimalTheta(X, Y, thresh);
    return thetas;

## Test the multi-class regression
#  @param {Number[][]} X
#  @param {Number[]}   Y
#  @param {Number[][]} thetas
#  @return {Number} The percentage of correctly identified points.
def test(X, Y, thetas):
    print 'done';

## Calculates the optimal theta using a gradient ascent method
#  @param  {Number[][]} X
#  @param  {Number[]}   Y
#  @param  {Number}     thresh
def calculateOptimalTheta(X, Y, thresh):
    m = len(X);
    n = len(X[0]);
    print thresh;
    theta = np.random.rand(n);
    t = 0;
    convergence_condition = False;
    while(not(convergence_condition) and t < MAX_ITERS):
        t += 1;
        delTheta = delta_Theta(X, Y, thresh, theta);
        theta += ALPHA*delTheta;
        if(squaredNorm(ALPHA*delTheta)<(THRESHOLD_RATE**2)):
            convergence_condition = True;
        print t, squaredNorm(ALPHA*delTheta), theta;
    print t, squaredNorm(delTheta), delTheta;
    return theta;

## Adds a 1 before each element in the feature vectors (for logistic regression)
#  @param  {Number[][]} X
#  @return {Number[][]} The modified set of feature vectors
def addOnes(X):
    m = len(X);
    onesvector = np.atleast_2d(np.ones(m)).T;
    return np.hstack((onesvector, X));

## Calculates the delta_Theta vector for the Gradient Ascent
#  @param  {Number[][]} X
#  @param  {Number[]}   Y
#  @param  {Number}     thresh
#  @param  {Number[]}   theta
#  @return {Number[]}   The delta_y vector
def delta_Theta(X, Y, thresh, theta):
    m = len(X);
    n = len(X[0]);
    delTheta = np.zeros(n);
    for i in range(m):
        for j in range(n):
            z = np.dot(theta, X[i]);
            ylabel = fthresh(float(Y[i]), thresh);
            delTheta[j] += (ylabel - sigmoid(z)) * X[i][j];
    return delTheta;

## Thresholding function. Gives 1 if input is above the threshold, and
#  0 if it is below.
#  @param  {Number} y
#  @param  {Number} threshold
#  @return {Number} 0 or 1
def fthresh(y, threshold):
    if(y >= threshold):
        return 1;
    else:
        return 0;

## Calculates the logistic function on a number
#  @param  {Number} x
#  @return {Number} The result of the logistic function
def sigmoid(x):
    # For precision purposes:
    if(x < -700):
        return 0;
    elif(x > 700):
        return 1;
    return 1/(1+math.exp(-x));

## Calculates the squared norm of a vector
#  @param  {Number[]} v
#  @return {Number}
def squaredNorm(v):
    sqn = 0;
    for i in v:
        sqn += i**2;
    return sqn;

if __name__ == "__main__":
    runScript();