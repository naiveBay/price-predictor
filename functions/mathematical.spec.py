import mathematical as m
EPS = .001;

def runTests():
    runThresholdTest();
    runSigmoidTest();
    runSquaredNormTest();

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

if __name__ == "__main__":
    runTests();