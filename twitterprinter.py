# -*- coding: utf-8 -*-

# CBM 231 social microprinter
# First version - this is hacky as anything, please forgive the mess, it'll get cleaned up...
# Git homepage:       https://github.com/ianozsvald/SocialMicroprinter
# Full write-up:      XXX
# Uses (thanks Ben!): https://github.com/benosteen/microprinter

import datetime
import os
import cPickle
import microprinter
#import microprinter_image # only if we're printing images
import time
# Would be nice to add a reason for a barcode...
#m.printUPCABarcode('012345678910')
#m.flush()


import urllib2
import twitter # http://mike.verdone.ca/twitter/ v1.4.2

"""search twitter for a term on cmd line, store in tweets.pickle"""

search_term = "theskiff"
#search_term = "fivepoundapp"
#search_term = "#sfriot"

tw_search = twitter.Twitter(domain="search.twitter.com")



NBR_TWEETS_TO_PRINT = 7 # max nbr of tweets to print

# set PRINT to True if we're printing via serial
PRINT = True 
m = None # m is the microprinter object
#if PRINT:
#    # /dev/cu.usbserial mac with PL2303 cable
#    # /dev/ttyUSB0 on Ubuntu
#    m = microprinter.Microprinter('/dev/cu.usbserial', 19200)

# note to self - redundant writing to file! clean up old modular code...
def get_tweets(search_term):
    search_results = None
    try:
        search_results = tw_search.search(q=search_term, rpp=100, page=1)['results']
    except urllib2.URLError, e:
        # sometimes twitter times out, here we catch it and ignore it
        print str(e)
    if search_results is not None:
        cPickle.dump(search_results, file('/home/ianozsvald/webapps/app_microprinter/tweets.pickle', 'w'))


def load_tweets():
    search_results = cPickle.load(file('/home/ianozsvald/webapps/app_microprinter/tweets.pickle', 'r'))
    timeline = []
    for result in search_results:
        tweet = (result['from_user'], result['text'])
        timeline.append(tweet)
    return timeline

def word_wrap_lines(txt, screen_name):
    """word wrap a 140 char txt, return a set of lines <48 chars each"""
    lines = []

    #print "----entering wordwrap", txt
    if True:
        linelen = 48
        linest = 0 
        lineend = linelen - len(screen_name) - 1
        while True:
            #print linest, lineend
            #time.sleep(1)
            # if the start of the string has a spc, we jump it for new line
            if linest+1 < len(txt):
                if txt[linest] == ' ':
                    linest += 1
            line= txt[linest:lineend]
            if lineend < len(txt):
                last_spc = line.rfind(' ') 
                if last_spc > -1:
                    lineend = last_spc + linest # find last right space 
                #print "lineend", last_spc
            line = txt[linest:lineend]
            #print line
            if linest >= len(txt):
                break
            lines.append(line.strip())

            linest = lineend
            lineend = linest + linelen
    #print "----done wordwrap"
    return lines

def print_some_tweets(timeline):
    """print a header (with img), tweets, footer"""

    # first remove our uploading file
    if os.path.exists(microprinter.index_filename):
        os.remove(microprinter.index_filename)
    global m
    m = microprinter.Microprinter('/dev/cu.usbserial', 19200)
    m.write("--------------")

    if PRINT:
        # we *could* print an image but on the CBM 231 it is all about the guesswork
        # mode 0 seems to work (most don't)
        # width 300 seems to work
        # 430x115 TIFF image worked fine (JPG variant didn't)
	#microprinter_image.print_image_from_file('430x115_img.tiff', 300, 0, m, autorotate=False, dither=True)
        # at 290 it prints oddly (with broken white horizontal lines), at 291 it has 1 pixel off the
        # right edge of the paper but otherwise prints fine, at 300 it has (maybe?) 10 px off the right of the paper
        #microprinter_image.print_image_from_file('logo.tiff', 291, 0, m, autorotate=False, dither=True)
        #print "IMG SENT"
        m.setDoubleprint(True)
        m.write("Twitter microprinter - Tweet with \n'fivepoundapp' to appear here\n")
        m.setDoubleprint(False)
        now = datetime.datetime.now()
        m.write(str(now) + '\n\n')

    # print tweets
    for screen_name, txt in timeline[:NBR_TWEETS_TO_PRINT]:
        txt = txt.replace('\n', ' ') 
        txt = txt.replace('&amp;', '&')
        txt = txt.replace('&lt;', '<')
        txt = txt.replace('&gt;', '>')
        txt = txt.replace('&quot;', '"')
        txt = str(txt.encode('ascii', 'replace'))

        lines = word_wrap_lines(txt, screen_name)
        print lines # print the lines for debugging

        if PRINT:
            m.setDoubleprint(True)
            m.write(str(screen_name) + ' ')
            m.setDoubleprint(False)
            for line in lines:
                m.write(line+'\n')
            m.setUnderline(True)
            m.write('                                               \n')
            m.setUnderline(False)

    if PRINT:
        # hardcoded list of events, this needs to come from a feed
        m.write("\nEvents via lanyrd.com/places/13911:\n")
        m.write("BuildBrighton normal evening   4th Oct\n")
        m.write("openMIC mobile innovation camp 4th Oct\n")
        m.write("FullFrontal JS Conf            12th Oct\n")
        m.write("Web 2.0 and Social Media Conf  16th Oct\n\n")
        m.write("For:  theSkiff.org\n")
        m.write("By:   @ianozsvald & @mattweston\n")
        m.write("Attr: @benosteen & @tomtaylor\n")
        m.write("Do tweet '@lanyrd attending fivepoundapp'\n")
        m.write("I want feedback pls! ian@ianozsvald.com\n")
        #m.feed(3)
        #m.cut()
        m.write("END OF MESSAGE--------------")

if __name__ == "__main__":
    print "Twitter microprinter",
    if PRINT:
        print "- printer online"
    else:
        print "- printer offline"
    print "--------"

    print "getting...", search_term
    get_tweets(search_term)
    timeline = load_tweets()
    print_some_tweets(timeline)
