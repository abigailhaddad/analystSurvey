# -*- coding: utf-8 -*-
"""
Created on Tue May  4 11:22:01 2021

@author: HaddadAE
"""

import os, pandas as pd
import numpy as np


def genDictAcrossSurveys():
    #this maps the question number in the FEVS survey to the column name in the data survey
    mapDict={"Q11": "My talents are used well in the workplace.",
             "Q18": "My training needs are assessed.",
             "Q12": "I know how my work relates to the agency’s goals and priorities.",
             "Q13": "The work I do is important.",
             "Q5": "I like the kind of work I do.",
             "Q69": "Considering everything, how satisfied are you with your job?",
             "Q70": "Considering everything, how satisfied are you with your pay?"
             }
    return(mapDict)
    
def mapResultsAgree():
    #this maps the responses in the data survey to the numbers
    mapDict={"Strongly Agree": 5,
             "Agree": 4,
             "Neither Agree nor Disagree": 3,
             "Disagree": 2,
             "Strongly Disagree": 1}
    return(mapDict)
    
def mapResultsSatisfied():
    #this maps the responses in the data survey to the numbers
    mapDict={"Very Satisfied": 5,
             "Satisfied": 4,
             "Neither Satisfied nor Dissatisfied": 3,
             "Dissatisfied": 2,
             "Very Dissatisfied": 1}
    return(mapDict)
    
def readFile(directory, fileName):
    #this reads in a csv file
    os.chdir(directory)
    df=pd.read_csv(fileName)
    return(df)
    
def getArmy(df):
    #this subsets FEVS data to just Army
    army=df.loc[df['AGENCY']=="AR"]
    return(army)

def getCleanFEVS(directory, fileName):
    #this pulls in the FEVS data, cleans, subsets, and makes responses numeric where it can
    df=readFile(directory, fileName)
    army= getArmy(df)
    aDict=genDictAcrossSurveys()
    army=army.rename(columns = aDict, inplace = False)
    keepVars=[i for i in army.columns if not i.startswith("Q")]
    army=army[keepVars]
    army=army.replace("X","")
    for i in army.columns:
        try:
            army[i]=pd.to_numeric(army[i])
        except:
            pass
    return(army)


def cleanColName(aString):
    #this cleans column names
    if "[" in aString:
        newString=aString.split("[")[1].split("]")[0]
        return(newString)
    else:
        return(aString)
        
def getSampleData(directory, fileName):
    #this 
    dfSample=readFile(directory, fileName)
    responseAgreeMap=mapResultsAgree()
    responseSatMap=mapResultsSatisfied()
    dfSample.columns=[cleanColName(i) for i in dfSample.columns]
    for i in dfSample.columns:
        sublist=list(dfSample[i].unique())
        if "Agree" in sublist:
            dfSample[i]=dfSample[i].map(responseAgreeMap)
        elif "Satisfied" in sublist:
            dfSample[i]=dfSample[i].map(responseSatMap)
        else:
            #print(i)
            pass
    #dropping my first two test responses
    dfSample=dfSample[2:]
    return(dfSample)

def genMeans(army, dfSample):
    armyMean=army[[i for i in army.columns if len(i)>20]].mean()
    dataMean=dfSample.mean()
    dataMeanOverlap=dataMean.loc[dataMean.index.isin(armyMean.index)]
    meanDF=armyMean.to_frame().merge(dataMeanOverlap.to_frame(), left_index=True, right_index=True)
    meanDF.columns=["Army Overall", "Data Survey"]
    
    selectVar=[i for i in army.columns if len(i)>20]
    dictWeights={}
    for i in selectVar:
        dictWeights[i]=(army[i]*army['POSTWT']).sum()/army['POSTWT'].sum()

    weights=pd.DataFrame.from_dict(dictWeights, orient='index', columns=['Army Weighted'])
    allMeans=meanDF.merge(weights, left_index=True, right_index=True)
    allMeans['Difference']=allMeans['Data Survey']-allMeans['Army Weighted']
    allMeans=allMeans.sort_values("Difference", ascending=False)
    return(allMeans)
    
def genIwant():
    myDict={"I have a version of this that doesn't meet my needs": 1,
       "I don't want access to this": 0,
       "I want access to this but don't have it": 1,
       'I have this and it meets my needs': 0}
    return(myDict)
      
def notMeans(allMeans, dfSample):
    dfSampleClean=dfSample[[i for i in dfSample.columns if i not in allMeans.index]].dropna(how='all', axis=1)
    return(dfSampleClean)
    
def wantingListedTools(dfSample):
    #outputs DF - disatisfied with tool
    wantMap=genIwant()
    wantThings=dfSample[['Python', 'R',
       'Git/version control', 'Tableau/other dashboarding capabilities',
       'A cloud environment', 'Pyspark']]
    for i in wantThings.columns:
        wantThings[i]=wantThings[i].map(wantMap)
    toFrame=wantThings.mean().to_frame()
    toFrame.columns=['Percent']
    toFrame=toFrame.sort_values("Percent", ascending=False)
    return(toFrame)

def toolsToDoMyJob(dfSample):
    #I have the tools I need
    question1='I have the technical tools I need to do my job.'
    question2="If there are other tools you want to use for data-related work but don't have available, please list them below:"
    df=pd.DataFrame(columns=[question1, question2])
    answer1=(dfSample[question1].mean())
    # I am listing a specific additional tool
    answer2=(dfSample[question2].count())/len(dfSample)
    df.loc[0]=answer1, answer2
    return(df)
    
def whatToolsDoYouUse(dfSample):
    #this looks at tool usage by tool
    dictTool={}
    for tool in ['Python', 'R', 'Git/version control', 'Tableau/other dashboarding capabilities',
       'A cloud environment', 'Pyspark']:
        aSeries=np.where(dfSample[tool].str.contains("access"), 0, 1)
        dictTool[tool]=aSeries.mean()
    for tool in ["Power BI", "Collibra", "SQL", "Vantage", "Excel", "Advana", "Cprobe", "AWS", "Oracle", 'MADE', ]:
        aSeries=np.where(dfSample['I use the following technical environments in my work:'].astype(str).str.lower().str.contains(tool.lower()), 1, 0)
        dictTool[tool]=aSeries.mean()
    series=pd.Series(dictTool).sort_values(ascending=False)
    return(series.to_frame())
    
def getLongestResponses(dfSample):
    #gives the longest text responses for those questions
    question1="If there are other tools you want to use for data-related work but don't have available, please list them below:"
    dfSample['ask length']=dfSample[question1].str.len()
    longestAsks= list(dfSample.sort_values('ask length', ascending=False)[question1][0:20])
    question2="Have you been in a situation, either in your current job or in another Army job, where you’ve tried to get a technical tool and had difficulties? If so, please tell us about your experience or experiences below."
    dfSample['try length']=dfSample[question2].str.len()
    longestTries=list(dfSample.sort_values('try length', ascending=False)[question2][0:20])
    df=pd.DataFrame(columns=[question1, question2])
    df[question1]=longestAsks
    df[question2]=longestTries
    return(df)
    
def createToolDistribution(dfSample):
    valueCounts=dfSample['I have the technical tools I need to do my job.'].value_counts(normalize=True).sort_index().to_frame()
    myDict=mapResultsAgree()
    inv_map = {v: k for k, v in myDict.items()}
    valueCounts['response']=valueCounts.index.map(inv_map)
    return(valueCounts)

def getInitialData():
    #reads in both data sets
    directory=r"C:\Users\HaddadAE\Git Repos\data workforce part n\data\FEVS2019_PRDF_CSV"
    fileName="FEVS_2019_PRDF_Revised_2020-04-27.csv"
    army=getCleanFEVS(directory, fileName)
    directory=r'C:\Users\HaddadAE\Git Repos\data workforce part n\data\Army Data Workforce Employee Engagement Survey.csv'
    fileName="Army Data Workforce Employee Engagement Survey.csv"
    dfSample=getSampleData(directory, fileName)
    return(army, dfSample)
    
def getResults(army, dfSample):
    #data workforce vs. overall Army graph numbers
    allMeans=genMeans(army, dfSample)
    toolsMeans=toolsToDoMyJob(dfSample)
    dfOfToolsWanted=wantingListedTools(dfSample)
    dfText=getLongestResponses(dfSample)
    dfToolDistribution=createToolDistribution(dfSample) 
    dfToolsIUse=whatToolsDoYouUse(dfSample)
    return(allMeans[['Data Survey', 'Army Weighted']], toolsMeans, dfOfToolsWanted,dfText, dfToolDistribution, dfToolsIUse)
    
def writeOut(allMeans, toolsMeans, dfOfToolsWanted, dfText, dfToolDistribution, dfToolsIUse):
    # write out results to excel file
    with pd.ExcelWriter('survey results.xlsx') as writer:  
        allMeans.to_excel(writer, sheet_name='Comparing with FEVS')
        toolsMeans.to_excel(writer, sheet_name='Means of Tool Needs',  index=False)
        dfOfToolsWanted.to_excel(writer, sheet_name='Unsatisifed by Tool')
        dfText.to_excel(writer, sheet_name='Long Text Answers')
        dfToolDistribution.to_excel(writer, sheet_name='Tool Distribution', index=False)
        dfToolsIUse.to_excel(writer, sheet_name="Tools I Use")
        
def main():
    #gets data, analyzes data, writes out data
    army, dfSample=getInitialData()
    allMeans, toolsMeans, dfOfToolsWanted, dfText, dfToolDistribution, dfToolsIUse=getResults(army, dfSample)
    writeOut(allMeans, toolsMeans, dfOfToolsWanted, dfText, dfToolDistribution, dfToolsIUse)
    return(army, dfSample)

army, dfSample=main()
