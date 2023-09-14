import os
import json


def get_app_config() -> dict:
    active_directory = os.getcwd()
    config_Path = active_directory + r'\appConfig.json'
    # Open the JSON file
    with open(config_Path) as json_file:
        # Load the JSON data into a dictionary
        app_config_settings = json.load(json_file)

    return app_config_settings
