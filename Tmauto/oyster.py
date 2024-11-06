from yapsy.PluginManager import PluginManager
import sys, requests
import inquirer
from inquirer.themes import load_theme_from_dict

currentVersion = 0.2
checkUpdate = False

# Code to check for updates (Incomplete as it needs login to check for update)
def checkForUpdate():
    versionLink = "https://example.com"
    try:
        version = requests.get(versionLink)
        if int(version.text) == currentVersion:
            print("You have the latest version of the script!")
        else:
            print("There is an update available! Kindly download the latest scripts from https://example.com")
    except:
        print("Could not check for Update! Kindly check manually at https://example.com")

def main():
    # Check for updates
    if checkUpdate:
        print("----------------------")
        print("Checking for updates...")
        print("----------------------")
        checkForUpdate()
    # Build the manager
    simplePluginManager = PluginManager(plugin_info_ext="info")
    # Tell it the default location where to find plugins
    simplePluginManager.setPluginPlaces(["plugins"])
    # Collect Plugins without loading them
    simplePluginManager.locatePlugins()
    # Variable to store all the plugin names in the plugin directory
    myAvailablePlugins = []
    # Variable to store plugin count
    pluginCount = 0

    # Activate all loaded plugins and save it the info in a variable
    for foundPlugins in simplePluginManager.getPluginCandidates():
        # Add plugins to the plugin list
        myAvailablePlugins.append(foundPlugins)
        # Increment plugin count for each plugin
        pluginCount += 1

    # Initialize the Script Manager
    print("\n-----------------------------")
    print("Welcome to SOC Script Manager!")
    print("------------------------------")
    # Iterate through the description list
    choices_list = []
    for idx, val in enumerate(myAvailablePlugins, start=1):
        choices_list.append(str(idx) + "] " + str(val[-1].name))
    choices_list.append("0] EXIT")
    question = [inquirer.List('choice',message="Select the script you want to run",choices=choices_list,),]
    
    
    # Custom Theme for the selector
    custom_theme_blue = {
        "Question": {
            "mark_color": "yellow",
            "brackets_color": "dodgerblue",
            "default_color": "deepskyblue2"
        },
        "List": {
            "selection_color": "white_on_dodgerblue",
            "selection_cursor": "➤",
            "unselected_color": "normal"
        },
        "Checkbox": {
            "selection_color": "white_on_dodgerblue",
            "selection_icon": "➤",
            "selected_icon": "☒",
            "selected_color": "dodgerblue",
            "unselected_color": "normal",
            "unselected_icon": "☐"
        }
    }
    # Take user input for the script they want to run
    answer = inquirer.prompt(question, theme=load_theme_from_dict(custom_theme_blue))

    # Check if input in a number and then take input
    try:
        choice = int(answer['choice'].split(']')[0])
    except ValueError:
        sys.exit("Invalid input provide! Exiting...")

    # Check if number is within range
    if (choice < 0 or choice > pluginCount):
        sys.exit("Invalid option selected! Exiting...")

    # Check if number is 0
    if (choice == 0):
        sys.exit("Exiting...")

    # If everything is right call the selected function
    # I am clearing the candidate list manually because it is popluated when locatePlugins is called and I only want to populate it with the plugin I want otherwise the option is to remove all the plugins which I do not want but this will be inefficient once the number of plugins are large and I want to select only one
    simplePluginManager._candidates.clear()
    simplePluginManager.appendPluginCandidate(myAvailablePlugins[choice - 1])
    # Load the selected plugin
    simplePluginManager.loadPlugins()
    print("\n-------------------------------\nExecuting your selected script\n-------------------------------\n")
    myAvailablePlugins[choice - 1][-1].plugin_object.main()
    print("\n---------------------------\nEnd of Execution of script\n---------------------------\n")        

# Run when the script is executed explicitly
if __name__ == "__main__":
    main()