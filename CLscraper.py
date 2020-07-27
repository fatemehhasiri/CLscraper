#!/usr/bin/python

"""
Forked from : Bobak Hashemi on 21/08/2020

This program takes in a list of craigslist search queries (given by the search links with GET data), 
indexes the results for each query, and emails new posts to a set of specified email addresses.
 """

import urllib
import datetime
from bs4 import BeautifulSoup
import time
import smtplib
import json
import sys
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
import random
from configparser import ConfigParser


DEFAULT_SLEEP_INTERVAL = [60, 80]

if len(sys.argv) > 1:
    CONFIG_FILE = str(sys.argv[1])
    RESULT_FILE = CONFIG_FILE.replace('.ini', '_results.txt')
else:
    print("No config file name were passed as argument. Exiting...")
    exit(1)

config = ConfigParser()
conf = {}
email = []  # Initialize list of posting's to be emailed after some run.


def load_config(conf, config):
    config.read(CONFIG_FILE)
    conf["smtp_server"] = config.get("CLscraper", "smtp_server").strip()
    conf["smtp_username"] = config.get("CLscraper", "smtp_username").strip()
    conf["smtp_password"] = config.get("CLscraper", "smtp_password").strip()
    conf["fromaddr"] = config.get("CLscraper", "fromaddr").strip()
    conf["toaddrs"] = json.loads(config.get("CLscraper", "toaddrs"))
    conf["urls"] = json.loads(config.get("CLscraper", "urls"))
    conf['exclude'] = json.loads(config.get("CLscraper", "exclude"))
    sleepinterval = json.loads(config.get("CLscraper", "sleeptime"))

    if sleepinterval[1] < sleepinterval[0]:
        print("Sleep interval %s is not well formed, second number must be larger than the first. Using default interval" % str(sleepinterval))
        sleepinterval = DEFAULT_SLEEP_INTERVAL

    # Number of seconds between searches
    conf["sleeptime"] = random.randint(60*sleepinterval[0], 60*sleepinterval[1])


def read_old_listings(result_file=RESULT_FILE):
    old_listings = []
    with open(result_file, 'r') as f:
        for line in f:
            id = line[:-1]
            old_listings.append(id)
    return old_listings


def append_listings(new_listings, result_file=RESULT_FILE):
    with open(result_file, 'a') as f:
        for item in new_listings:
            f.write("%s\n" % item)


def constructMessage(new_listings):
    subject =  'Subject: New Matches on Craigslist Search "' + CONFIG_FILE + '" \n\n' 
    header = 'New postings for search "' + CONFIG_FILE + '" : \n\n'
    msg = ''
    for pid in new_listings.keys():
        msg = msg + new_listings[pid][0] + " : " + new_listings[pid][1] + "\n"
    details = '\n Details on search configuration : \n' + '\tList of urls : \n'
    for url in conf['urls']:
        details = details + '\t\t' + url + '\n'
    details = details + '\t Word based exclusions : "' + '", "'.join(conf['exclude']) + '" \n'
    return subject + header +  msg + details


def getListOfIdsAndUrls():
    """Scrapes the web pages for listings and returns a dictionary with PIDs as keys and (URLs, title) as value for stuff not in old_listings"""
    new_listings = {}  # dictionary which holds the unique ID for each listing and the URL.
    old_listings = read_old_listings()
    listings_to_save = []

    for craigslistLinkAddress in conf["urls"]:
        f = urlopen(craigslistLinkAddress)  # Open Web Address

        # read in html into BS4 data structure
        soup = BeautifulSoup(f.read(), "html.parser")

        # Get the body of the search, strips away all the sidebars and stuff.
        content = soup.find(id="sortable-results")

        # For each listing, find the listings by searching for results table elements. This tag also stores a unique ID for each listing
        for listing in content.find_all("li", {"class": "result-row"}):
            date = datetime.datetime.strptime(listing.find('time').attrs['datetime'], '%Y-%m-%d %H:%M')
            #keeping post from last 24h only
            if date + datetime.timedelta(hours = 24) > datetime.datetime.now():
                # finds the listing title
                title = listing.find("a", {"class": "result-title"}).text
                ignore = False
                for word in conf['exclude']:
                    if word.lower() in title.lower():
                        ignore = True
                if not ignore:
                    pid = listing.attrs["data-pid"]
                    # finds the link by looking for a link with results-title class and extracts the url.
                    url = listing.find("a", {"class": "result-title"}).attrs["href"]
                    # check if listing is in the old list
                    if pid not in old_listings:
                        new_listings[pid] = (url, title)  # listing should be returned
                        # add the new pid to list of ones we've seen
                        listings_to_save.append(pid)

    append_listings(listings_to_save)

    return new_listings


def doIteration():
    new_listings = getListOfIdsAndUrls()

    if new_listings:
        msg = constructMessage(new_listings)
        print('Found new listings, sending email')
        server = smtplib.SMTP(conf["smtp_server"])
        server.starttls()
        if conf["smtp_username"]:
            server.login(conf["smtp_username"], conf["smtp_password"])
        server.sendmail(conf["fromaddr"], conf["toaddrs"], msg.encode('utf-8'))
        server.quit()
    else:
        print("No new listings found")


append_listings([])
while True:
    load_config(conf, config)
    # Print timestamp to terminal so you know it's working
    print("\n\n "+str(datetime.datetime.now())+":  --Checking!-- \n\n")
    doIteration()
    # re-initialize list of new posts and new post flag and wait sleeptime seconds before starting again
    email = []
    new = False
    time.sleep(conf["sleeptime"])