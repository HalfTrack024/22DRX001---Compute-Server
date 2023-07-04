import sys
import matplotlib
#matplotlib.use('Agg')

import pandas
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt

import dataBaseConnect as dbc



def processBuilder(predict : list):
    """"Prediction List to Compute 'iec2lvl20', 'iec2lvl30',	'iec2lvl40',	'iec3lvl20',	'iec3lvl30',	'iec3lvl40',	'ilayer count'"""
    df = pandas.read_csv(r'Python_Script\dataExtract_EHX\util\truthtable.csv')

    features = ['iec2lvl20', 'iec2lvl30',	'iec2lvl40',	'iec3lvl20',	'iec3lvl30',	'iec3lvl40',	'ilayer count']
    results = ['oEC2_Place',	'oEC3_Place',	'oEC2_Fasten',	'oEC3_Fasten',	'oEC2_Routing',	'oEC3_Routing']
    X = df[features]
    Y = df[results]
    
    dtree = DecisionTreeClassifier()
    dtree = dtree.fit(X,Y)

    tree.plot_tree(dtree, feature_names=features)

    #Two  lines to make our compiler able to draw:
    plt.savefig(sys.stdout.buffer)
    plt.savefig('tree', dpi = 600)
    sys.stdout.flush()
    result = dtree.predict([predict])
    
    dictResult = dict(zip(results, result[0]))


    return dictResult


def printProcess(results, result):
    print(chr(27) + "[2J")
    i = 0
    for item in results:
        print(item + "   : " + str(result[0][i]))
        i += 1
