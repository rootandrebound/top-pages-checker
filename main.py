"""
This script checks a google analytics account for the top pages visited,
and then updates a json file in a github repo with the results.
It is intended to be run about once per day.
"""
import os
import io
import requests
import json
from pprint import pprint
import honcho
import boto3
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
VIEW_ID = '154632053'
GOOGLE_API_JSON = os.environ.get("GOOGLE_API_JSON")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
JSON_FILE_NAME = 'top_pages.json'
NUMBER_OF_TOP_PAGES = 10


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


def parse_top_page(raw_ga_dict):
    title, url = raw_ga_dict['dimensions']
    return dict(
        url=url,
        title=title.replace(' - Roadmap to Reentry', ''))


def main():
    # create bucket if it doesnt exist
    print("Initializing connection to Amazon S3")
    s3 = boto3.client('s3')
    print("Ensuring that s3 bucket '{}' exists".format(S3_BUCKET_NAME))
    bucket_exists = S3_BUCKET_NAME in [
        bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
    if not bucket_exists:
        print("Creating s3 bucket '{}'".format(S3_BUCKET_NAME))
        s3.create_bucket(Bucket=S3_BUCKET_NAME)
    print("Connecting to Google Analytics Core Reporting API")
    google_api_credentials = json.loads(
        GOOGLE_API_JSON.translate(str.maketrans({"\n": r"\n"})))
    analytics = initialize_analyticsreporting(google_api_credentials)
    print("Requesting list of most visited pages")
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
    top_pages = [
        parse_top_page(row)
        for row in response['reports'][0]['data']['rows'][:10]]
    print("Received new list of top pages:")
    pprint(top_pages)
    top_pages_json = json.dumps(top_pages)
    top_pages_json_bytes = top_pages_json.encode('utf-8')
    json_file = io.BytesIO(top_pages_json_bytes)
    print("Saving top pages to '{}'".format(JSON_FILE_NAME))
    s3.upload_fileobj(json_file, S3_BUCKET_NAME, JSON_FILE_NAME)
    print("Allowing public access to '{}'".format(JSON_FILE_NAME))
    s3.put_object_acl(
        ACL='public-read', Bucket=S3_BUCKET_NAME, Key=JSON_FILE_NAME)
    print("Complete.")

if __name__ == '__main__':
    main()
