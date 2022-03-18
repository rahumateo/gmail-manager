from __future__ import print_function

import csv
import glob
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from halo import Halo
from math import ceil
from time import sleep, time
from utils import print_progress_bar, timestamp_pretty

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']
EMAIL_LABELS = []
EMAIL_FETCH_BATH_SIZE = 50
EMAIL_DELETE_BATCH_SIZE = 25
spinner = Halo(spinner='triangle', interval=300)


def main():
    try:
        main_menu()
    except HttpError as error:
        print(f'An error occurred: {error}')


def get_credentials():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def init_service():
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    return service


def main_menu(service=None):
    """
        Capabilities:
        1. Get labels
        2. Get emails with a label and write to a csv file
        3. Delete emails from a file (containing message IDs)
    """
    print("""
    Menu:
    [1] Get labels
    [2] Get emails of a label
    [3] Delete emails
    [0] Exit
    """)
    selection = input("Select an option (typing in the number then hit enter): ")

    # init the API
    if service is None:
        service = init_service()
    options = {
        '1': get_label_menu,
        '2': get_emails_menu,
        '3': delete_messages_menu
    }
    print(f'\nSelected option: {selection}')
    if selection == '0':
        exit()
    options[selection](service)


# 1. Get Labels
def get_label_menu(service, redirect_to_main_menu=True):
    email_labels = _do_get_labels(service)
    print('Labels:')
    for index, item in enumerate(email_labels):
        print(f'[{index}] - {item[1]}')
    if redirect_to_main_menu:
        main_menu()
    else:
        return email_labels


# 2. Get Emails -- and write to a csv file
def get_emails_menu(service, redirect_to_main_menu=True):
    email_labels = get_label_menu(service, redirect_to_main_menu=False)
    selection = input("\nSelect a label (typing in the number then hit enter): ")
    print(f'\nSelected option: {selection}')
    label = email_labels[int(selection)]
    file_name = get_label_file_name(label).replace('/', '_')
    get_emails(service, label[0], file_name)
    if redirect_to_main_menu:
        main_menu()


def get_emails(service, label_id, file_name):
    start_time = time()
    print(f'[{timestamp_pretty(start_time)}] Downloading emails from label: {file_name}')
    file_path = f'files/get-emails/{file_name}.csv'

    label_info = _do_get_label_info(service, label_id)
    email_count = label_info['messagesTotal']
    if email_count == 0:
        print('There are no emails in this label.')
        return
    page_token = 0
    emails = []
    iteration = 0
    total_iteration = int(ceil(email_count / EMAIL_FETCH_BATH_SIZE))
    print_progress_bar(iteration, total_iteration, prefix='Downloading:',
                       suffix=f'Complete ({len(emails)}/{email_count})', length=50)
    while page_token is not None:
        fetched, page_token = _do_get_emails(service, [label_id], EMAIL_FETCH_BATH_SIZE, page_token)
        write_emails_to_csv(file_path=file_path, emails=fetched)
        emails.extend(fetched)
        iteration += 1
        print_progress_bar(iteration, total_iteration, prefix='Downloading:',
                           suffix=f'Complete ({len(emails)}/{email_count})',
                           elapsed_second=int((time() - start_time)), length=50)
        sleep(0.2)
    print(f'[{timestamp_pretty(time())}] Done! Emails data stored in {file_path}.')


# 3. Delete Emails
def delete_messages_menu(service, redirect_to_main_menu=True):
    to_delete_files = get_to_delete_file_names()
    for index, file_name in enumerate(to_delete_files):
        print(f'[{index}] - {file_name}')

    file_name = input("\nSelect the file number: ")
    print(f'\nSelected option: {to_delete_files[int(file_name)]}\n')
    delete_messages(service, to_delete_files[int(file_name)])
    if redirect_to_main_menu:
        main_menu()


# -----------
def delete_messages(service, file_name):
    start_time = time()
    print(f'[{timestamp_pretty(start_time)}] Deleting messages in file {file_name}')
    file_row_count = sum(1 for _ in open(file_name))
    if file_row_count == 0:
        print('There are no email ids in this file.')
        return
    messages_count = 0
    iteration = 0
    total_iteration = int(ceil(file_row_count / EMAIL_DELETE_BATCH_SIZE))
    print_progress_bar(iteration, total_iteration, prefix='Deleting:',
                       suffix=f'Complete ({messages_count}/{file_row_count})', length=50)
    for curr_batch in read_file_with_batch_line(file_name, EMAIL_DELETE_BATCH_SIZE):
        _do_delete_messages(service, curr_batch)
        messages_count += len(curr_batch)
        iteration += 1
        print_progress_bar(iteration, total_iteration, prefix='Deleting:',
                           suffix=f'Complete ({messages_count}/{file_row_count})',
                           elapsed_second=int((time() - start_time)), length=50)
        sleep(1)
    print(f'[{timestamp_pretty(time())}] Finished deleting {messages_count} messages')


def read_file_with_batch_line(file_name, batch_size):
    rows = []
    for row in open(file_name, 'r'):
        if len(rows) == batch_size:
            yield rows
            rows = []
        id = row.split('\t')[0].rstrip()
        id = id.split(',')[0].rstrip()
        rows.append(id)
    yield rows


# Helpers
def get_label_file_name(label):
    if label[0] == label[1]:
        return label[0]
    return f"{label[0]}-{label[1]}"


def write_emails_to_csv(file_path, emails):
    with open(file_path, 'a', newline='') as csvfile:
        fieldnames = ['id', 'date', 'from', 'subject']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for email in emails:
            writer.writerow(email)


def construct_message_data(message_id, message):
    headers = message['payload']['headers']
    message_data = {
        'id': message_id
    }
    for header in headers:
        if header['name'] == 'Subject':
            message_data['subject'] = header['value'].replace(',', ' ')
        elif header['name'] == 'From' or header['name'] == 'from':
            message_data['from'] = header['value'].replace(',', ' ')
        elif header['name'] == 'Date':
            message_data['date'] = header['value'].replace(',', ' ')
    return message_data


def get_to_delete_file_names():
    csv_files = []
    for file in glob.glob("files/to-delete/*.csv"):
        csv_files.append(file)
    return csv_files


# API calls
def _do_get_labels(service):
    try:
        spinner.start(text='Getting labels')
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        spinner.stop()

        if not labels:
            print('No labels found.')
            return []
        return [(label["id"], label["name"]) for label in labels]
    except HttpError as error:
        print(f'An error occurred: {error}')


def _do_get_label_info(service, label_id):
    try:
        spinner.start(text='')
        results = service.users().labels().get(userId='me', id=label_id).execute()
        spinner.stop()
        return results
    except HttpError as error:
        print(f'An error occurred: {error}')


def _do_get_emails(service, label_ids, max_results, page_token):
    """
    Get emails from Gmail API
    """
    try:
        # Call the Gmail API
        results = service.users().messages().list(userId='me', labelIds=label_ids,
                                                  maxResults=max_results, pageToken=page_token).execute()
        messages = results.get('messages', [])

        if len(messages) == 0:
            print('No messages found.')
            return
        result = []
        for message in messages:
            result.append(_do_get_email(service, message['id']))
            sleep(1)
        return result, results.get('nextPageToken', None)
    except HttpError as error:
        print(f'An error occurred: {error}')


def _do_get_email(service, message_id):
    """
    Get email from Gmail API
    """
    try:
        # Call the Gmail API
        message = service.users().messages().get(userId='me', id=message_id).execute()
        message_data = construct_message_data(message_id, message)
        return message_data
    except HttpError as error:
        print(f'An error occurred: {error}')


def _do_delete_messages(service, message_ids):
    """
    Delete email from Gmail API
    """
    try:
        # Call the Gmail API
        body = {'ids': message_ids}
        service.users().messages().batchDelete(userId='me', body=body).execute()
    except HttpError as error:
        print(f'An error occurred: {error}')


def trash_messages(service, message_ids):
    """
    Delete email from Gmail API
    """
    try:
        # Call the Gmail API
        for message_id in message_ids:
            result = service.users().messages().trash(userId='me', id=message_id).execute()
            print(result)
    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
