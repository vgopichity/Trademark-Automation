import pymysql.cursors
import time

#--------------------------------------------------- Account Data -------------------------------------------------------
def harvestAccountUserEmailFromID(userID, alphaConnection):
    try:
        with alphaConnection['digitalocean'].cursor() as cursor:
            # 
            sql = "select email_address from users \
                    where \
                    id = %s;"
            cursor.execute(sql, [userID])
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                # Return an empty string on error
                return ""
            # Save ids to a list
            userEmail = [i['email_address'] for i in result]
        # Only return the first result
        return userEmail[0]
    except Exception as e:
        print("Error getting UserEmailFromID! MSG: " + str(e))
        return ""
        
        
def harvestAccountPromoUsedListFromID(userID, alphaConnection):
    def getCodeFromString(commentString):
        try:
            return commentString.partition("Code: ")[-1]
        except:
            return commentString
        
    promoList = []
    try:
        with alphaConnection['digitalocean'].cursor() as cursor:
            # SQL Query
            sql = " select comment from audit_actions \
                    where name = 'promo.applied' AND \
                    user_id = %s"
            cursor.execute(sql, [userID])
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                # Return an empty list on error
                promoList = []
            else:
                # Save to a list
                for i in result:
                    if "Code: " in i['comment']:
                        promoList.append(getCodeFromString(i['comment']))
                
    except:
        print("Error getting Promo List!")
        promoList = []
        
    return promoList
    
    
def harvestAccountNamesOfBYOIFromID(userID, alphaConnection):
    imageNameList = []
    try:
        with alphaConnection['digitalocean'].cursor() as cursor:
            # SQL Query
            sql = "select name from images \
                    where \
                    user_id = %s "
            cursor.execute(sql, [userID])
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                # Return an empty list on error
                imageNameList = []
            else:
                # Save to a list
                imageNameList = [i['name'] for i in result]
    except:
        print("Error getting Image Names!")
        imageNameList = []
        
    return imageNameList
    
    
def harvestEmailChangeFromID(userID, alphaConnection):
    emailChangeList = []
    try:
        with alphaConnection['digitalocean'].cursor() as cursor:
            # SQL Query
            sql = "select comment from audit_actions \
                    where name = 'user.request_change_email' AND comment is not null AND \
                    user_id = %s"
            cursor.execute(sql, [userID])
            result = cursor.fetchall()
            if (result is None) or (len(result) == 0):
                # Return an empty list on error
                emailChangeList = []
            else:
                # Save to a list
                emailChangeList = [i['comment'] for i in result]
    except:
        print("Error getting Email Change List!")
        emailChangeList = []
        
    emailChangesDict = {}
    for item in emailChangeList:    
        try:
            newItem = ((item.replace('(','')).replace(')','')).split(" -> ")
            emailChangesDict[newItem[0]] = newItem[1]
        except:
            print("Error processing Email Change data!")
    
    return emailChangesDict