"""
This script checks a google analytics account for the top pages visited,
and then updates a json file in a github repo with the results.
It is intended to be run about once per day.
"""
import os
import sys
import io
import urllib.parse as urlparse
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
PROTOCOL = 'http'
HOST = 'roadmap.rootandrebound.org'
BASE_DOMAIN = '{}://{}'.format(PROTOCOL, HOST)

SEARCH_PAGE_TITLE_TEMPLATE = 'Search results for “{}”'


def is_valid_top_page(page):
    path = page['url'].replace('roadmap-to-html/','')
    url = BASE_DOMAIN + path
    response = requests.get(url)
    is_valid = response.status_code == 200
    print("Checking: '{}' ... {}".format(path, is_valid))
    return is_valid


def modify_titles_for_search_pages(pages):
    for page in pages:
        params = urlparse.parse_qs(urlparse.urlparse(page['url']).query)
        if 'q' in params:
            page['title'] = SEARCH_PAGE_TITLE_TEMPLATE.format(params['q'][0])


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


def filter_to_valid_pages_only(pages):
    return [
        page for page in pages
        if is_valid_top_page(page)
    ]



def main(days_ago='30'):
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
    print(
        "Requesting list of most visited pages for past {} days".format(
            days_ago))
    start_date = '{}daysAgo'.format(days_ago)
    report_params = {
        'viewId': VIEW_ID,
        'dateRanges': [{'startDate': start_date, 'endDate': 'today'}],
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
        for row in response['reports'][0]['data']['rows'][:20]]
    print("Received new list of top pages")
    valid_top_pages = filter_to_valid_pages_only(top_pages)
    invalid_pages = [
        page for page in top_pages
        if page not in valid_top_pages
    ]
    modify_titles_for_search_pages(valid_top_pages)
    print("\nRESULTS: {} valid, {} invalid".format(
        len(valid_top_pages), len(top_pages) - len(valid_top_pages)))
    print("\nVALID:")
    pprint(valid_top_pages)
    print("\nINVALID:")
    pprint(invalid_pages)
    top_pages_json = json.dumps(valid_top_pages)
    top_pages_json_bytes = top_pages_json.encode('utf-8')
    json_file = io.BytesIO(top_pages_json_bytes)
    print("Saving top pages to '{}'".format(JSON_FILE_NAME))
    s3.upload_fileobj(json_file, S3_BUCKET_NAME, JSON_FILE_NAME)
    print("Allowing public access to '{}'".format(JSON_FILE_NAME))
    s3.put_object_acl(
        ACL='public-read', Bucket=S3_BUCKET_NAME, Key=JSON_FILE_NAME)
    print("Complete.")

if __name__ == '__main__':
    args = sys.argv
    day_count = '30'
    if len(args) > 1:
        day_count = args[1]
    main(days_ago=day_count)
