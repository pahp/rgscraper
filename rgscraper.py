#!/usr/bin/env python3
import re
import os
import sys
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import csv

# used these references
# https://www.twilio.com/blog/2016/12/http-requests-in-python-3.html
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/

base = "https://recordgroop218blog.wordpress.com/"

def scrape_month(csvw, year, month):


    month = f"{month:02d}"

    url = base + str(year) + "/" + month

    print("Fetching: " + url)

    try:
        f = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        print(f"Fetch for URL {url} failed.")
        return

    soup = BeautifulSoup(f.read().decode('utf-8'), 'html.parser')
    lines = soup.get_text().split("\n")

    pat_find_session = re.compile("^Session (\d+): (.+)")
    pat_find_host = re.compile("^Host: (.+)")
    pat_find_date = re.compile("^Date: (.+)")
    pat_find_loc = re.compile("^Location: (.+)")
    pat_find_theme = re.compile("^Theme: (.+)")
    pat_find_song = re.compile("^“([^”]+)”")

    session = 0
    host = 1
    date = 2
    loc = 3
    theme = 4
    member = 5
    song = 6
    songnum = 7
    artist = 8
    album = 9
    row = []

    # set up empty row
    for i in range(10):
        row.append("")



    for num in range(len(lines)):

        # find the session and title
        match = re.search(pat_find_session, lines[num])
        if match:
            #print("Session change to: ", match.group(1), " / ", match.group(2))
            row[session] = match.group(1)
            session_song = 0 # reset the session song count
            row[host] = ""
            row[date] = ""
            row[theme] = ""

        # find the host
        match = re.search(pat_find_host, lines[num])
        if match:
            #print("Host change to: ", match.group(1))
            row[host] = match.group(1)

        # find the location
        match = re.search(pat_find_loc, lines[num])
        if match:
            #print("Location change to: ", match.group(1))
            row[loc] = match.group(1)

        # find the date
        match = re.search(pat_find_date, lines[num])
        if match:
            #print("Date change to: ", match.group(1))
            row[date] = match.group(1)

        # find the theme
        match = re.search(pat_find_theme, lines[num])
        if match:
            #print("Theme change to: ", match.group(1))
            row[theme] = match.group(1)

        # i considered matching member names, but in some cases, we have
        # had guests come to RG, and they would not be found. So
        # instead, I'm going to try to match on a song title, which
        # seems to always start with double quotes, then I'll back up a
        # line to find the attendee who played the song

        # find the theme
        match = re.search(pat_find_song, lines[num])
        if match:
            row[song] = match.group(1)
            session_song = session_song + 1 # we found a new song
            row[songnum] = session_song

            row[member] = lines[num - 1]
            num = num + 1
            row[artist] = lines[num]
            num = num + 1
            row[album] = lines[num]

            csvw.writerow(row)

            row[member] = ""
            row[song] = ""
            row[artist] = ""
            row[album] = ""
            row[songnum] = ""

def main():

    header=["session", "host", "date", "loc", "theme",
            "member", "song", "songnum", "artist", "album"]

    with open(sys.argv[1], 'w', newline='\n') as csvfile:
        csvw = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        csvw.writerow(header)

        for year in range(2016,2020):
            for month in range(1, 13):
                scrape_month(csvw, year, month)


if __name__ == '__main__':
    main()
