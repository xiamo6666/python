# encoding: utf-8
import pandas as pd

if __name__ == '__main__':
    test = pd.read_excel('/Volumes/Mark/www/1.xlsx')
    for x in test.values:
        print("(null,{},'flightData'),".format(str(x[1])[:-2]))
