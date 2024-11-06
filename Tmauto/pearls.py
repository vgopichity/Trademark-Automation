import sys, os, time
from getpass import getpass
import pymysql.cursors
import pathlib
import patterns
import harvester
import re
import ipaddress
import requests
import json
import csv

# Check if a directory exists
def checkIfDirExist(dirpath):
    try:
        if pathlib.Path(dirpath).is_dir():
            return True
        else:
            return False
    except:
        return False

# Check if a file exists
def checkIfFileExist(filepath):
    try:
        if pathlib.Path(filepath).is_file():
            return True
        else:
            return False
    except:
        return False

def getSharedFolder():
    if checkIfDirExist(pathlib.Path(__file__).parent.resolve() / "shared_data"):
        return pathlib.Path(__file__).parent.resolve() / "shared_data"
    else:
        sys.exit("'shared_data' folder does not exist! Create it first and run the script again.")

def getCurrentPath():
    #return os.path.realpath(__file__)
    return pathlib.Path(__file__).parent.resolve()

def getUserInput(stringToDisplay = "Enter an input: "):
    """
    Get the input from user in String format
    
    :param stringToDisplay: The text to display to user while asking the input.
    :type stringToDisplay: String

    :return: The result of the user input.
    :rtype: String
    """
    getInputTemp = input(stringToDisplay)    
    return getInputTemp
    
def getCSVStringInputList(stringToDisplay = "Enter a comma sepearted input: ", doStrip = True):
    getInputTemp = input(stringToDisplay)
    inputList = getInputTemp.split(",")
    if doStrip:
        strippedList = [input.strip() for input in inputList]
        return strippedList
    return inputList
    
def getLineWiseFileInputList(stringToDisplay = "Enter the full file name: ", doStrip = True):
    getInputFilename = input(stringToDisplay)
    inputList = getDatafromFile(getInputFilename, lines = True, rightStrip = False)
    # "fullStrip = doStrip" can be added to the function getDatafromFile since it already supports striping but I will do the below instead just for consistency across the functions and there is no over head due to this as both the ways does the same computation
    if doStrip:
        strippedList = [s.strip() for s in inputList]
        return strippedList
    return inputList

def getUserPass(stringToDisplay = "Enter the password: "):
    return getpass(stringToDisplay) 
    
def printListLineWise(givenList):
    for element in givenList:
        print(element)

def saveDataToFile(filename, data, successMsg=True):
    getExtension = ''.join(pathlib.Path(filename).suffixes)
    newFileName = filename.replace(getExtension,'') + '_' + str(int(time.time())) + getExtension
    filePath = getSharedFolder() / newFileName
    try:
        with open(filePath, 'w') as f:
            print(data, file=f, end='')
        if successMsg:
            print("Successfully written data to: " + newFileName)
    except:
        print("Something went wrong while writing to the file!")

def getDatafromFile(filename, lines = False, rightStrip = True, fullStrip = False):
    filePath = getSharedFolder() / filename
    if not checkIfFileExist(filePath):
        sys.exit("Could not find the file! Please put the file in the shared folder and run the script again.")
    try:
        with open(filePath, 'r') as f:
            datalines = f.readlines()
            if rightStrip:
                datalines = [line.rstrip() for line in datalines]
            if fullStrip:
                datalines = [line.strip() for line in inputList]
        if lines:
            return datalines
        else:
            return '\n'.join(datalines)
    except:
        print("Something went wrong while reading the file!")
        
def getDatafromCSVFile(filename, customDelimiter = ',', customQuotechar = '"', customNewline=''):
    filePath = getSharedFolder() / filename
    if not checkIfFileExist(filePath):
        sys.exit("Could not find the file! Please put the file in the shared folder and run the script again.")
    try:
        with open(filePath, newline=customNewline) as csvfile:
            csvData = list(csv.reader(csvfile, delimiter=customDelimiter, quotechar=customQuotechar))
        return csvData
    except Exception as e:
        print("Something went wrong while reading the CSV file! : " + str(e))
        
def getDatafromCSVFileIntoDict(filename, customDelimiter = ',', customQuotechar = '"', customNewline=''):
    filePath = getSharedFolder() / filename
    if not checkIfFileExist(filePath):
        sys.exit("Could not find the file! Please put the file in the shared folder and run the script again.")
    try:
        with open(filePath, newline=customNewline) as csvfile:
            csvData = list(csv.DictReader(csvfile, delimiter=customDelimiter, quotechar=customQuotechar))
        return csvData
    except Exception as e:
        print("Something went wrong while reading the CSV file! : " + str(e))

def getConnectionToAlpha(dbName = 'all', dbUser = None, dbPass = None, dbHost = 'prod-alpha-mysql.internal.digitalocean.com'):
    connection = {}
    if dbUser == None:
        dbUser = getUserInput("DB Username:")
    if dbPass != None:
        print("Storing password in String is not advised! Please Enter below,")
    dbPass = getUserPass("DB Password:")
    if dbName == 'all':
        connection['digitalocean'] = pymysql.connect(host=dbHost,
                         user=dbUser,
                         password=dbPass,
                         database='digitalocean',
                         cursorclass=pymysql.cursors.DictCursor)
        connection['authentication'] = pymysql.connect(host=dbHost,
                         user=dbUser,
                         password=dbPass,
                         database='authentication',
                         cursorclass=pymysql.cursors.DictCursor)
        connection['usermetadata'] = pymysql.connect(host=dbHost,
                         user=dbUser,
                         password=dbPass,
                         database='usermetadata',
                         cursorclass=pymysql.cursors.DictCursor)
    else:
        connection[dbName] = pymysql.connect(host=dbHost,
                         user=dbUser,
                         password=dbPass,
                         database=dbName,
                         cursorclass=pymysql.cursors.DictCursor)
    return connection

def runSQLQuery(connection, userquery, dbName='digitalocean'):
    with connection[dbName].cursor() as cursor:
        sql = userquery
        cursor.execute(sql)
        result = cursor.fetchall()
        return result    

def runSQLQueryWithParam(connection, userquery, paramTuple, dbName='digitalocean'):
    with connection[dbName].cursor() as cursor:
        sql = userquery
        cursor.execute(sql, paramTuple)
        result = cursor.fetchall()
        return result

def convertCursorToSingleList(result, key):
    try:
        listData = [i[key] for i in result]
        return listData
    except Exception as e:
        #print(e)
        sys.exit("Error converting to list! Check your data and key.")

def convertResultToAccountSweeperFormat(result, key):
    try:
        listData = [i[key] for i in result]
        accountSweeperFormat = '\n'.join(str(v) for v in listData)
        return accountSweeperFormat
    except Exception as e:
        #print(e)
        sys.exit("Error converting to Account Sweeper Format! Check your data and key.")
        
def convertListToAccountSweeperFormat(inputList):
    try:
        accountSweeperFormat = '\n'.join(str(v) for v in inputList)
        return accountSweeperFormat
    except Exception as e:
        #print(e)
        sys.exit("Error converting to Account Sweeper Format! Check your input list.")

# This is to get around the issue of Sammy Cert not recognised in virtual env of python so manually providing the file to the function.
def getDefaultVerifyTLSSettingValue():
    filePath = getSharedFolder() / "sammyca-ca.crt"
    if not checkIfFileExist(filePath):
        return "True"
    else:
        return filePath
        
# Validate if UserID is an integer
def validateUserID(userID):
    try: 
        int(userID)
        return True
    except:
        print("UserID contains invalid value!")
        return False
        
# Validate a list of UserIDs if they are valid integers
def validateUserIDList(userIDList):
    try:
        # Try to convert all values to int to see if there is any invalid character
        userIDList = [ int(x) for x in userIDList ]
        return True
    except:
        print("UserID List contains invalid value!")
        return False

# Remove all chars except number and dot(.) from a string        
def sanitizeIP4(IP4String):
    return re.sub(r"[^0-9\.]+", "", IP4String)

# Remove all chars except number and dot(.) and A-F from a string        
def sanitizeIP6(IP6String):
    return re.sub(r"[^A-Fa-f0-9:]+", "", IP6String)

# Check if a string is a valid IP address
def isIPaddress(IPString):
    try:
        ip = ipaddress.ip_address(IPString)
        return True
    except:
        return False

# Validate an IP address based on conditions
# isVersion = 4, 6
# isType = any, public, private, reserved, multicast, unspecified, loopback, linklocal
def isValidIP(ip, isVersion = 0, isType = "any", sanitize=True):
    sanitizedIP = ip
    #Check for IPv4 first as it has less characters
    if isVersion == 4 and (not isIPaddress(sanitizeIP4(ip))):
        return False
    elif isVersion == 6 and (not isIPaddress(sanitizeIP6(ip))):
        return False
    elif isVersion == 0 or isVersion == 4 or isVersion == 6:
        if isIPaddress(sanitizeIP4(ip)):
            if sanitize:
                sanitizedIP = sanitizeIP4(ip)
        elif isIPaddress(sanitizeIP6(ip)):
            if sanitize:
                sanitizedIP = sanitizeIP6(ip)
        else:
            return False
    else:
        return False
    
    # Save string in IP format
    try:
        ipaddr = ipaddress.ip_address(sanitizedIP)
    except:
        return False
    #Check for IP type    
    if isType == 'any':
        return True
    elif isType == 'public':
        return True if ipaddr.is_global else False
    elif isType == 'private':
        return True if ipaddr.is_private else False
    elif isType == 'reserved':
        return True if ipaddr.is_reserved else False
    elif isType == 'multicast':
        return True if ipaddr.is_multicast else False
    elif isType == 'unspecified':
        return True if ipaddr.is_unspecified else False
    elif isType == 'loopback':
        return True if ipaddr.is_loopback else False
    elif isType == 'linklocal':
        return True if ipaddr.is_link_local else False
    else:
        return False

def securityIPAMgetListURNsForIP(ip, verifyTLS = getDefaultVerifyTLSSettingValue()):
    baseURL = "https://security-ipam-ui.internal.digitalocean.com"
    APIPath = "/v1/ipam/ListURNsForIP"
    url = baseURL + APIPath
    payload = '{"ip":"' + ip + '","page":1,"per_page":1}'
    header = {"Content-type": "application/json"} 
    r = requests.post(url, data=payload, headers=header, verify=verifyTLS)
    if r.status_code != 200:
        return "invalid"
    if "droplet" not in r.text:
        return "invalid"
    if "results" not in r.text:
        return "invalid"    
    response = json.loads(r.text)
    return response['results']
    
def securityIPAMgetNetworkInfo(urnsList, verifyTLS = getDefaultVerifyTLSSettingValue()):
    baseURL = "https://security-ipam-ui.internal.digitalocean.com"
    APIPath = "/v1/droplet/NetworkInfo"
    url = baseURL + APIPath
    payloadURN = ','.join(f'"{w}"' for w in urnsList)
    payload = '{"canonical_urns":[' + payloadURN + ']}'
    header = {"Content-type": "application/json"} 
    r = requests.post(url, data=payload, headers=header, verify=verifyTLS)
    if r.status_code != 200:
        return "invalid"
    if "owner_id" not in r.text:
        return "invalid"
    if "network_info" not in r.text:
        return "invalid"    
    response = json.loads(r.text)
    return response['network_info']
    
def securityIPAMgetIPResolver(ip, getDate = time.strftime("%Y-%m-%d"), getTime = '00:00:01', verifyTLS = getDefaultVerifyTLSSettingValue()):
    baseURL = "https://security-ipam-ui.internal.digitalocean.com"
    APIPath = "/v1/resolve/droplet"
    url = baseURL + APIPath
    payload = '{"ip_address":"' + ip + '","active_at": "' + getDate + 'T' + getTime + 'Z"}'
    header = {"Content-type": "application/json"} 
    r = requests.post(url, data=payload, headers=header, verify=verifyTLS)
    if r.status_code != 200:
        return "invalid"
    if "owner_id" not in r.text:
        return "invalid"   
    response = json.loads(r.text)
    return response

def getLastUserIDForIP(IPAddress, verifyTLS = getDefaultVerifyTLSSettingValue()):
    urnJSON = securityIPAMgetListURNsForIP(IPAddress, verifyTLS)
    if urnJSON == 'invalid':
        return "invalid"
    dropletURNList = [urnJSON[0]['urn']]
    networkInfoJSON = securityIPAMgetNetworkInfo(dropletURNList, verifyTLS)
    try:
        # To get the first json item you need to first find the key value as it cannot be accessed by index like [0] so convert all the keys to a list and then index the first item of the list
        firstJSON = list(networkInfoJSON.keys())[0]
        ownerID = networkInfoJSON[firstJSON]['owner_id']
        return ownerID
    except:
        return "invalid"
        
        
def getLastUserIDForDropletIPFromAplha(alphaConnection, IPAddress):
    with alphaConnection['digitalocean'].cursor() as cursor:
        sql = "select user_id from droplets \
                where \
                beip = %s \
                order by created_at desc \
                limit 1;"
        cursor.execute(sql, (str(IPAddress), ) )
        result = cursor.fetchall()
        if (result is None) or (len(result) == 0):
            # Return an empty list 
            return "invalid"
        else:
            userID = [i['user_id'] for i in result]
            return userID[0]
            
def getLastUserIDandDateTimeOfAnIPFromAlpha(alphaConnection, IPAddress):
    with alphaConnection['digitalocean'].cursor() as cursor:
        sql = "select user_id, UNIX_TIMESTAMP(created_at) as dropletAssignSec from droplets \
                where \
                beip = %s \
                order by created_at desc \
                limit 1;"
        cursor.execute(sql, (str(IPAddress), ) )
        result = cursor.fetchall()
        if (result is None) or (len(result) == 0):
            # Return an empty list 
            return "invalid"
        else:
            userID = [i['user_id'] for i in result]
            dropletAssignSec = [i['dropletAssignSec'] for i in result]
            return [userID[0], dropletAssignSec[0]]
            
def getLastUserIDandDateTimeOfAnIP(IPAddress, verifyTLS = getDefaultVerifyTLSSettingValue()):
    urnJSON = securityIPAMgetListURNsForIP(IPAddress, verifyTLS)
    if urnJSON == 'invalid':
        return "invalid"
    dropletURNList = [urnJSON[0]['urn']]
    networkInfoJSON = securityIPAMgetNetworkInfo(dropletURNList, verifyTLS)
    try:
        dropletAssignSec = urnJSON[0]['assign_sec']
        #dropletUnassignSec = urnJSON[0]['unassign_sec']
        # To get the first json item you need to first find the key value as it cannot be accessed by index like [0] so convert all the keys to a list and then index the first item of the list
        firstJSON = list(networkInfoJSON.keys())[0]
        ownerID = networkInfoJSON[firstJSON]['owner_id']
        return [ownerID, dropletAssignSec]
    except:
        return "invalid"
    
def getLastDropletIDForIP(IPAddress, verifyTLS = getDefaultVerifyTLSSettingValue()):
    urnJSON = securityIPAMgetListURNsForIP(IPAddress, verifyTLS)
    if urnJSON == 'invalid':
        return "invalid"
    dropletURNList = [urnJSON[0]['urn']]
    networkInfoJSON = securityIPAMgetNetworkInfo(dropletURNList, verifyTLS)
    try:
        # To get the first json item you need to first find the key value as it cannot be accessed by index like [0] so convert all the keys to a list and then index the first item of the list
        firstJSON = list(networkInfoJSON.keys())[0]
        dropletID = networkInfoJSON[firstJSON]['droplet_id']
        return dropletID
    except:
        return "invalid"
    
def getLastActiveUserIDForIP(IPAddress, verifyTLS = getDefaultVerifyTLSSettingValue()):
    urnJSON = securityIPAMgetListURNsForIP(IPAddress, verifyTLS)
    if urnJSON == 'invalid':
        return "invalid"
    if urnJSON[0]['unassign_sec'] != 0 or not urnJSON[0]['is_active']:
        return "inactive"
    dropletURNList = [urnJSON[0]['urn']]
    networkInfoJSON = securityIPAMgetNetworkInfo(dropletURNList, verifyTLS)
    try:
        # To get the first json item you need to first find the key value as it cannot be accessed by index like [0] so convert all the keys to a list and then index the first item of the list
        firstJSON = list(networkInfoJSON.keys())[0]
        ownerID = networkInfoJSON[firstJSON]['owner_id']
        return ownerID
    except:
        return "invalid"

def getLastActiveDropletIDForIP(IPAddress, verifyTLS = getDefaultVerifyTLSSettingValue()):
    urnJSON = securityIPAMgetListURNsForIP(IPAddress, verifyTLS)
    if urnJSON == 'invalid':
        return "invalid"
    if urnJSON[0]['unassign_sec'] != 0 or not urnJSON[0]['is_active']:
        return "inactive"
    dropletURNList = [urnJSON[0]['urn']]
    networkInfoJSON = securityIPAMgetNetworkInfo(dropletURNList, verifyTLS)
    try:
        # To get the first json item you need to first find the key value as it cannot be accessed by index like [0] so convert all the keys to a list and then index the first item of the list
        firstJSON = list(networkInfoJSON.keys())[0]
        dropletID = networkInfoJSON[firstJSON]['droplet_id']
        return dropletID
    except:
        return "invalid"
        
def getExactUserIDForIP(IPAddress, getDate = time.strftime("%Y-%m-%d"), getTime = '00:00:01', verifyTLS = getDefaultVerifyTLSSettingValue()):
    dropletInfoJSON = securityIPAMgetIPResolver(IPAddress, getDate, getTime, verifyTLS)
    try:
        ownerID = dropletInfoJSON['owner_id']
        return ownerID
    except:
        return "invalid"
        
def getExactUserIDForIPFromAlpha(alphaConnection, IPAddress, getUnixTime = int(time.time()) ):
    with alphaConnection['digitalocean'].cursor() as cursor:
        sql = "select user_id, UNIX_TIMESTAMP(created_at) as dropletAssignSec from droplets \
                where \
                beip = %s \
                order by created_at desc;"
        cursor.execute(sql, (str(IPAddress), ) )
        result = cursor.fetchall()
        if (result is None) or (len(result) == 0):
            # Return an empty list 
            return "invalid"
        else:
            for i in result:        
                userID = i['user_id']
                dropletAssignSec = i['dropletAssignSec']
                if int(getUnixTime) >= int(dropletAssignSec): 
                    return userID
            #if nothing matches in for loop return Invalid
            return "invalid"
        
def getExactDropletIDForIP(IPAddress, getDate = time.strftime("%Y-%m-%d"), getTime = '00:00:01', verifyTLS = getDefaultVerifyTLSSettingValue()):
    dropletInfoJSON = securityIPAMgetIPResolver(IPAddress, getDate, getTime, verifyTLS)
    try:
        dropletID = dropletInfoJSON['id']
        return dropletID
    except:
        return "invalid"

def getIPtoLastUserIDList(IPAddressList, verifyTLS = getDefaultVerifyTLSSettingValue()):
    userIDList = []
    for ip in IPAddressList:
        userID = getLastUserIDForIP(ip, verifyTLS)
        userIDList.append(userID)
    return userIDList
    
def getIPtoLastDropletIDList(IPAddressList, verifyTLS = getDefaultVerifyTLSSettingValue()):
    dropletIDList = []
    for ip in IPAddressList:
        dropletID = getLastDropletIDForIP(ip, verifyTLS)
        dropletIDList.append(dropletID)
    return dropletIDList
    
def getActiveUserListOfRegion(regionName, alphaConnection, dropletMonthLimit = 3):
    userIDList = []
    with alphaConnection['digitalocean'].cursor() as cursor:
        # 
        sql = "select distinct user_id from droplets \
                where region_id=(select id from regions where slug = %s) \
                and is_active=1 and \
                created_at BETWEEN (CURRENT_DATE() - INTERVAL %s MONTH) AND CURRENT_DATE();"
        cursor.execute(sql, (regionName, str(dropletMonthLimit),))
        result = cursor.fetchall()
        if result is None:
            # Return an empty list on error
            return userIDList
        # Save ids to a list
        userIDList = [i['user_id'] for i in result]
    return userIDList

def getActiveDropletListOfRegion(regionName, alphaConnection, dropletMonthLimit = 3):
    dropletIDList = []
    with alphaConnection['digitalocean'].cursor() as cursor:
        # 
        sql = "select distinct id from droplets \
                where region_id=(select id from regions where slug = %s) \
                and is_active=1 and \
                created_at BETWEEN (CURRENT_DATE() - INTERVAL %s MONTH) AND CURRENT_DATE();"
        cursor.execute(sql, (regionName, str(dropletMonthLimit),))
        result = cursor.fetchall()
        if result is None:
            # Return an empty list on error
            return dropletIDList
        # Save ids to a list
        dropletIDList = [i['id'] for i in result]
    return dropletIDList

def getActiveUserListOfNode(nodeName, alphaConnection):
    userIDList = []
    with alphaConnection['digitalocean'].cursor() as cursor:
        # 
        sql = "select distinct user_id from droplets \
                where server_id=(select id from servers where name = %s) \
                and is_active=1;"
        cursor.execute(sql, (nodeName,))
        result = cursor.fetchall()
        if result is None:
            # Return an empty list on error
            return userIDList
        # Save ids to a list
        userIDList = [i['user_id'] for i in result]
    return userIDList
    
def getActiveDropletListOfNode(nodeName, alphaConnection):
    dropletIDList = []
    with alphaConnection['digitalocean'].cursor() as cursor:
        # 
        sql = "select distinct id from droplets \
                where server_id=(select id from servers where name = %s) \
                and is_active=1;"
        cursor.execute(sql, (nodeName,))
        result = cursor.fetchall()
        if result is None:
            # Return an empty list on error
            return dropletIDList
        # Save ids to a list
        dropletIDList = [i['id'] for i in result]
    return dropletIDList

def matchCohorts(userIDList, alphaConnection, patternList = ['abuse_sas_not_locked'], showProgress = True, getIDsInInteger = True):
    # Input verification of userIDList
    try:
        # Try to convert all values to int to see if there is any invalid character
        userIDList = [ int(x) for x in userIDList ]
        # Convert back to string for further usage
        userIDList = [ str(x) for x in userIDList ]
    except:
        print("UserID List contains invalid value! Exiting")
        # Return an empty list on error
        return []
    # Remove duplicate userIDs
    userIDList = list(set(userIDList))
    # Check for each pattern in a loop
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for pattern in patternList:
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Matching Pattern " + str(progressCount) + " out of " + str(len(patternList)))
        # ----- End of Progress --------
        # If userIDList is empty due to an error or intentionally then end immediately as it does not make sense to continue
        if len(userIDList) > 0:
            userIDList = patterns.cohorts(userIDList, alphaConnection, pattern, showProgress = showProgress)
    if getIDsInInteger:
        userIDList = [ int(x) for x in userIDList ]
    return userIDList

def checkNegativeIndicators(userIDList, alphaConnection, patternList = [''], showProgress = True, returnList = True, getIDsInInteger = True):
    # Input verification of userIDList
    try:
        # Try to convert all values to int to see if there is any invalid character
        userIDList = [ int(x) for x in userIDList ]
        # Convert back to string for further usage
        userIDList = [ str(x) for x in userIDList ]
    except:
        print("UserID List contains invalid value! Exiting")
        # Return an empty list on error
        return []
    # Remove duplicate userIDs
    userIDList = list(set(userIDList))
    # Create a dictionary of UserIDs
    userIDDict = dict.fromkeys(userIDList, 0)
    # Check for each pattern in a loop
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for pattern in patternList:
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Checking Negative Indicator " + str(progressCount) + " out of " + str(len(patternList)))
        # ----- End of Progress --------
        # If userIDList is empty due to an error or intentionally then end immediately as it does not make sense to continue
        if len(userIDDict) > 0:
            userIDDict = patterns.negativeIndicators(userIDDict, alphaConnection, pattern, showProgress = showProgress)
            
    # Filter only items which has values greater than 0 (Meaning matched atleast 1 indicator)
    matchedUserIDDict = {key:value for (key,value) in userIDDict.items() if value > 0}
    if getIDsInInteger:
        matchedUserIDDict = {int(key):matchedUserIDDict[key] for key in matchedUserIDDict}
    if returnList:
        return list(matchedUserIDDict) 
    return matchedUserIDDict
    
#--------------------------------------------------- Function calls for harvester -------------------------------------------------------

def getAccountUserEmailFromID(userID, alphaConnection):
    if not validateUserID(userID):
        return "error"
    return harvester.harvestAccountUserEmailFromID(userID, alphaConnection)
    
def getAccountPromoUsedListFromID(userID, alphaConnection):
    if not validateUserID(userID):
        return "error"
    return harvester.harvestAccountPromoUsedListFromID(userID, alphaConnection)
    
def getAccountNamesOfBYOIFromID(userID, alphaConnection):
    if not validateUserID(userID):
        return "error"
    return harvester.harvestAccountNamesOfBYOIFromID(userID, alphaConnection)
    
def getEmailChangeFromID(userID, alphaConnection):
    if not validateUserID(userID):
        return "error"
    return harvester.harvestEmailChangeFromID(userID, alphaConnection)