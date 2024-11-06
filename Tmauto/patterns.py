import pymysql.cursors
import statistics
import time

    
def cohorts(userIDList, alphaConnection, patternName, showProgress = True):
    # All patterns are added in a if-elif ladder
    patternChoice = str(patternName).lower()
    if patternChoice == 'abuse_sas_not_locked':
        return abuse_sas_not_locked(userIDList, alphaConnection, showProgress = showProgress)
    elif patternChoice == 'same_cost_droplet':
        return same_cost_droplet(userIDList, alphaConnection, showProgress = showProgress)
    elif patternChoice.startswith('droplet_creation_time_difference'):
        parameters = getExtraParametersforCohorts(patternChoice)
        return droplet_creation_time_difference(userIDList, alphaConnection, parameters, showProgress = showProgress)
    elif patternChoice == 'droplet_name_seq_of_three':
        return droplet_name_seq_of_three(userIDList, alphaConnection, showProgress = showProgress)
    elif patternChoice.startswith('droplet_count'):
        parameters = getExtraParametersforCohorts(patternChoice)
        return droplet_count(userIDList, alphaConnection, parameters, showProgress = showProgress)
    else:
        # Return an empty list on error
        return []
        
def getExtraParametersforCohorts(inputChoice):
    if inputChoice.startswith('droplet_creation_time_difference'):
        # Example inputs : droplet_creation_time_difference or droplet_creation_time_difference=100
        try:
            timeDifference = int(inputChoice.split("=")[1].strip())
        except:
            # Default value
            timeDifference = 60
        # A dictionary of parameters necessary
        return { "timeDifference" : timeDifference }
    elif inputChoice.startswith('droplet_count'):
        # Example inputs : droplet_count or droplet_count=3 or droplet_count=3+ or droplet_count=3-
        try:
            givenValue = inputChoice.split("=")[1].strip()
            if givenValue.endswith('+'):
                compareType = '>'
                numOfDroplet = int(givenValue[:-1])
            elif givenValue.endswith('-'):
                compareType = '<'
                numOfDroplet = int(givenValue[:-1])
            else:
                compareType = '='
                numOfDroplet = int(givenValue)
        except:
            # Default value
            numOfDroplet = 8
            compareType = '='
        # A dictionary of parameters necessary
        return { "numOfDroplet" : numOfDroplet , "compareType" : compareType}
    else:
        return ''
#------------------------------------------ Write all the Cohort Functions below----------------------------------------------

def abuse_sas_not_locked(userIDList, alphaConnection, parameters=None, showProgress = True):
    userIDMatchList = []
    # This is used to create a number of %s equal to number of elements in the list
    format_strings = ','.join(['%s'] * len(userIDList))
    #userids = ','.join(f'"{w}"' for w in userIDList)
    with alphaConnection['digitalocean'].cursor() as cursor:
        # 
        sql = "select distinct id from users \
                where \
                id IN (" + format_strings + ") and \
                is_admin_locked = 0 and \
                is_admin = 0 and \
                is_free <> 1 and \
                lifetime_value <= 5 and \
                created_at BETWEEN (CURRENT_DATE() - INTERVAL 3 MONTH) AND CURRENT_DATE();"
        cursor.execute(sql, tuple(userIDList))
        result = cursor.fetchall()
        if (result is None) or (len(result) == 0):
            # Return an empty list on error
            return userIDMatchList
        # Save ids to a list
        userIDMatchList = [i['id'] for i in result]
    return userIDMatchList
    
def same_cost_droplet(userIDList, alphaConnection, parameters=None, showProgress = True):
    userIDMatchList = []
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for userids in userIDList:
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Sub Progress: " + str(progressCount) + " out of " + str(len(userIDList)), end="\r", flush=True)
        # ----- End of Progress --------
        with alphaConnection['digitalocean'].cursor() as cursor:
            # Read a single record
            sql = "select d.name, d.created_at, s.monthly_price from droplets d inner join sizes s on s.id=d.size_id where d.user_id = %s and d.is_active = 1 order by d.created_at;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Check for same cost droplets
            price_list = [i['monthly_price'] for i in result]
            if not statistics.mean(price_list) == price_list[0]:
                continue
            userIDMatchList.append(userids)
    return userIDMatchList
    
def droplet_creation_time_difference(userIDList, alphaConnection, parameters=None, showProgress = True):
    # Read parameters
    timeDifference = parameters['timeDifference']
    userIDMatchList = []
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for userids in userIDList:
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Sub Progress: " + str(progressCount) + " out of " + str(len(userIDList)), end="\r", flush=True)
        # ----- End of Progress --------
        with alphaConnection['digitalocean'].cursor() as cursor:
            # Read a single record
            sql = "select d.name, d.created_at, s.monthly_price from droplets d inner join sizes s on s.id=d.size_id where d.user_id = %s and d.is_active = 1 order by d.created_at;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Check for creation time difference 
            creation_time_list = [i['created_at'] for i in result]
            sorted_datetime = sorted(creation_time_list)
            if (sorted_datetime[0] - sorted_datetime[-1]).total_seconds() > timeDifference:
                continue
            userIDMatchList.append(userids)
    return userIDMatchList

def droplet_name_seq_of_three(userIDList, alphaConnection, parameters=None, showProgress = True):
    userIDMatchList = []
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for userids in userIDList:
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Sub Progress: " + str(progressCount) + " out of " + str(len(userIDList)), end="\r", flush=True)
        # ----- End of Progress --------
        with alphaConnection['digitalocean'].cursor() as cursor:
            # Read a single record
            sql = "select d.name, d.created_at, s.monthly_price from droplets d inner join sizes s on s.id=d.size_id where d.user_id = %s and d.is_active = 1 order by d.created_at;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Check droplet names in sequence
            droplet_name_last_char_list = [i['name'][-1] for i in result]
            joined_droplet_char = '' . join(str(i) for i in sorted(droplet_name_last_char_list))
            if any(sublist in joined_droplet_char for sublist in ('123','234','345','456','567','678','789')):
                userIDMatchList.append(userids)
            else:
                continue
    return userIDMatchList

def droplet_count(userIDList, alphaConnection, parameters=None, showProgress = True):
    # Read parameters
    numOfDroplet = parameters['numOfDroplet']
    compareType = parameters['compareType']
    userIDMatchList = []
    # This is used to create a number of %s equal to number of elements in the list
    format_strings = ','.join(['%s'] * len(userIDList))
    #userids = ','.join(f'"{w}"' for w in userIDList)
    with alphaConnection['digitalocean'].cursor() as cursor:
        # 
        sql = "select user_id from droplets \
                where \
                is_active = 1 and \
                user_id IN (" + format_strings + ") \
                group by user_id \
                having count(user_id) " + compareType + " " + str(numOfDroplet) + ";"
        cursor.execute(sql, tuple(userIDList))
        result = cursor.fetchall()
        if (result is None) or (len(result) == 0):
            # Return an empty list on error
            return userIDMatchList
        # Save ids to a list
        userIDMatchList = [i['user_id'] for i in result]
    return userIDMatchList

#--------------------------------------------------- End of Cohort Functions -------------------------------------------------------

def negativeIndicators(userIDDict, alphaConnection, patternName, showProgress = True):
    
    # All patterns are added in a if-elif ladder
    patternChoice = str(patternName).lower()
    if patternChoice.startswith('high_runrate_multiplier'):
        parameters = getExtraParametersforNegativeIndicators(patternChoice)
        return high_runrate_multiplier(userIDDict, alphaConnection, parameters, showProgress = showProgress)
    elif patternChoice.startswith('logins_from_multiple_countries'):
        return logins_from_multiple_countries(userIDDict, alphaConnection, showProgress = showProgress)
    elif patternChoice.startswith('login_and_payment_from_different_countries'):
        return login_and_payment_from_different_countries(userIDDict, alphaConnection, showProgress = showProgress)
    else:
        # Return an empty list on error
        return []

def getExtraParametersforNegativeIndicators(inputChoice):
    if inputChoice.startswith('high_runrate_multiplier'):
        try:
            multiplier = int(inputChoice.split("=")[1])
        except:
            # Default value
            multiplier = 10
        # A dictionary of parameters necessary
        return { "multiplier" : multiplier }
    else:
        return ''
        
#------------------------------------------ Write all the Negative Indicator Functions below----------------------------------------------------

def high_runrate_multiplier(userIDDict, alphaConnection, parameters=None, showProgress = True):
    # Read parameters
    multiplier = parameters['multiplier']
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for userids in list(userIDDict):
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Sub Progress: " + str(progressCount) + " out of " + str(len(userIDDict)), end="\r", flush=True)
        # ----- End of Progress --------
        with alphaConnection['digitalocean'].cursor() as cursor:
            # Read a single record
            sql = "select lifetime_value, run_rate from users where id = %s;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Check for High Run Rate and select only first value of list because there can be only 1 row
            lifetime_value = int([i['lifetime_value'] for i in result][0])
            # If LTV is 0 then consider as 5 since it is the least value with PayPal
            lifetime_value = 5 if lifetime_value == 0 else lifetime_value
            run_rate = int([i['run_rate'] for i in result][0])
            if run_rate < lifetime_value * multiplier:
                continue
            userIDDict[userids] += 1
    return userIDDict
    
    
def logins_from_multiple_countries(userIDDict, alphaConnection, parameters=None, showProgress = True):
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for userids in list(userIDDict):
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Sub Progress: " + str(progressCount) + " out of " + str(len(userIDDict)), end="\r", flush=True)
        # ----- End of Progress --------
        with alphaConnection['authentication'].cursor() as cursor:
            # Read a single record
            sql = "select user_id, country_code from security_ops_user_signin_data where user_id = %s group by user_id, country_code;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Check if the number of rows output is greater than 1
            if len(result) > 1:
                userIDDict[str(userids)] += 1
    return userIDDict
    
    
def login_and_payment_from_different_countries(userIDDict, alphaConnection, parameters=None, showProgress = True):
    login_countries = []
    payment_countries = []
    tax_countries = []
    # ------ Just for Progress ------
    progressCount = 0
    # ----- End of Progress --------
    for userids in list(userIDDict):
        # ------ Just for Progress ------
        if showProgress:
            progressCount += 1
            print("Sub Progress: " + str(progressCount) + " out of " + str(len(userIDDict)), end="\r", flush=True)
        # ----- End of Progress --------
        with alphaConnection['authentication'].cursor() as cursor:
            # Read a single record
            sql = "select distinct country_code from security_ops_user_signin_data where user_id = %s;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Save the countries to the list
            login_countries = [i['country_code'] for i in result]
        
        with alphaConnection['digitalocean'].cursor() as cursor:
            # Read a single record
            sql = "select distinct country from user_payment_attempts where user_id=%s;"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Save the countries to the list
            payment_countries = [i['country'] for i in result]
            
        with alphaConnection['digitalocean'].cursor() as cursor:
            # Read a single record
            sql = "select distinct iso from countries where ID IN (select country_id from taxation_locations where user_id= %s);"
            cursor.execute(sql, (userids,))
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                continue
            # Save the countries to the list
            tax_countries = [i['iso'] for i in result]    
            
        for country in login_countries:
            if country not in [*payment_countries, *tax_countries]:
                userIDDict[str(userids)] += 1
                break
    return userIDDict

#--------------------------------------------------- End of Negative Indicator Functions -------------------------------------------------------