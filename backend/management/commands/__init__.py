import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from django.core.management.base import BaseCommand
from django.conf import settings

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class GoogleCommand(BaseCommand):

    def get_data(self, spreadsheet_id, spreadsheet_name):

        creds = None
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except OSError:
            pass

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GOOGLE_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=spreadsheet_name).execute()
        return result.get('values', [])
