# Gmail manager
This is a simple gmail manager (download and bulk delete), using the Gmail API.
A small enhancement from quickstart on [official Gmail API Quickstart](https://developers.google.com/gmail/api/quickstart/python). 

This code would allow you to download all your emails from Gmail to csv files.
Included in this codebase:
1. Download all emails from Gmail per-label (INBOX, filter labels, etc.) to CSV files.
Download information about your emails to CVS files so that you can easily manage and filter them in spreadsheets and bulk-delete them.

2. Bulk delete emails in Gmail from a file
After applying some filtering on the CVS, copy them to a new file which you can submit and request bulk-delete in Gmail.

## Prerequisites
You will need the following pre-requisites:
1. Python 3.6 or later
2. PIP
3. A Google Platform account (You can use free trial):
   See the [pre-requisites steps document here](https://developers.google.com/gmail/api/quickstart/python)
   1. A [Google Cloud Platform project](https://developers.google.com/workspace/guides/create-project) with the API enabled. 
   2. Set up authorization credentials for a desktop application.
   3. A Google account with Gmail enabled.
    
## Installation
Install the required libraries:

```pip install -r requirements.txt```

**Note:** You can use virtual environment to install the required libraries.

## Execution
Run the program:

```python email_fetcher.py```
