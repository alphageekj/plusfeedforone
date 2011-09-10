#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import logging
import pycurl
import StringIO
import os
import codecs

import simplejson as json

from cgi import escape
from datetime import datetime
from datetime import timedelta
from time import mktime
from time import sleep
from htmlentitydefs import name2codepoint
from os import environ

allurls = re.compile(r'/(.*)')
idurls = re.compile(r'[0-9]+')
commas = re.compile(',,',re.M)
se_break = re.compile('[.!?:]\s+', re.VERBOSE)

HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"
ATOM_DATE = "%Y-%m-%dT%H:%M:%SZ"

# this is the only thing to change - put in your Google Plus profile number to replace the ##########'s
p = "#####################"

myuri = os.environ['SCRIPT_URI']
url = "https://plus.google.com/_/stream/getactivities/?&sp=[1,2,\"" + p + "\",null,null,10,null,\"social.google.com\",[]]"

def htmldecode(text):
	if type(text) is unicode:
		uchr = unichr

	else:
		uchr = lambda value: value > 255 and unichr(value) or chr(value)

	def entitydecode(match, uchr=uchr):
		entity = match.group(1)
		if entity.startswith('#x'):
			return uchr(int(entity[2:], 16))
		elif entity.startswith('#'):
			return uchr(int(entity[1:]))
		elif entity in name2codepoint:
			return uchr(name2codepoint[entity])
		else:
			return match.group(0)
	charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
	return charrefpat.sub(entitydecode, text)

c = pycurl.Curl()
c.setopt(pycurl.URL, url)
c.setopt(pycurl.HTTPHEADER, ["Accept:"])
b = StringIO.StringIO()
c.setopt(pycurl.WRITEFUNCTION, b.write)
c.setopt(pycurl.FOLLOWLOCATION, 1)
c.setopt(pycurl.MAXREDIRS, 5)
c.perform()
txt = unicode(b.getvalue(), errors='ignore')

txt = txt[5:]
txt = commas.sub(',null,',txt)
txt = commas.sub(',null,',txt)
txt = txt.replace('[,','[null,')
txt = txt.replace(',]',',null]')
obj = json.loads(txt)

posts = obj[1][0]

author = posts[0][3]
authorimg = 'https:' + posts[0][18]
updated = datetime.fromtimestamp(float(posts[0][5])/1000)

feed = '<?xml version="1.0" encoding="UTF-8"?>\n'
feed += '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">\n'
feed += '<title>' + author + ' - Google+ User Feed</title>\n'
feed += '<link href="https://plus.google.com/' + p + '" rel="alternate"></link>\n'
feed += '<link href="' + myuri + '" rel="self"></link>\n'
feed += '<id>https://plus.google.com/' + p + '</id>\n'
feed += '<updated>' + updated.strftime(ATOM_DATE) + '</updated>\n'
feed += '<author><name>' + author + '</name></author>\n'

count = 0
			
for post in posts:
				
	count = count + 1
	if count > 10:
		break
				
				
	dt = datetime.fromtimestamp(float(post[5])/1000)
	id = post[21]
	permalink = "https://plus.google.com/" + post[21]
				
	desc = ''
				
	if post[47]:
		desc = post[47]					
	elif post[4]:
		desc = post[4]
				
	if post[44]:
		desc = desc + ' <br/><br/><a href="https://plus.google.com/' + post[44][1] + '">' + post[44][0] + '</a> originally shared this post: ';
				
	if post[66]:
				
		if post[66][0][1]:						
			desc = desc + ' <br/><br/><a href="' + post[66][0][1] + '">' + post[66][0][3] + '</a>'
						
		if post[66][0][6]:
			if post[66][0][6][0][1].find('image') > -1:
				desc = desc + ' <p><img src="http:' + post[66][0][6][0][2] + '"/></p>'
			else:
				try:
					desc = desc + ' <a href="' + post[66][0][6][0][8] + '">' + post[66][0][6][0][8] + '</a>'
				except:
					sys.exc_clear()
									
	if desc == '':
		desc = permalink

	ptitle = htmldecode(desc)
	ptitle = re.sub('<.*?>', ' ', ptitle)
	ptitle = re.sub('\s+', ' ', ptitle)
												
	sentend = 75
												
	m = se_break.split(ptitle)
	if m:
		sentend = len(m[0]) + 1

	if sentend < 5 or sentend > 75:
		sentend = 75
	
	feed += '<entry>\n'
	feed += '<title>' + escape(ptitle[:sentend]) + '</title>\n'
	feed += '<link href="' + permalink + '" rel="alternate"></link>\n'
	feed += '<updated>' + dt.strftime(ATOM_DATE) + '</updated>\n'
	feed += '<id>tag:plus.google.com,' + dt.strftime('%Y-%m-%d') + ':/' + id + '/</id>\n'
	feed += '<summary type="html">' + escape(desc) + '</summary>\n'
	feed += '</entry>\n'
	
feed += '</feed>\n'
	
print 'Last-Modified: ' + updated.strftime(HTTP_DATE_FMT)
print "Content-Type: application/atom+xml\n"

ufeed=unicode(feed)

print ufeed.encode()

