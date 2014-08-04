# -*- coding: utf-8 -*-
import sys
sys.path.append("C:\\Program Files (x86)\\IronPython 2.7\\Lib")
sys.path.append("C:\\Python27\\Lib")
import os
import csv
import requests
import time
import datetime
import sqlalchemy
import tempfile

os.chdir(tempfile.gettempdir())

print(tempfile.gettempdir())
os.pause()

def writeCSV( content ):
    '''Saves CSV content to folder on desktop'''
    ## File to save output to
    if not os.path.exists("Incident"):
        os.makedirs("Incident")
    date = time.strftime("%Y%m%d")
    path = os.getcwd() + "\\Incident\\Incidents.csv"
    fh = open(path,"w")
    fh.write(ResolveDoubleNewLine(content))
    fh.close()

def ResolveDoubleNewLine( content ):
    '''Resolves the double new line in CSV files'''
    resolver = content.replace("\r\n","\n")
    return resolver

def mwatchcsrf( content ):
    '''Gets mwatchcsrf (unique token) from sdp.mymwatch.com login page'''
    start = "<input type=\"hidden\" value=\""
    end = "\""
    startIndex = content.find(start) + len(start)
    endIndex  = content.find(end,startIndex)
    return content[startIndex:endIndex]

def Authenticate():
    '''Authenticated to sdp.mymwatch.com'''
    username = "b.marks@fordfound.org"
    password = "ZaQwSx12"
    postUrl = "https://sdp.mymwatch.com/Portal/index.php?r=User/authentication/Login&goto=https%3A%2F%2Fsdp.mymwatch.com%2FPortal%2Findex.php"
    session = requests.Session()

    ## To get the token
    response = session.get(postUrl)

    postData = {
        "Login[username]" : username,
        "Login[password]" : password,
        "mwatchcsrf" : mwatchcsrf(response.content)
        }

    response = session.post(postUrl,postData)


    ## Returns session
    return session

def GetIncidents( session ):
    '''Gets Incidents_*.csv file and saves it'''
    incidentUrl = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/ExportToCSV&ticketType=1&action=IncidentFilter&fStatus=groupincidents&fStatusname=Group+Incidents&undefined&&searchTxt="
    response = session.get(incidentUrl)
    writeCSV(response.content)

def GetFiles():
    '''Gets all files with Incidents*.csv and Advanced...*.csv and finds the most recent one (going by filename). Returns incident,advanced'''
    path = os.getcwd() + "\\Incident\\"
    incident = path + "Incidents.csv"
    advanced = path + "AdvancedSearchTicket.csv"
    return incident,advanced

def GetDescriptions( advanced ):
    '''Gets dictionary of TicketID to Description'''
    descriptions = {}
    with open(advanced,"rb") as advancedCSV:
        reader = csv.reader(advancedCSV, delimiter=',', quotechar='"')
        for row in reader:
            if row[0] not in descriptions:
                descriptions[row[0]] = row[1]
    advancedCSV.close()
    return descriptions

def UpdateDescription(ticketID, session ):
    '''Updates descriptions.csv file from web'''
    description = LookupDescription( ticketID, session )
    description = description.replace("\r\n"," ").replace("Problem:"," ").replace("Problem Description:"," ")
    description = description.strip()
    writeHandle = open("Incident\\descriptions.csv","a")
    writeHandle.write('"%s","%s"\n' % (ticketID, description))
    writeHandle.close()
    return description    

def GetContents( incident ):
    '''Gets List of Rows of the file'''
    fhr = open(incident,"r")
    file_read = fhr.read()
    rows = file_read.split("\n")
    fhr.close()
    return rows

def GenerateLine( rowsList, descriptions, rowNum, session, ccls ):
    '''Writes one line into the destination file'''
    col = rowsList[rowNum].split('","')
    if( len(col) < 40 ):
        return ""

    condition = True
    
    if col[0] != "":
        col[0] = col[0].strip('"') ## fixes leading quote
        col[-1] = col[-1].strip('"') ## fixes trailing quote

        description = ""
        duration = ""
        
        try:
            description = descriptions[col[0]]
        except KeyError:
            descriptions[col[0]] = UpdateDescription( col[0], session )
            description = descriptions[col[0]]

        try:
            test = ccls[col[0]]
        except:
            ccls[col[0]] = "Unknown"
            
        columns = [col[0].strip('"'),
                   ccls[col[0]],
                   description, ## Description
                   col[9], ## Issue Type
                   col[22], ## Owner
                   col[12], ## Priority
                   col[3], ## Status
                   col[25], ## Requestor
                   duration, ## Time to complete
                   col[5], ## Created
                   col[31], ## Resolved
                   col[33], ## Closed
                   ]
        
        oneRow = '~'.join(columns)
        return oneRow + '"\n'
    return ""

def GenerateHeader( rowsList ):
    '''Generates CSV header'''
    col = rowsList[0].split('","')
    col[0] = col[0].strip('"') ## fixes leading quote
    col[0] = "Ticket ID"
    col[-1] = col[-1].strip('"') ## fixes trailing quote
    columns = [
            col[0].strip('"'), ## Ticket
            "CCL#",
            "Description", ## Description
            col[9], ## Issue Type
            col[22], ## Owner
            col[12], ## Priority
            col[3], ## Status
            col[25], ## Requestor
            "Completion Time", ## Duration
            col[5], ## Created 
            col[31], ## Resolved
            col[33] ## Closed
            ]
    oneRow = "~".join(columns)
    return oneRow + "\n"

def GenerateFile( session ):
    '''Generates result file with all the bells and whistles'''

    writeHandle = open(os.getcwd() + "\\Incident\\bsd_report.csv","w")
        
    incident,advanced = GetFiles()
    MakeNewFiles()
    descriptionFile = "Incident\\descriptions.csv"
    descriptions = GetDescriptions( descriptionFile )
    rows = GetContents( incident )
    writeHandle.write( GenerateHeader( rows ))

    ccls = GetCCLs()

    for i in range(1, len(rows) - 1):
        sys.stdout.write("\r%s%%" % (round(float(i*100)/float(len(rows) - 2),2)))
        writeHandle.write(GenerateLine( rows, descriptions, i, session, ccls ))
        sys.stdout.flush()
    writeHandle.close()
    sys.stdout.write("\n")

def LookupDescription( ticketID, session ):
    '''Looks up description of ticket'''
    url = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/view&id=%s" % (ticketID)
    response = session.get(url)
    content = response.content

    delimeters = [
        '<td  class="bg-col1" width="17.9%" >Description</td>'
        ]

    description = ""
    for i in range(len(delimeters)):
        delimeter = delimeters[i]
        start = content.find(delimeter) + len(delimeter)
        end = content.find("</tr>",start)
        description = content[start:end]
        if not ( description == "" or start == (-1 + len(delimeter))):
            break
    while description.find("&nbsp;") != -1:
        description = description.replace("&nbsp;"," ")
    while description.find("<") != -1:
        subset = description[description.find("<"):description.find(">") + 1]
        description = description.replace(subset," ")
    return description

def MakeNewFiles():
    if not os.path.exists("Incident\\descriptions.csv"):
        f = open("Incident\\descriptions.csv","w")
        f.write('"TicketID","Description"\n')
        f.close()

def GetCCLs():
    '''Gets list of Tickets to CCL#'''
    server = "ffnyc0355"
    database = "FordNet_Content"
    query = "SELECT FLOAT2 AS MWATCHID, tp_ID AS CCLnR FROM AllUserData WHERE TP_LISTID = '5E36CE12-E5BD-45F6-8260-244BE2008D7F' AND tp_IsCurrent =1 AND FLOAT2 IS NOT NULL ORDER BY TP_ID DESC"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    ccl = {}
    for row in engine.execute(query):
        ccl[str(int(row[0]))] = str(int(row[1]))

    return ccl


def main():
    '''Main func'''
    sys.stdout.write("Authenticating\n")
    session = Authenticate()

    sys.stdout.write("\nDownloading\n")
    GetIncidents(session)

    sys.stdout.write("\nGenerating File\n")
    GenerateFile( session )

if __name__ == "__main__":
    ## const
    main()
