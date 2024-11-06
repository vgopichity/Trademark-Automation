from yapsy.IPlugin import IPlugin
from pearls import *
import tornado.ioloop
import tornado.web
import base64
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
import requests
import socket

class ExampleTest(IPlugin):
    def main(self):
        # Create a connection to Database
        #connect = getConnectionToAlpha()
        listOfAllTickets = []
        fullListOfSFTicketURLs = []
        listOfExtractedURLs = []
        listOfUnparsedSFTckets = []
        listOfExtractedIPs = []

        # Make sure to export report in unicode : utf-8
        resultList = getDatafromCSVFileIntoDict('tickets.csv')
        progressCount = 0
        print("")
        for row in resultList:
            progressCount += 1
            print("Parsing file Progress: " + str(progressCount), end="\r", flush=True)
            # Only during testing
            ##if progressCount == 20:
            ##    break
            #print(row['Description'])
            #print('-'*10)
            SFTicketNumer = row['Ticket Number']
            ticketDescription = row['Description']
            SFTicketLink = self.convertSFTicketIDtoLink(row['Ticket ID'])
            reportedURL = self.extractURLfromContent(ticketDescription)
            reporterEmail = self.extractReporterEmailfromContent(ticketDescription)
            reportedDateTime = self.extractEpochTimeFromContent(ticketDescription, row['Date/Time Opened'])
            listOfAllTickets.append({'SFTicketNumer':SFTicketNumer, 'SFTicketLink':SFTicketLink, 'ticketDescription':ticketDescription, 'reportedDateTime':reportedDateTime})
            if reportedURL:
                #print(reportedURL)
                urlDomain = urlparse(reportedURL).hostname
                domainIP = self.getIPForADomain(urlDomain)
                ipOrg = self.getOrgFromIPUsingIPinfo(domainIP)
                #print(ipOrg)
                #print(urlDomain)
                fullListOfSFTicketURLs.append({'SFTicketNumer':SFTicketNumer, 'SFTicketLink':SFTicketLink, 'reportedURL':reportedURL, 'reportedDateTime':reportedDateTime, 'reporterEmail':reporterEmail, 'urlDomain':urlDomain, 'domainIP':domainIP, 'ipOrg':ipOrg})
                listOfExtractedURLs.append({'SFTicketNumer':SFTicketNumer, 'SFTicketLink':SFTicketLink, 'reportedURL':reportedURL, 'reportedDateTime':reportedDateTime, 'reporterEmail':reporterEmail, 'urlDomain':urlDomain, 'domainIP':domainIP, 'ipOrg':ipOrg})
            else:
                possibleURL = self.findURLInAString(ticketDescription)
                listOfUnparsedSFTckets.append({'SFTicketNumer':SFTicketNumer, 'SFTicketLink':SFTicketLink, 'reportedDateTime':reportedDateTime, 'reporterEmail':reporterEmail, 'ticketDescription':ticketDescription, 'possibleURL':possibleURL})

            #print(row['Ticket ID'])
            #print('-'*10)
            #print(self.convertSFTicketIDtoLink(row['Ticket ID']))
            #break
        #print(fullListOfSFTicketIPs)
        dictOfRepeatedURLs = self.getDictOfRepeatedURLs(fullListOfSFTicketURLs)
        listOfKnownReporters = self.getListOfKnownReporters(fullListOfSFTicketURLs)
        #print("-"*24)
        #print(len(fullListOfSFTicketIPs))
        print("")
        print("-"*24)
        print("Starting Web Server at port 8888")
        print("-"*24)
        app = self.make_app(listOfAllTickets, listOfExtractedURLs, listOfUnparsedSFTckets, dictOfRepeatedURLs, listOfKnownReporters)
        app.listen(8888)
        tornado.ioloop.IOLoop.current().start()


    def getDictOfRepeatedURLs(self, fullListOfSFTicketURLs):
        try:
            URLList = [ticketInfo['urlDomain'] for ticketInfo in fullListOfSFTicketURLs]
            # Get count of repeated values in list and store in a dict
            setList = list(set(URLList))
            URLDict = {i:URLList.count(i) for i in setList}
            # Filter only those having more than 2 count which can also be done in the above line directly like - IPDict = {i:IPList.count(i) for i in setList if IPList.count(i) > 2} but done seperately for readability
            finalURLDict = {url: count for url, count in URLDict.items() if count > 1}
            # Sort the dict and return
            return dict(sorted(finalURLDict.items(), key=lambda item: item[1]))
        except:
            return {}

    def getListOfKnownReporters(self, fullListOfSFTicketURLs):
        knownReporters = ['jeremy@jeremysmith.me.uk', 'kgerdenich@vistahigherlearning.com','adrian@bid13.com','anonymous.f5r6i5d1a3xy@gmail.com']
        finalList = []
        for ticketInfo in fullListOfSFTicketURLs:
            if ticketInfo['reporterEmail'] in knownReporters:
                finalList.append(ticketInfo)
        return finalList


    def extractURLfromContent(self, content):
        try:
            #reportedURLPattern = re.compile(r'URL\(s\) of the infringing content: (.*?)$',re.MULTILINE)
            reportedURLPattern = re.compile(r'of the infringing content: (.*?)Digital Signature',re.DOTALL)
            firstURL = re.search(reportedURLPattern, content).group(1)
            return firstURL
        except Exception as e:
            #print(e)
            #foundURLs = self.findURLsInAString(content)
            #for url in foundURLs:
                #return url #This will return the first url in the list
            return None

    def extractReporterEmailfromContent(self, content):
        try:
            reporterEmailPattern = re.compile(r'Email Address: (.*?)$',re.MULTILINE)
            reporterEmail = re.search(reporterEmailPattern, content).group(1)
            return reporterEmail
        except:
            return "unknown"

    def findIPsInAString(self, string):
        ipPattern = re.compile('(?:^|\b(?<!\.))(?:1?\d\d?|2[0-4]\d|25[0-5])(?:\.(?:1?\d\d?|2[0-4]\d|25[0-5])){3}(?=$|[^\w.])')
        try:
            ip = re.findall(ipPattern, string)
            return ip
        except:
            return []

    def findURLsInAString(self, string):
        urlPattern = re.compile(r'[(http://)|\w]*?[\w]*\.[-/\w]*\.\w*[(/{1})]?[#-\./\w]*[(/{1,})]?', re.IGNORECASE)
        try:
            url = re.findall(urlPattern, string)
            return url
        except:
            return []

    def findURLInAString(self, string):
        urlPattern = re.compile(r'[(http://)|\w]*?[\w]*\.[-/\w]*\.\w*[(/{1})]?[#-\./\w]*[(/{1,})]?', re.IGNORECASE)
        try:
            urlList = re.findall(urlPattern, string)
            for url in urlList:
                return url
        except:
            return ""

    def getIPForADomain(self, domainString):
        try:
            domainIP = socket.gethostbyname(domainString)
            return domainIP
        except:
            return "0.0.0.0"

    def getOrgFromIPUsingIPinfo(self, IP):
        try:
            if "0.0.0.0" not in IP:
                ## API token for IPinfo
                ipinfo_api_token = 'Enter your Token'
                ipinfoURL = "https://ipinfo.io/" + IP + "?token=" + ipinfo_api_token
                r = requests.get(ipinfoURL)
                ipInformation = r.json()
                ipOrg = ipInformation['org']
                return ipOrg
            else:
                return "NO IP"
        except Exception as e:
            #print(e)
            return "NOT FOUND"

    def extractEpochTimeFromContent(self, content, ticketDateTime):
        formattedDateTime = datetime.strptime(ticketDateTime, '%m/%d/%Y %I:%M %p')
        epochTime = formattedDateTime.timestamp()
        return int(epochTime)

    def convertSFTicketIDtoLink(self, ticketID):
        if len(ticketID) == 15:
            return "https://doinstance.lightning.force.com/lightning/r/Case/" + str(self.convertSF15IDto18ID(ticketID)) + "/view"
        elif len(ticketID) == 18:
            return "https://doinstance.lightning.force.com/lightning/r/Case/" + str(ticketID) + "/view"
        else:
            return None

    def convertSF15IDto18ID(self, ticket15ID):
        if len(ticket15ID) == 15:
            addon = ""
            for block in range(0,3):
                loop = 0
                for position in range(0,5):
                    current = ticket15ID[block*5+position]
                    if current >= 'A' and current <= 'Z':
                        loop += 1 << position
                addon = addon + "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"[loop]
            return str(ticket15ID) + str(addon)
        else:
            return 0

    def make_app(self, listOfAllTickets, listOfExtractedURLs, listOfUnparsedSFTckets, dictOfRepeatedURLs, listOfKnownReporters):
        return tornado.web.Application([
            (r"/", MainHandler),
            (r"/all", allHandler, dict(listOfAllTickets=listOfAllTickets)),
            (r"/extractedURLs", extractedURLsHandler, dict(listOfExtractedURLs=listOfExtractedURLs)),
            (r"/unParsed", unParsedHandler, dict(listOfUnparsedSFTckets=listOfUnparsedSFTckets)),
            (r"/repeatedURLs", repeatedURLsHandler, dict(dictOfRepeatedURLs=dictOfRepeatedURLs)),
            (r"/knownReporters", knownReportersHandler, dict(listOfKnownReporters=listOfKnownReporters))

        ])

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        #self.render('../shared_data/sf2.html')
        self.write(self.getHomePage())

    def getHomePage(self):
        return base64.b64decode("PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9ImVuIj4KICA8aGVhZD4KICAgIDxtZXRhIGNoYXJzZXQ9IlVURi04Ij4KICAgIDxtZXRhIG5hbWU9InZpZXdwb3J0IiBjb250ZW50PSJ3aWR0aD1kZXZpY2Utd2lkdGgsIGluaXRpYWwtc2NhbGU9MS4wIj4KICAgIDxtZXRhIGh0dHAtZXF1aXY9IlgtVUEtQ29tcGF0aWJsZSIgY29udGVudD0iaWU9ZWRnZSI+CiAgICA8bGluayBocmVmPSJkYXRhOmltYWdlL3BuZztiYXNlNjQsaVZCT1J3MEtHZ29BQUFBTlNVaEVVZ0FBQUNBQUFBQWdDQVlBQUFCemVucjBBQUFCcGtsRVFWUjRBY1hWQTQ4ZFlSVEg0YmUySGRaMm85cUlVWnZmb3c1cVIzVWJWZXY5RnRjM3pqcFlHL1hwcitZWnZwMTdrbWM4Yy81ajQ3bE95UWdjeGoyazBBcUJvQjFwUE1VSlRETFc2cFJNeDMzMFFEejZnRktzRHRONElDN2lQU1NFUEl6MzIzd0tzaEJMNnJEQ2EvTUZhSUJZMW8xdGJzMW4yR3F1Nk1JeXJma2daQ0F1eW5FRmU3QVNhN0VENTVHQXVLakdpSDhGdUF5QnBnbzcwZHZsS3E1R0hBTE4vVDkzbW8xM0VFVXhodmw0aVB2aERrVHhFWXQrM2VFK1JGR0svaVpBdVlSNC9uMmowWGlqWFhhTUNQRXQ2YWZkRHJ6RFJNUGdBRVN4eDhLWGREVkVjY0l3ZUtpc3JFRWZZNlAwdCtPcFlaQlNWdDYwK0Q4NXIvUklHd1p0eXNwREZnUHNVSHEwR3dhaTJHUXh3RnExVHlURkZ6UFhBZllvQVZxakNuQkZDWkNLb25sdmxDc0I3dms1a1B5VCszNDdJWXJEL3pjQVB6QlVLZnYyWU1RL0QyNGxBRDh3Rkh2NUpkc1B3Sm1oRktKNGorbjJBL0R2d0I1VVFUUzRhQ2dyQWJBSmgzQVROUkFYV1F6MC9jRDUybGJYZ0NtR3lrV0FCaXd3VkM0Q1pERGRVRkVIZUlmTEdHU29LQU84d1gzTWp1SmJMMmhEQ2c5eEFLT054L29FN1pMV3FibWY0VW9BQUFBQVNVVk9SSzVDWUlJPSIgcmVsPSJpY29uIiB0eXBlPSJpbWFnZS9wbmciIC8+CiAgICA8dGl0bGU+U2FsZXNmb3JjZSBIZWxwZXI8L3RpdGxlPgogICAgPCEtLSA8bWV0YSBuYW1lPSJidWktaWNvbnMiIGNvbnRlbnQ9Imh0dHBzOi8vYXNzZXRzLmRpZ2l0YWxvY2Vhbi5jb20vYnVpLzEuMi4yL2J1aS1pY29ucy5zdmciPiAtLT4KICAgIDwhLS0gQlVJIENTUyAtLT4KICAgIDxsaW5rIHJlbD0ic3R5bGVzaGVldCIgaHJlZj0iaHR0cHM6Ly9hc3NldHMuZGlnaXRhbG9jZWFuLmNvbS9idWkvMS4yLjIvYnVpLmNzcyI+CiAgPC9oZWFkPgoKICA8IS0tIFBhZ2UgU3R5bGVzIHNob3VsZCBiZSBicm9rZW4gb3V0IGludG8gdGhlaXIgb3duIHN0eWxlc2hlZXRzLCBidXQgdGhpcyBpcyBhIG9uZS1wYWdlIGRlbW8gZXhhbXBsZSAtLT4KICA8c3R5bGU+CiAgICAvKiBBZGRpdGlvbmFsIFN0eWxpbmcgSGVyZSAqLwogICAgLkV4YW1wbGUtZmlsbCB7CiAgICAgIGJhY2tncm91bmQtY29sb3I6ICMwMDY5ZmY7CiAgICAgIHBhZGRpbmc6IDFlbTsKICAgIH0KICA8L3N0eWxlPgoKICA8Ym9keT4KICAgIDxkaXYgaWQ9InJvb3QiIGNsYXNzPSJidWktQ29udGFpbmVyIj4KICAgICAgPGRpdiBjbGFzcz0iYnVpLUdyaWRDb250YWluZXIgYnVpLXUtZmxleE1pZGRsZSBidWktdS1tdi0tcmVndWxhciI+CiAgICAgICAgPGRpdiBjbGFzcz0iYnVpLUNvbC02IGJ1aS11LXRleHRMZWZ0IGJ1aS1JbmxpbmUgYnVpLXUtcHQtLXJlZ3VsYXIiPgogICAgICAgICAgPHN2ZyBjbGFzcz0iYnVpLUljb24gYnVpLUljb24tLXhsYXJnZSBidWktSWNvbi0tYmx1ZSI+PHVzZSB4bGluazpocmVmPSIjbG9nbyI+PC91c2U+PC9zdmc+CiAgICAgICAgICA8aDE+U2FsZXNmb3JjZSBIZWxwZXI8L2gxPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KICAgICAgCiAgICAgIAogICAgICA8ZGl2IGNsYXNzPSJidWktQmFubmVyIGJ1aS1CYW5uZXItLWRhbmdlciIgcm9sZT0iYmFubmVyIj4KICAgICAgICA8ZGl2IGNsYXNzPSJidWktQmFubmVyLWNvbnRlbnQiPgogICAgICAgICAgVGhpcyBzY3JpcHQgaXMganVzdCB0byBhdXRvbWF0ZSBhbmQgZmluZCBsb3cgaGFuZ2luZyB0aWNrZXRzIGluIFNGCiAgICAgICAgPC9kaXY+CiAgICAgICAgPGRpdiBjbGFzcz0iYnVpLUJhbm5lci1yaWdodCI+CiAgICAgICAgICA8YnV0dG9uIGNsYXNzPSJidWktQnV0dG9uLS1yZXNldCBidWktQmFubmVyLWNsb3NlIiB0eXBlPSJidXR0b24iPgogICAgICAgICAgICA8c3ZnIGNsYXNzPSJidWktSWNvbiI+CiAgICAgICAgICAgICAgPHRpdGxlPkNsb3NlIEJhbm5lcjwvdGl0bGU+CiAgICAgICAgICAgICAgPHVzZSB4bGluazpocmVmPSIjY2xvc2UiPjwvdXNlPgogICAgICAgICAgICA8L3N2Zz4KICAgICAgICAgIDwvYnV0dG9uPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KCiAgICAgIDx1bCBjbGFzcz0iYnVpLVRhYnMgYnVpLVRhYnMtbGlzdCI+CiAgICAgICAgPGxpIGNsYXNzPSJidWktdS1tci0tbWVkaXVtIj48YSBocmVmPSIjYWwiIGRhdGEtdGFiPkFsbDwvYT48L2xpPgogICAgICAgIDxsaSBjbGFzcz0iYnVpLXUtbXItLW1lZGl1bSI+PGEgaHJlZj0iI2V1IiBkYXRhLXRhYj5FeHRyYWN0ZWQgVVJMczwvYT48L2xpPgogICAgICAgIDxsaSBjbGFzcz0iYnVpLXUtbXItLW1lZGl1bSI+PGEgaHJlZj0iI3VwIiBkYXRhLXRhYj5VbnBhcnNlZDwvYT48L2xpPgogICAgICAgIDxsaSBjbGFzcz0iYnVpLXUtbXItLW1lZGl1bSI+PGEgaHJlZj0iI3J1IiBkYXRhLXRhYj5SZXBlYXRlZCBVUkxzPC9hPjwvbGk+CiAgICAgICAgPGxpIGNsYXNzPSJidWktdS1tci0tbWVkaXVtIj48YSBocmVmPSIja3IiIGRhdGEtdGFiPktub3duIFJlcG9ydGVyczwvYT48L2xpPgogICAgICA8L3VsPgogICAgICA8ZGl2IGNsYXNzPSJidWktVGFicy1jb250ZW50IGJ1aS1UYWJzLWNvbnRlbnQtLXRvcFJ1bGUiPgogICAgICAgIDxkaXYgY2xhc3M9ImJ1aS1UYWJzLXBhbmUiIGlkPSJhbCI+TG9hZGluZy4uLjwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImJ1aS1UYWJzLXBhbmUiIGlkPSJldSI+TG9hZGluZy4uLgogICAgICAgICAgPCEtLSA8ZGl2IGNsYXNzPSJidWktR3JpZENvbnRhaW5lciI+CiAgICAgICAgICAgIDx0YWJsZSBjbGFzcz0iYnVpLVRhYmxlIGJ1aS1UYWJsZS0tcmVzcG9uc2l2ZSI+CiAgICAgICAgICAgICAgPHRoZWFkPgogICAgICAgICAgICAgICAgPHRyPgogICAgICAgICAgICAgICAgICA8dGg+Tm8uPC90aD4KICAgICAgICAgICAgICAgICAgPHRoPlRpY2tldCBOdW1iZXI8L3RoPgogICAgICAgICAgICAgICAgICA8dGg+TGFzdCBVc2VyIElEPC90aD4KICAgICAgICAgICAgICAgICAgPHRoPlNGIExpbms8L3RoPgogICAgICAgICAgICAgICAgPC90cj4KICAgICAgICAgICAgICA8L3RoZWFkPgogICAgICAgICAgICAgIDx0Ym9keT4KICAgICAgICAgICAgICAgIDx0cj4KICAgICAgICAgICAgICAgICAgPHRkIGRhdGEtdGg9Ik5vLiI+MTwvdGQ+CiAgICAgICAgICAgICAgICAgIDx0ZCBkYXRhLXRoPSJUaWNrZXQgTnVtYmVyIj4xMTExMjU8L3RkPgogICAgICAgICAgICAgICAgICA8dGQgZGF0YS10aD0iTGFzdCBVc2VyIElEIj4xMjM0NTwvdGQ+CiAgICAgICAgICAgICAgICAgIDx0ZCBkYXRhLXRoPSJTRiBMaW5rIj48YSBocmVmPSIjIj5vcGVuPC9hPjwvdGQ+CiAgICAgICAgICAgICAgICA8L3RyPgogICAgICAgICAgICAgICAgPHRyPgogICAgICAgICAgICAgICAgICA8dGQgZGF0YS10aD0iTm8uIj4yPC90ZD4KICAgICAgICAgICAgICAgICAgPHRkIGRhdGEtdGg9IlRpY2tldCBOdW1iZXIiPjExMTEyNTwvdGQ+CiAgICAgICAgICAgICAgICAgIDx0ZCBkYXRhLXRoPSJMYXN0IFVzZXIgSUQiPjEyMzQ1PC90ZD4KICAgICAgICAgICAgICAgICAgPHRkIGRhdGEtdGg9IlNGIExpbmsiPjxhIGhyZWY9IiMiPm9wZW48L2E+PC90ZD4KICAgICAgICAgICAgICAgIDwvdHI+CiAgICAgICAgICAgICAgICA8dHI+CiAgICAgICAgICAgICAgICAgIDx0ZCBkYXRhLXRoPSJOby4iPjM8L3RkPgogICAgICAgICAgICAgICAgICA8dGQgZGF0YS10aD0iVGlja2V0IE51bWJlciI+MTExMTI1PC90ZD4KICAgICAgICAgICAgICAgICAgPHRkIGRhdGEtdGg9Ikxhc3QgVXNlciBJRCI+MTIzNDU8L3RkPgogICAgICAgICAgICAgICAgICA8dGQgZGF0YS10aD0iU0YgTGluayI+PGEgaHJlZj0iIyI+b3BlbjwvYT48L3RkPgogICAgICAgICAgICAgICAgPC90cj4KICAgICAgICAgICAgICA8L3Rib2R5PgogICAgICAgICAgICA8L3RhYmxlPgogICAgICAgICAgPC9kaXY+IC0tPgogICAgICAgIDwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImJ1aS1UYWJzLXBhbmUiIGlkPSJ1cCI+TG9hZGluZy4uLjwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImJ1aS1UYWJzLXBhbmUiIGlkPSJydSI+TG9hZGluZy4uLjwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImJ1aS1UYWJzLXBhbmUiIGlkPSJrciI+TG9hZGluZy4uLjwvZGl2PgogICAgICA8L2Rpdj4KCiAgICAKCiAgICAKCiAgICAKCiAgICA8IS0tIE1pbmlmaWVkIFNsaW0galF1ZXJ5IGJlY2F1c2UgaXQncyB1c2VkIGluIG9uZSBvZiBvdXIgdmVuZG9yIGxpYnJhcmllcywgQ2hvc2VuLCBmb3IgZm9ybXMgLS0+CiAgICA8c2NyaXB0IHNyYz0iaHR0cHM6Ly9jb2RlLmpxdWVyeS5jb20vanF1ZXJ5LTMuNi4wLm1pbi5qcyI+PC9zY3JpcHQ+CgogICAgPCEtLSBCVUkgSlMgLS0+CiAgICA8c2NyaXB0IHNyYz0iaHR0cHM6Ly9hc3NldHMuZGlnaXRhbG9jZWFuLmNvbS9idWkvMS4yLjIvYnVpLmpzIj48L3NjcmlwdD4KCiAgICA8IS0tIEljb24gTGlicmFyeSBzaG91bGQgYmUgaW5jbHVkZWQgd2hlcmUgcG9zc2libGUgd2l0aCBhIHRlbXBsYXRlLiBUaGlzIGJyaW5ncyB0aGUgbGlicmFyeSBpbnRvIHRoZSBoZWFkIHVzaW5nIEFKQVggLS0+CiAgICA8c2NyaXB0PgogICAgICB2YXIgeGhyID0gbmV3IFhNTEh0dHBSZXF1ZXN0OwogICAgICB4aHIub3BlbignZ2V0JywnaHR0cHM6Ly9hc3NldHMuZGlnaXRhbG9jZWFuLmNvbS9idWkvMS4yLjIvYnVpLWljb25zLnN2ZycsdHJ1ZSk7CiAgICAgIHhoci5vbnJlYWR5c3RhdGVjaGFuZ2UgPSBmdW5jdGlvbigpewogICAgICAgIGlmICh4aHIucmVhZHlTdGF0ZSAhPSA0KSByZXR1cm47CiAgICAgICAgdmFyIHN2ZyA9IHhoci5yZXNwb25zZVhNTC5kb2N1bWVudEVsZW1lbnQ7CiAgICAgICAgc3ZnID0gZG9jdW1lbnQuaW1wb3J0Tm9kZShzdmcsdHJ1ZSk7IC8vIHN1cnByaXNpbmdseSBvcHRpb25hbCBpbiB0aGVzZSBicm93c2VycwogICAgICAgIGRvY3VtZW50LmhlYWQuYXBwZW5kQ2hpbGQoc3ZnKTsKICAgICAgfTsKICAgICAgeGhyLnNlbmQoKTsKICAgIDwvc2NyaXB0PgogICAgCiAgICA8c2NyaXB0PgogICAgICAkKGRvY3VtZW50KS5yZWFkeShmdW5jdGlvbigpIHsKICAgICAgICBzZXRUaW1lb3V0KGZ1bmN0aW9uKCkgewogICAgICAgICAgJC5hamF4KHt1cmw6ICIvYWxsIiwgc3VjY2VzczogZnVuY3Rpb24ocmVzdWx0KXsKICAgICAgICAgICAgJCgiI2FsIikuaHRtbChyZXN1bHQpOwogICAgICAgICAgfX0pOwogICAgICAgICAgJC5hamF4KHt1cmw6ICIvZXh0cmFjdGVkVVJMcyIsIHN1Y2Nlc3M6IGZ1bmN0aW9uKHJlc3VsdCl7CiAgICAgICAgICAgICQoIiNldSIpLmh0bWwocmVzdWx0KTsKICAgICAgICAgIH19KTsKICAgICAgICAgICQuYWpheCh7dXJsOiAiL3VuUGFyc2VkIiwgc3VjY2VzczogZnVuY3Rpb24ocmVzdWx0KXsKICAgICAgICAgICAgJCgiI3VwIikuaHRtbChyZXN1bHQpOwogICAgICAgICAgfX0pOwogICAgICAgICAgJC5hamF4KHt1cmw6ICIvcmVwZWF0ZWRVUkxzIiwgc3VjY2VzczogZnVuY3Rpb24ocmVzdWx0KXsKICAgICAgICAgICAgJCgiI3J1IikuaHRtbChyZXN1bHQpOwogICAgICAgICAgfX0pOwogICAgICAgICAgJC5hamF4KHt1cmw6ICIva25vd25SZXBvcnRlcnMiLCBzdWNjZXNzOiBmdW5jdGlvbihyZXN1bHQpewogICAgICAgICAgICAkKCIja3IiKS5odG1sKHJlc3VsdCk7CiAgICAgICAgICB9fSk7CiAgICAgICAgfSwgMzAwMCk7CiAgICAgIH0pOwogICAgICAvKiQoZG9jdW1lbnQpLnJlYWR5KGZ1bmN0aW9uKCkgewogICAgICAgIC8vIEluc3RlYWQgb2YgYnV0dG9uIGNsaWNrLCBjaGFuZ2UgdGhpcy4KICAgICAgICBzZXRUaW1lb3V0KGZ1bmN0aW9uKCkgewogICAgICAgICAgalF1ZXJ5LnN1cHBvcnQuY29ycyA9IHRydWU7CiAgICAgICAgICAkLmFqYXgoewogICAgICAgICAgICBhc3luYzogdHJ1ZSwKICAgICAgICAgICAgdHlwZTogIkdFVCIsCiAgICAgICAgICAgIGNhY2hlOiB0cnVlLAogICAgICAgICAgICB1cmw6ICIvb2xkQWNjb3VudHMiLAogICAgICAgICAgICBzdWNjZXNzOiBmdW5jdGlvbihyZXN1bHQpIHsKICAgICAgICAgICAgICAkKCIjb2EiKS5odG1sKHJlc3VsdCk7CiAgICAgICAgICAgIH0sCiAgICAgICAgICAgIC8vanNvbnBDYWxsYmFjazogJ2NhbGxiYWNrRm5jJywKICAgICAgICAgICAgZmFpbHVyZTogZnVuY3Rpb24oKSB7fSwKICAgICAgICAgICAgY29tcGxldGU6IGZ1bmN0aW9uKGRhdGEpIHsKICAgICAgICAgICAgICAkKCIjZGl2MiIpLmh0bWwoIlN1Y2Nlc3MgOiAiKTsKICAgICAgICAgICAgICBpZiAoZGF0YS5yZWFkeVN0YXRlID09ICc0JyAmJiBkYXRhLnN0YXR1cyA9PSAnMjAwJykgewoKICAgICAgICAgICAgICAgIC8vZG9jdW1lbnQud3JpdGUoIlN1Y2Nlc3MgOiAiKTsKICAgICAgICAgICAgICAgIC8vZG9jdW1lbnQud3JpdGUoZGF0YSk7CiAgICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgIGRvY3VtZW50LndyaXRlbG4oIkZhaWxlZCIpOwogICAgICAgICAgICAgIH0KICAgICAgICAgICAgfQogICAgICAgICAgfSk7CiAgICAgICAgfSwgMzAwMCk7CiAgICAgIH0pOyovCgogICAgPC9zY3JpcHQ+CiAgPC9ib2R5Pgo8L2h0bWw+")

class allHandler(tornado.web.RequestHandler):
    def initialize(self, listOfAllTickets):
        self.listOfAllTickets = listOfAllTickets

    def get(self):
        outputHTML = '<div class="bui-GridContainer">\
        <table class="bui-Table bui-Table--responsive">\
            <thead>\
                <tr>\
                <th>No.</th>\
                <th>Ticket Number</th>\
                <th>Reported Date</th>\
                <th>SF Link</th>\
                <th>Description</th>\
                </tr>\
            </thead>\
            <tbody>'
        count = 0
        for ticketInfo in self.listOfAllTickets:
            count += 1
            outputHTML += '<tr>'
            outputHTML += '<td data-th="No.">' + str(count) + '</td>'
            outputHTML += '<td data-th="Ticket Number">' + str(ticketInfo['SFTicketNumer']) + '</td>'
            outputHTML += '<td data-th="Reported Date">' + str(datetime.utcfromtimestamp(ticketInfo['reportedDateTime']).strftime('%Y-%m-%d')) + " " + str(datetime.utcfromtimestamp(ticketInfo['reportedDateTime']).strftime('%H:%M:%S')) + '</td>'
            outputHTML += '<td data-th="SF Link"><a href="' + str(ticketInfo['SFTicketLink']) + '" target="_blank" rel="noopener noreferrer">open</a></td>'
            outputHTML += '<td data-th="Description" style="white-space: pre-line; word-wrap: break-word;">' + str(ticketInfo['ticketDescription'])  + '</td>'
            outputHTML += '</tr>'
        outputHTML += '</tbody>\
            </table>\
        </div>'
        self.write(outputHTML)

class extractedURLsHandler(tornado.web.RequestHandler):
    def initialize(self, listOfExtractedURLs):
        self.listOfExtractedURLs = listOfExtractedURLs

    def get(self):
        outputHTML = '<div class="bui-GridContainer">\
        <table class="bui-Table bui-Table--responsive">\
            <thead>\
                <tr>\
                <th>No.</th>\
                <th>Ticket Number</th>\
                <th>Reported Date</th>\
                <th>SF Link</th>\
                <th>Base Domain</th>\
                <th>Domain IP</th>\
                <th>IP ORG</th>\
                <th>URL</th>\
                </tr>\
            </thead>\
            <tbody>'
        count = 0
        for ticketInfo in self.listOfExtractedURLs:
            count += 1
            outputHTML += '<tr>'
            outputHTML += '<td data-th="No.">' + str(count) + '</td>'
            outputHTML += '<td data-th="Ticket Number">' + str(ticketInfo['SFTicketNumer']) + '</td>'
            outputHTML += '<td data-th="Reported Date">' + str(datetime.utcfromtimestamp(ticketInfo['reportedDateTime']).strftime('%Y-%m-%d')) + " " + str(datetime.utcfromtimestamp(ticketInfo['reportedDateTime']).strftime('%H:%M:%S')) + '</td>'
            outputHTML += '<td data-th="SF Link"><a href="' + str(ticketInfo['SFTicketLink']) + '" target="_blank" rel="noopener noreferrer">open</a></td>'
            outputHTML += '<td data-th="Domain">' + str(ticketInfo['urlDomain']) + ' (<a href="https://www.virustotal.com/gui/domain/' + str(ticketInfo['urlDomain']) + '/details" target="_blank" rel="noopener noreferrer">info</a>)</td>'
            outputHTML += '<td data-th="IP">' + str(ticketInfo['domainIP']) + '</td>'
            outputHTML += '<td data-th="IPORG">' + str(ticketInfo['ipOrg']) + '</td>'
            outputHTML += '<td data-th="URL">' + str(ticketInfo['reportedURL']) + '</td>'
            #outputHTML += '<td data-th="URL" style="word-wrap: break-word;max-width:150px">' + str(ticketInfo['reportedURL']) + '</td>'
            outputHTML += '</tr>'
        outputHTML += '</tbody>\
            </table>\
        </div>'
        self.write(outputHTML)

class unParsedHandler(tornado.web.RequestHandler):
    def initialize(self, listOfUnparsedSFTckets):
        self.listOfUnparsedSFTckets = listOfUnparsedSFTckets

    def get(self):
        outputHTML = '<div class="bui-GridContainer">\
        <table class="bui-Table bui-Table--responsive">\
            <thead>\
                <tr>\
                <th>No.</th>\
                <th>Ticket Number</th>\
                <th>Reported Date</th>\
                <th>SF Link</th>\
                <th>Possible URL</th>\
                <th max-width="120">Description</th>\
                </tr>\
            </thead>\
            <tbody>'
        count = 0
        for ticketInfo in self.listOfUnparsedSFTckets:
            count += 1
            outputHTML += '<tr>'
            outputHTML += '<td data-th="No.">' + str(count) + '</td>'
            outputHTML += '<td data-th="Ticket Number">' + str(ticketInfo['SFTicketNumer']) + '</td>'
            outputHTML += '<td data-th="Reported Date">' + str(datetime.utcfromtimestamp(ticketInfo['reportedDateTime']).strftime('%Y-%m-%d')) + " " + str(datetime.utcfromtimestamp(ticketInfo['reportedDateTime']).strftime('%H:%M:%S')) + '</td>'
            outputHTML += '<td data-th="SF Link"><a href="' + str(ticketInfo['SFTicketLink']) + '" target="_blank" rel="noopener noreferrer">open</a></td>'
            outputHTML += '<td data-th="Possible URL">' + str(ticketInfo['possibleURL'])  + '</td>'
            outputHTML += '<td data-th="Description" style="white-space: pre-line; word-wrap: break-word;">' + str(ticketInfo['ticketDescription'])  + '</td>'

            outputHTML += '</tr>'
        outputHTML += '</tbody>\
            </table>\
        </div>'
        self.write(outputHTML)

class repeatedURLsHandler(tornado.web.RequestHandler):
    def initialize(self, dictOfRepeatedURLs):
        self.dictOfRepeatedURLs = dictOfRepeatedURLs

    def get(self):
        outputHTML = '<div class="bui-GridContainer">\
        <table class="bui-Table bui-Table--responsive">\
            <thead>\
                <tr>\
                <th>No.</th>\
                <th>URL</th>\
                <th>Count</th>\
                <th>SF Link</th>\
                </tr>\
            </thead>\
            <tbody>'
        count = 0
        for URL, URLCount in self.dictOfRepeatedURLs.items():
            count += 1
            outputHTML += '<tr>'
            outputHTML += '<td data-th="No.">' + str(count) + '</td>'
            outputHTML += '<td data-th="URL">' + str(URL) + '</td>'
            outputHTML += '<td data-th="Count">' + str(URLCount) + '</td>'
            outputHTML += '<td data-th="SF Link"><a href="' + self.getSFSearchTicketsLink(URL) + '" target="_blank" rel="noopener noreferrer">open</a></td>'
            outputHTML += '</tr>'
        outputHTML += '</tbody>\
            </table>\
        </div>'
        self.write(outputHTML)

    def getSFSearchTicketsLink(self, searchTerm):
        searchJSON = '{\
          "componentDef": "forceSearch:searchPageDesktop",\
          "attributes": {\
            "term": "' + str(searchTerm) + '",\
            "scopeMap": {\
              "color": "F2CF5B", \
              "icon": "https://doinstance.my.salesforce.com/img/icon/t4v35/standard/case_120.png",\
              "nameField": "CaseNumber",\
              "label": "Ticket",\
              "disambiguationFieldType": "STRING",\
              "name": "Case",\
              "cacheable": "Y",\
              "disambiguationField": "Subject",\
              "id": "Case",\
              "fields": "CaseNumber\nSubject\nStatus\ntoLabel(Status) Status__l\nCreatedDate\nformat(CreatedDate) CreatedDate__f\nOwner.NameOrAlias\nSuppliedEmail\nLast_Agent_Date_Time__c\nformat(Last_Agent_Date_Time__c) Last_Agent_Date_Time__c__f\nLast_Agent__r.Name\nOwnerId\nIsEscalated\nLastModifiedDate\nRecordTypeId\nId\nLastModifiedById\nSystemModstamp",\
              "labelPlural": "Tickets",\
              "entity": "Case"\
            },\
            "context": {\
              "FILTERS": {},\
              "searchSource": "ASSISTANT_DIALOG",\
              "disableIntentQuery": true,\
              "disableSpellCorrection": false,\
              "permsAndPrefs": {\
                "SearchUi.feedbackComponentEnabled": false,\
                "OrgPreferences.ChatterEnabled": true,\
                "Search.crossObjectsAutoSuggestEnabled": true,\
                "OrgPreferences.EinsteinSearchNaturalLanguageEnabled": true,\
                "SearchUi.searchUIInteractionLoggingEnabled": false,\
                "MySearch.userCanHaveMySearchBestResult": true,\
                "SearchResultsLVM.lvmEnabledForTopResults": false\
              }\
            },\
            "groupId": "DEFAULT"\
          },\
          "state": {}\
        }'
        finalLink = "https://doinstance.lightning.force.com/one/one.app#" + base64.b64encode(bytes(re.sub(r"[\n\t\s]*", "", searchJSON), 'utf-8')).decode("utf-8")
        return finalLink

class knownReportersHandler(tornado.web.RequestHandler):
    def initialize(self, listOfKnownReporters):
        self.listOfKnownReporters = listOfKnownReporters

    def get(self):
        outputHTML = '<div class="bui-GridContainer">\
        <table class="bui-Table bui-Table--responsive">\
            <thead>\
                <tr>\
                <th>No.</th>\
                <th>Ticket Number</th>\
                <th>Reporter Email</th>\
                <th>SF Link</th>\
                </tr>\
            </thead>\
            <tbody>'
        count = 0
        for ticketInfo in self.listOfKnownReporters:
            count += 1
            outputHTML += '<tr>'
            outputHTML += '<td data-th="No.">' + str(count) + '</td>'
            outputHTML += '<td data-th="Ticket Number">' + str(ticketInfo['SFTicketNumer']) + '</td>'
            outputHTML += '<td data-th="Reporter Email">' + str(ticketInfo['reporterEmail']) + '</td>'
            outputHTML += '<td data-th="SF Link"><a href="' + str(ticketInfo['SFTicketLink']) + '" target="_blank" rel="noopener noreferrer">open</a></td>'
            outputHTML += '</tr>'
        outputHTML += '</tbody>\
            </table>\
        </div>'
        self.write(outputHTML)
