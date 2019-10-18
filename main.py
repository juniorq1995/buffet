# Here shall be written the code that builds my portfolio
# input data and calculate the ROI from different companies and average all the companies to represent the "market"
# look at both the open and the close
# company symbol,ROI per year starting from recent, going back 15 years at the most
# company symbol, ROI past 15 years, ROI past 10 years, ROI past 5 years
import os
import pandas as pd
import numpy as np

temp = pd.read_csv('data/Stocks/a.us.txt',sep=',')
roi = []
buyIn = temp['Open'][0]
currYear = temp['Date'][0].split('-')[0]
for index, row in temp.iterrows():
    if(row[0].split('-')[0] != currYear):
        roiCalc = (temp.iloc[index - 1, 1] - buyIn) / buyIn
        roi.append([currYear,roiCalc])
        currYear = row[0].split('-')[0]
        buyIn = row[1]
print(roi)
# for filename in os.listdir(directory):
#     if filename.endswith(".txt"):
#         with open(filename) as f:
#             for line in f:
