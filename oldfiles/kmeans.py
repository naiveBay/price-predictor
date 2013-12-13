import sys
import sqlite3
import json
import math
import numpy as np
import dataStuff as ds
import softmax as sm
import random as rand
from copy import deepcopy

## This script will use k-means clustering to analyze the record set data. Runs k-means for various
#  k and averages over the distances to try and find a stable output for the algorithm.

#### Some constants for use in the algorithm ######################################################
MAX_ITERS   = 100;
EPSILON     = 0.01;
Nk          = 20;   # Number of times to run k-means for a particular k.
dispStatus  = True; # Turn this to false to turn off the convergence display
conn = sqlite3.connect('record_set.db'); # Connect to the records database
####################################################################################################

## The equivalent of a "main" method
def runScript():
    [X, Y] = sm.generateDataMatrices(conn);
    kerrors = [];
    for k in range(1, 11):
        toterror = float('Inf');
        for n in range(Nk):
            Mus = kmeans(X, k);
            avdist = calculateAverageDistance(X, Mus) / float(Nk);
            if avdist < toterror:
                toterror = avdist;
        kerrors.append(toterror);
    print kerrors;

## Runs k-means clustering until convergence or max iterations are exceeded.
#  @param  {Number[][]} X
#  @param  {Number} k
#  @return {Number[][]} The array of mean vectors (i.e. the centroids)
def kmeans(X, k):
    m = len(X);
    n = len(X[0]);
    Mus = np.zeros((k, n));
    # Assuming k < n, assign distinct random values to the centroids.
    randInds = [];
    for i in range(k):
        flag = False;
        while not(flag):
            num = rand.randint(0, m-1);
            if not(num in randInds):
                randInds.append(num);
                flag = True;

    for i in range(k):
        Mus[i] = X[randInds[i]];

    convCond = False;
    t = 0;
    while(not(convCond) and t < MAX_ITERS):
        t += 1;
        Musn = np.zeros((k, n));
        c = np.zeros((m, 1));
        numC = np.zeros((k,1));
        for i in range(m):
            dists = [];
            for j in range(k):
                dists.append(squaredNorm(X[i], Mus[j]));
            c[i] = argmin(dists);
            numC[int(c[i])] += 1;
        for i in range(m):
            Musn[int(c[i])] += X[i] * (1. / numC[int(c[i])]);
        # Check convergence
        if squaredNorm(np.reshape(Mus,(k*n, 1)), np.reshape(Musn, (k*n, 1))) < EPSILON*EPSILON:
            convCond = True;
        Mus = deepcopy(Musn);
    if dispStatus:
        print 'k =',k, ' t =',t, 'Convergence Met?', convCond;
    return Mus;

## Calculates the distance for each point to its nearest centroid
#  @param {Number[][]} X
#  @param {Number[][]} Mus
#  @return The average distance to the nearest centroid
def calculateAverageDistance(X, Mus):
    m = len(X);
    k = len(Mus);
    totaldist = 0.;
    for i in range(m):
        for j in range(k):
            minDist = float('Inf');
            dist = squaredNorm(X[i], Mus[j]);
            if dist < minDist:
                minDist = dist;
        totaldist += minDist;
    return totaldist / m;

## Returns the squared Euclidean distance between two vectors of equal length
#  @param {Number[]} v1
#  @param {Number[]} v2
#  @return The squared 2-norm distance between the two vectors
def squaredNorm(v1, v2):
    dist = 0;
    for i in range(len(v1)):
        dist += (v1[i] - v2[i])*(v1[i] - v2[i]);
    return dist;

## Returns the index of the minimum element in a vector. Useful for argmin
#  @param  {Number[]} v
#  @return {Number} The index of the minimum element
def argmin(v):
    minInd = -1;
    minVal = float('Inf');
    for i in range(len(v)):
        val = v[i];
        if val < minVal:
            minVal = val;
            minInd = i;
    return minInd;

## Returns the index of the maximum element in a vector. Useful for argmax
#  @param  {Number[]} v
#  @return {Number} The index of the maximum element
def argmax(v):
    maxInd = -1;
    maxVal = -float('Inf');
    for i in range(len(v)):
        val = v[i];
        if val > maxVal:
            maxVal = val;
            maxInd = i;
    return maxInd;

if __name__ == "__main__":
    runScript();
