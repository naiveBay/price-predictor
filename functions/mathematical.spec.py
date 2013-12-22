import mathematical as m
EPS = .001;

def runTests():
    runThresholdTest();
    runSigmoidTest();
    runSquaredNormTest();
    runClassificationErrorTest();
    ##runFrangeTest();   ## See notes in function

def runThresholdTest():
    thresh = 5;
    fail = False;

    if(m.threshold(1 , thresh) != 0):
        fail = True;
    if(m.threshold(7, thresh) != 1):
        fail = True;
    if(m.threshold(5, thresh) != 1):
        fail = True;

    if(fail):
        print "Threshold Function has failed!";

def runSigmoidTest():
    fail = False;

    if(m.sigmoid(0) != 0.5):
        fail = True;
    if(m.sigmoid(750) != 1):
        fail = True;
    if(m.sigmoid(-701) != 0):
        fail = True;
    if(m.sigmoid(3) - 0.9526 > EPS):
        fail = True;
    if(m.sigmoid(-1) - 0.2689 > EPS):
        fail = True;
    if(fail):
        print "Sigmoid Function has failed!";

def runSquaredNormTest():
    v1 = [3, 2, 5, -1];
    v2 = [2, 1, 9, 2];
    fail = False;

    if(m.squaredNorm(v1) != 39):
        fail = True;
    if(m.squaredNorm(v2) != 90):
        fail = True;

    if(fail):
        print "Squared Norm Function has failed!";

def runClassificationErrorTest():
    fail = False;
    p2 = [0,1,0];
    a2 = [0,1,1];

    if (m.classificationError([0],[0]) != 0):       fail = True;
    if (m.classificationError([0],[1]) != 1):       fail = True;
    if (m.classificationError([0],[-1]) != 1):      fail = True;

    if (m.classificationError([0,0],[0,0]) != 0):   fail = True;
    if (m.classificationError([0,0],[0,1]) != 0.5): fail = True;
    if (m.classificationError([0,0],[1,1]) != 1):   fail = True;

    if (fail):
        print "Classification Error Function has failed!";

def runFrangeTest():
    ## Python frange is a funny thing.
    ## See http://code.activestate.com/recipes/66472/
    ## For now, we will live with small floating point errors.

    fail = False

    if (m.frange(0,1,0.2) != (0,0.2,0.4,0.8) ):    fail = True

    if (fail):
        print "Float range function has failed!"

if __name__ == "__main__":
    runTests();