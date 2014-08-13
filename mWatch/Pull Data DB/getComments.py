import requests
import xlrd
from requests_ntlm import HttpNtlmAuth

def DownloadFile(url, cred):
    '''Downloads file with credentials'''
    local_filename = "sharepoint_tickets.xlsx"
    r = requests.get(url, auth=cred)
    f = open(local_filename, 'wb')
    for chunk in r.iter_content(chunk_size=512 * 1024):
        if chunk: # filter out keep-alive new chunks
            f.write(chunk)
    f.close()
    return

def InsertComments(engine):
    '''Inserts comments + satisfaction in DB'''
    wb = xlrd.open_workbook("sharepoint_tickets.xlsx")
    sheet = wb.sheets()[0]
    for i in range(1, sheet.nrows):
        if (sheet.cell(i,14).value != "" or sheet.cell(i,15).value != ""):
            values = "'" + str(int(sheet.cell(i,0).value)) + "','" + str(int(sheet.cell(i,14).value)) + "','" + str(sheet.cell(i,15).value) + "'"
            query = "INSERT INTO Comments VALUES("+values+")"
            engine.execute(query)

		
def main():
    '''main func'''
    cred = HttpNtlmAuth('FORDFOUNDATION\\b.marks','ZaQwSx12')
    url = "https://fordnet.fordfound.org/ts/OPER/IT/BSD/Documents/mWatch%20Ticket%20Reports/BSD_mWatch_Tickets_Report.xlsx"
    DownloadFile(url,cred)
    InsertComments()

if __name__ == '__main__':
    main()
