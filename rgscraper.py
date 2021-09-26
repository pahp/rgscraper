#!/usr/bin/env python3
import shutil
import re
import os
import sys
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import csv
import time
import datetime

# used these references
# https://www.twilio.com/blog/2016/12/http-requests-in-python-3.html
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/


totalsongs = 0 # overall songs since beginning
startyear = 2016
endyear = datetime.datetime.now().year
startmonth = 1
endmonth = 12
base = "https://recordgroop218blog.wordpress.com"
cachedir = "cache"

def scrape_month(csvw, year, month):


    month = f"{month:02d}"
    

    url = base + "/" + str(year) + "/" + month

    print("Fetching: " + url)

    try:
        f = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        print(f"Fetch for URL {url} failed.")
        return

    html = f.read().decode('utf-8') # get the page as HTML

    # clean up the HTML
    # -----------------
    # something changed after 7/2019 so that items that used to be 
    # on their own line in the source HTML are now all on the same line
    # separated by <br> tags (Wordpress editor change, I guess).
    # BeautifulSoup pulls <br>s out anyway, and this script just expects
    # lines in the order:
    #   1. member
    #   2. "song" (in quotes)
    #   3. artist
    #   4. album
    # So: replace BRs with newlines to compensate for joined lines
    
    html = html.replace("<br>","\n")
    html = html.replace("</br>","\n")
    html = html.replace("<br />","\n")

    print(html)

    # run HTML through beautifulsoup
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text() # put the stuff from soup into a file

    print(text)
    
    lines_with_blanks = text.split("\n")

    # our fix from above results in some blank lines, which break up the
    # "member song record" (1-4 above). So, delete any blank lines from
    # 'lines'

    lines = []
    for line in lines_with_blanks:
        if line == "\n" or line == "":
            continue
        lines.append(line)

    print(lines)
    
    # dump the scrape sources to file for debugging

    cachepath = cachedir + "/" + str(year) + "-" + str(month)

    with open(cachepath, "w+") as cachefile:
        for line in lines:
            cachefile.write(line + "\n")
    cachefile.close()

    pat_find_session = re.compile("^Session (\d+): +(.+)")
    pat_find_host = re.compile("^Host: +(.+)")
    pat_find_date = re.compile("^Date: +(.+)")
    pat_find_loc = re.compile("^Location: +(.+)")
    pat_find_theme = re.compile("^Theme: +(.+)")
    pat_find_song = re.compile("^“([^”]+)”")
    pat_clean_member = re.compile("^ *(.+) *")

    alltimesong = 0
    session = 1
    host = 2
    date = 3
    loc = 4
    theme = 5
    member = 6
    sess_song = 7
    song = 8
    artist = 9
    album = 10
    row = []

    # set up empty row
    for i in range(12):
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
            print("Found session: " + row[session])


        # find the host
        match = re.search(pat_find_host, lines[num])
        if match:
            #print("Host change to: ", match.group(1))
            row[host] = match.group(1)
            print("Found host: " + row[host])

        # find the location
        match = re.search(pat_find_loc, lines[num])
        if match:
            #print("Location change to: ", match.group(1))
            row[loc] = match.group(1)
            print("Found host: " + row[host])

        # find the date
        match = re.search(pat_find_date, lines[num])
        if match:
            #print("Date change to: ", match.group(1))
            row[date] = match.group(1)
            print("Found date: " + row[date])

        # find the theme
        match = re.search(pat_find_theme, lines[num])
        if match:
            #print("Theme change to: ", match.group(1))
            row[theme] = match.group(1)
            print("Found theme: " + row[theme])

        # i considered matching member names, but in some cases, we have
        # had guests come to RG, and they would not be found. So
        # instead, I'm going to try to match on a song title, which
        # seems to always start with double quotes, then I'll back up a
        # line to find the attendee who played the song

        # find the theme
        match = re.search(pat_find_song, lines[num])
        if match:
            row[song] = match.group(1)
            print("Found song: " + row[song])
            session_song = session_song + 1 # we found a new song
            row[sess_song] = session_song
           
            global totalsongs
            totalsongs = totalsongs + 1
            row[alltimesong] = totalsongs
            
            print("Found overall song: %d (session song: %d)" % (row[alltimesong], row[sess_song]))
            match = re.search(pat_clean_member, lines[num - 1])
            row[member] = match.group(1)

            print("Found member: " + row[member])
            num = num + 1
            row[artist] = lines[num]
            print("Found artist: " + row[artist])
            num = num + 1
            row[album] = lines[num]
            print("Found album: " + row[album])

            csvw.writerow(row)

            row[alltimesong] = ""
            row[member] = ""
            row[song] = ""
            row[artist] = ""
            row[album] = ""
            row[sess_song] = ""

def main():


    # delete and recreate cachedir if exists
    if os.path.exists(cachedir):
        try:
            shutil.rmtree(cachedir)
        except:
            print("Couldn't remove %s." % (cachedir))
            sys.exit(1)
    if not os.path.exists(cachedir):
        try:
            os.mkdir(cachedir, mode = 0o775)
        except:
            print("Couldn't create %s." % (cachedir))
            sys.exit(2)


    header=["rgsong", "session", "host", "date", "loc", "theme",
            "member", "sess_song", "song", "artist", "album"]

    if len(sys.argv) < 2:
        sys.stderr.write("No output file specified.\n")
        sys.stderr.write("./rgscraper.py OUTPUTFILE\n")
        sys.exit(1)



    with open(sys.argv[1], 'w', newline='\n') as csvfile:
        csvw = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        csvw.writerow(header)

        for year in range(startyear, endyear + 1):
            for month in range(startmonth, endmonth + 1):
                scrape_month(csvw, year, month)
                time.sleep(1)



if __name__ == '__main__':
    main()
