import sys

import pandas
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt


def process_builder(predict: list):
    """"Prediction List to Compute 'iec2lvl20', 'iec2lvl30',	'iec2lvl40',	'iec3lvl20',	'iec3lvl30',	'iec3lvl40',	'ilayer count'"""
    df = pandas.read_csv(
        r'C:\Users\Andrew Murray\source\Copia\22DRX001\Python_Script\dataExtract_EHX\util\truthtable.csv')

    features = ['iec2lvl20', 'iec2lvl30', 'iec2lvl40', 'iec3lvl20', 'iec3lvl30', 'iec3lvl40', 'ilayer count']
    results = ['oEC2_Place', 'oEC3_Place', 'oEC2_Fasten', 'oEC3_Fasten', 'oEC2_Routing', 'oEC3_Routing']
    X = df[features]
    Y = df[results]

    d_tree = DecisionTreeClassifier()
    d_tree = d_tree.fit(X, Y)

    tree.plot_tree(d_tree, feature_names=features)

    # Two  lines to make our compiler able to draw:
    plt.savefig(sys.stdout.buffer)
    plt.savefig('tree', dpi=600)
    sys.stdout.flush()
    result = d_tree.predict([predict])

    dictResult = dict(zip(results, result[0]))

    return dictResult


def printProcess(results, result):
    print(chr(27) + "[2J")
    i = 0
    for item in results:
        print(item + "   : " + str(result[0][i]))
        i += 1
