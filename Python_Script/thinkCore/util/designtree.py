import sys

import matplotlib.pyplot as plt
import pandas
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier


def process_builder(predict: list, app_settings):
    """"Prediction List to Compute 'iec2lvl20', 'iec2lvl30', 'iec2lvl35', 'iec2lvl40',	'iec3lvl20',	'iec3lvl30', 'iec3lvl35', 'iec3lvl40',	'ilayer count'"""
    df = pandas.read_csv(app_settings.get('TruthTable'))

    features = ['iec2lvl20', 'iec2lvl30', 'iec2lvl35', 'iec2lvl40', 'iec3lvl20', 'iec3lvl30', 'iec3lvl35', 'iec3lvl40', 'ilayer count']
    results = ['oEC2_Place', 'oEC3_Place', 'oEC2_Fasten', 'oEC3_Fasten', 'oEC2_SmallRouting', 'oEC3_SmallRouting',  'oEC2_Routing', 'oEC3_Routing']
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
