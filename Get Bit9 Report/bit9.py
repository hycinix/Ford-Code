# -*- coding: utf-8 -*-
import requests
import time
import xlsxwriter

def Authenticate():
    '''Authenticates to parity.fordfound.org'''
    session = requests.session()
    loginurl = "https://parity.fordfound.org/login.php"
    logindata = {"username" : "brian",
            "password" : ";yL$*bp!Kq5/S?/k"}
    response = session.post(loginurl,logindata)

    dashboardurl = "https://parity.fordfound.org/Dashboard/Dashboard/Dashboard.aspx"
    data = {"BootstrapSessionHandle" : Bootstrap(response.content) }
    response = session.post(dashboardurl, data)

    return session
    
def Bootstrap( content ):
    '''Gets the bootstrap number from dashboard'''
    delim = 'BootstrapSessionHandle" value="'
    start = content.find(delim) + len(delim)
    end = content.find('"', start)
    return content[start:end]

def WriteHTML( content ):
    '''Writes to test.html doc on desktop'''
##    fh = open("C:\\users\\b.marks\\desktop\\test.html","w")
    fh = open("Bit9\\test.html","w")
    fh.write(content)
    fh.close()

def WriteCSV( content ):
    '''Writes to test.csv doc on desktop'''
    date = time.strftime("%Y-%m-%d")
    filename = "Blocked_Files_(All)" + date + ".csv"
##    fh = open("C:\\users\\b.marks\\desktop\\" + filename,"w")
    fh = open("Bit9\\" + filename,"w")
    fh.write(content)
    fh.close()

def GetCSV( session ):
    '''Gets CSV file'''
    csvurl = "https://parity.fordfound.org/events.php?CSV_EXPORT"
    csvfile = session.get(csvurl)
    return csvfile.content

def GetContents( csvfile ):
    '''Gets List of Rows of the file'''
    fhr = open(csvfile,"r")
    file_read = fhr.read()
    rows = file_read.split("\n")
    fhr.close()
    return rows

def GetSources():
    '''Gets dictionary of filename to possible source'''
    fh = open("Bit9\\sources.txt","r")
    read = fh.read()
    rows = read.split("\n")

    sources = {}

    for i in range(len(rows)):
        columns = rows[i].split(",")
        sources[columns[0].strip('"')] = columns[1].strip('"')
    sources[""] = 'Possible Source'
    return sources

def WriteXlsx(csvfile):
    '''Writes spreadsheet'''
    sources = GetSources()
    csvRows = csvfile.split("\n")
    date = time.strftime("%Y-%m-%d")
    name = "Blocked_Files_(All)"
    filename = "Bit9\\" + name + date + ".xlsx"
    workbook = xlsxwriter.Workbook(filename)
    pivot = workbook.add_worksheet('Report')
    data = workbook.add_worksheet(name)

    csvHeader = csvRows[0].split(",")
    csvHeader[0] = 'Possible Source'
    header = []
    for i in range(len(csvHeader)):
        header.append({'header' : csvHeader[i].strip('"')})
    
    data.add_table('A1:N%s' % (len(csvfile) - 1), {'columns' : header })
    data.set_column('A:N', 20)

    for i in range(1, len(csvRows)):
        csvCols = csvRows[i].split(",")
        for j in range(len(csvCols)):
            if len(csvCols) < 9:
                continue
            try:
                source = sources[csvCols[9].strip('"')]
            except KeyError:
                source = 'Unknown'
            data.write(i,j,csvCols[j].strip('"').decode('utf-8'))
            data.write(i,0, source)

    workbook.close()

def main():
    '''main func'''
    print("Authenticating")
    session = Authenticate()
    print("Downloading CSV")
    csvfile = GetCSV( session )
    
######     Not needed!!
####    print("Writing CSV to disk")
####    WriteCSV( csvfile )
    print("Generating File")
    WriteXlsx(csvfile)
    

if __name__ == '__main__':
    main()
