import requests
import csv
import sqlalchemy
import pyodbc

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
##    write(ResolveLinks(response.content)) ## Outputs HTML file


    ## Returns session
    return session

def ResolveDoubleNewLine( content ):
    '''Resolves the double new line in CSV files'''
    resolver = content.replace("\r\n","\n")
    return resolver

def WriteCSV( content ):
    '''Saves CSV content to desktop'''
    ## File to save output to
##    path = "C:\\Users\\b.marks\\Desktop\\FordGBSIncidents.csv"
    path = "Incident\\FordGBSIncidents.csv"
    fh = open(path,"w")
    fh.write(ResolveDoubleNewLine(content))
    fh.close()

def GetRecentIncidents( session ):
    '''Gets FordGBS incidents'''
    incidentUrl = "https://sdp.mymwatch.com/Portal/index.php?r=servicedelivery/ticket/ExportToCSV&ticketType=1&action=IncidentFilter&fStatus=groupincidents&fStatusname=Group+Incidents&undefined&&searchTxt="
    response = session.get(incidentUrl)
    WriteCSV(response.content)

def PushTfs( session ):
    '''Inputs new info into tfs'''
    tickets = GetTickets()
##    path = "C:\\Users\\b.marks\\Desktop\\FordGBSIncidents.csv"
    path = "Incident\\FordGBSIncidents.csv"
    with open(path, "rb") as CSV:
    reader = csv.reader(CSV, delimiter = ',', quotechar = '"' )
    for row in reader:
        if row[0] not in tickets:
            AddTicket( row, LookupDescription(row[0], session) )

def GetTickets():
    '''Gets all ticketID from TFS'''
    server = "ffazu0317\\gbs2uat2012"
    database = "FF_Grants_TSP1"
    query = "select * from subject"
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

    tickets = []
    for row in engine.execute(query):
        tickets.append(row[0])
    return tickets

def AddTicket( ticketInfo, description ):
    '''Adds a ticket to the TFS db'''
    server = "ffazu0317\\gbs2uat2012"
    database = "FF_Grants_TSP1"
    query = "INSERT INTO subject VALUES( %s, %s )" % (ticketInfo, description)
    engine = sqlalchemy.create_engine("mssql+pyodbc://%s/%s" % (server, database))

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
    while description.find("&nbsp") != -1:
        description = description.replace("&nbsp"," ")
    while description.find("<") != -1:
        subset = description[description.find("<"):description.find(">") + 1]
        description = description.replace(subset," ")
    description = description.replace("\r\n"," ").replace("Problem:"," ").replace("Problem Description:"," ")
    description = description.strip()
    return description

def Verify():
    '''Verifies all tickets have been updated'''
##    fh = open("C:\\users\\b.marks\\desktop\\tfsLog.txt","a")
    fh = open("Incident\\tfsLog.txt","a")
    tfsTickets = GetTickets()
##    path = "C:\\Users\\b.marks\\Desktop\\FordGBSIncidents.csv"
    path = "Incident\\FordGBSIncidents.csv"
    with open(path, "rb") as CSV:
    reader = csv.reader(CSV, delimiter = ',', quotechar = '"' )
    for row in reader:
        if row[0] not in tfsTickets:
            message = "Error adding " + row[0] + " to TFS"
            print(message)
            fh.write(message)
    fh.close()
            

def main():
    '''main func'''
    print("Authenticating")
    session = Authenticate()
    print("Downloading File")
    getRecentIncidents(session)
    print("Updating TFS database")
    PushTfs( session )
    print("Verifying")
    Verify()

if __name__ == '__main__':
    main()
