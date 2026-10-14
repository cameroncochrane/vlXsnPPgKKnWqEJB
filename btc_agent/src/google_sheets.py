import os
import base64
import json
from google.oauth2 import service_account

# Things to put in the sheet:
# - 


# Google Sheet: https://docs.google.com/spreadsheets/d/16xCo6fEscpNHEAqC9uXQjQrdUBlwZ_-LUEtPkIyTcPU/edit?gid=0#gid=0 

# Decode the Base64 environment variable (as the credentials are a json)
decoded_json = base64.b64decode(os.environ["GOOGLE_CREDENTIALS_BASE64"]).decode("utf-8")
credentials_info = json.loads(decoded_json)
print(credentials_info) # Check if it is loaded in env

# Load credentials directly into the Google client
credentials = service_account.Credentials.from_service_account_info(credentials_info)
