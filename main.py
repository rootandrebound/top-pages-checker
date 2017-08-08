"""
This script checks a google analytics account for the top pages visited,
and then updates a json file in a github repo with the results.
It is intended to be run about once per day.
"""
import os
import requests


def main():
    # connect to google analytics reporter API
    print("Connecting to Google Analytics Core Reporting API")
    # pull report
    print("Pulling information about most visited pages")
    # connect to github
    print("Connecting to github")
    # write a file??
    print("Overwriting contents of 'output/js/top_pages.json'")
    pass



if __name__ == '__main__':
    main()