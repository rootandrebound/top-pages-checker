"""
This script checks a google analytics account for the top pages visited,
and then updates a json file in a github repo with the results.
It is intended to be run about once per day.
"""
import os
import requests
import json
from pprint import pprint
import honcho
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
VIEW_ID = '154632053'


def initialize_analyticsreporting(api_json_data):
  """Initializes an Analytics Reporting API V4 service object.

  Returns:
    An authorized Analytics Reporting API V4 service object.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_dict(
      api_json_data, SCOPES)
  # Build the service object.
  analytics = build('analyticsreporting', 'v4', credentials=credentials)
  return analytics

def main():
    GOOGLE_API_JSON = os.environ.get("GOOGLE_API_JSON")
    google_api_credentials = json.loads(
        GOOGLE_API_JSON.translate(str.maketrans({"\n": r"\n"})))
    # connect to google analytics reporter API
    print("Connecting to Google Analytics Core Reporting API")
    # import ipdb; ipdb.set_trace()
    analytics = initialize_analyticsreporting(google_api_credentials)
    # pull report
    print("Pulling information about most visited pages")
    report_params = {
        'viewId': VIEW_ID,
        'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
        'metrics': [
            {'expression': 'ga:pageviews'},
            {'expression': 'ga:uniquePageviews'}
        ],
        'dimensions': [
            {'name': 'ga:pageTitle'},
            {'name': 'ga:pagePath'},
        ],
        "orderBys": [
            {"fieldName": "ga:pageviews", "sortOrder": "DESCENDING"}]
    }
    response = analytics.reports().batchGet(
      body={'reportRequests': [report_params]}).execute()
    pprint(response)
    # print_response(response)
    # connect to github
    print("Connecting to github")
    # write a file??
    print("Overwriting contents of 'output/js/top_pages.json'")


if __name__ == '__main__':
    main()
