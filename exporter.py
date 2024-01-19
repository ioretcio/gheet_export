import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials	
from googleapiclient.http import MediaIoBaseDownload
import io
import psycopg2

import os
from dotenv import load_dotenv
load_dotenv()

SPREAD_SHEET_ID = os.getenv('SPREAD_SHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME')
range = "A2:G400"

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE =  "credentials.json"
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
httpAuth = creds.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)
spreadsheetId = SPREAD_SHEET_ID
sheet = service.spreadsheets().values().batchGet(spreadsheetId=spreadsheetId,
                                                                ranges=[f"{SHEET_NAME}!{range}"],
                                                                valueRenderOption='FORMATTED_VALUE',
                                                                dateTimeRenderOption='FORMATTED_STRING').execute()
drive_service = apiclient.discovery.build('drive', 'v3', http=httpAuth)

def get_connection():
    conn = None
    try:
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(
            database="archivarius_api", host="localhost",
            user="postgres", password="postgres",
            port=5432)
        conn.autocommit = True
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return conn
conn = get_connection()





def recursive_download_folder(folder_id, product_id):
    results = drive_service.files().list(pageSize=100, q=f"'{folder_id}' in parents", fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                recursive_download_folder(item['id'], product_id)
            else:
                request = drive_service.files().get_media(fileId=item['id'])
                fh = io.BytesIO()
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT google_id FROM product_images WHERE google_id = '{item['id']}'")
                    if cursor.fetchone() is None:
                        downloader = MediaIoBaseDownload(fh, request)
                        print(f"\tDownloading {item['id']}")
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                        file_content = fh.getvalue()
                        binary_content = psycopg2.Binary(file_content)
                        item['name']=item['name'].replace("'", "")
                        with conn.cursor() as cursor:
                            cursor.execute(f"INSERT INTO product_images (product_id, content, filename, google_id) VALUES ({product_id}, {binary_content}, '{item['name']}', '{item['id']}')")


for product in sheet["valueRanges"][0]['values']:
    if(len(product)<6):
        continue
    
    Lo = product[0].replace("'", "")
    product_type = product[1].replace("'", "")
    name = product[2].replace("'", "")
    price = product[3].replace("'", "")
    availability = product[5].replace("'", "")
    donor_site = ''
    
    folder_id = product[4].split("/")[-1].split("?")[0]
    if len(product)==7:
        donor_site = product[6]
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT id FROM products WHERE lo = '{Lo}' AND type = '{product_type}' AND name = '{name}'")
        existing_product = cursor.fetchone()
        if existing_product is None:
            cursor.execute(f"INSERT INTO products (lo, type, name, description, price, availability, donor_site) VALUES \
                        ('{Lo}', '{product_type}', '{name}', '{name}', {price}, '{availability}','{donor_site}') RETURNING id")
        else:
            cursor.execute(f"UPDATE products SET availability = '{availability}' WHERE id = {existing_product[0]} RETURNING id")
            print(f"Updating avialibility for {name}")
       
        product_id = cursor.fetchone()[0]
        recursive_download_folder(folder_id, product_id)