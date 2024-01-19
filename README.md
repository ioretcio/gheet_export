# Archivarius API

This program is designed to interact with Google Sheets and PostgreSQL database. It fetches data from a Google Sheet, processes it and stores it into a PostgreSQL database. It also downloads files from Google Drive and stores them in a local directory.

## Required Libraries

- httplib2
- apiclient.discovery
- oauth2client.service_account
- googleapiclient.http
- io
- psycopg2
- os
- dotenv

## Required Files

- credentials.json: This file is required for authenticating the Google API. It should be placed in the same directory as the script.
- .env: This file contains SPREAD_SHEET_ID and SHEET_NAME
## How to Run

1. Install the required libraries using pip.
2. Set up your Google API credentials and download the credentials.json file.
3. Set the environment variables for the Google Sheet ID and Sheet Name.
4. Run the script using Python 3.
