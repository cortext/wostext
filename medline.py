#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WOS.
Description:

Medline Extractor

Usage:
	wos.py <query> [--o=<filename>] [(--u=<username> --p=<passwd>)] [-v] [-s]
	wos.py (-h | --help)
	wos.py --version

Options:
	[query] Advance search query respecting the WOS syntax.
	--o Output filename [defaut:wos_saved-recs.txt].
	--u Username with MLV credential to acess to WOS.
	--p Password of MLV credential to acess to WOS.
	-v Activate verbose mode with debug ouput print.
	-s Activate Basic search mode, defaut is advanced mode.
	-h --help Show usage and Options.
	--version Show versions.

"""


import sys, os
import re
import random, time
import requests
import urllib
import spynner
from pyquery import PyQuery
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup
from private import private
from docopt import docopt
from pyvirtualdisplay import Display
	

class Session():
	def __init__(self, docopt_args):
		self.session = None
		self.dict_params = {}
		self.cookies = {}
		
		# print docopt_args
		#docopts_args variables
		self.query_arg = docopt_args['<query>']
		self.local_filename = docopt_args['--o']

		if self.local_filename is None:
			self.local_filename = "wos_saved-recs.txt"
		
		
		self.username = docopt_args['--u']
		self.password = docopt_args['--p']
		
		if self.username is None and self.password is None:
			self.username, self.password = private
			
		self.debug_opt = docopt_args['-v']
		self.basic = docopt_args['-s']
		if self.debug_opt is not None:
			print "initializing the extractor"

	def format(self, query):
		'''format basic search by topic'''
		return "TS=(%s)" %query 
	
	def debug(self, on=False):
		'''activate debug option'''
		if self.debug_opt is True or on is True:
			self.session.show()

			self.session.wait(60)
			return self.session

	def parse_params(self):
		'''parse an url its arguments and store them for future usage such as export'''
		if self.session.url is not None:
			self.p_url = urlparse(self.session.url)
			#parse query
			try:
				self.fragments = self.p_url.fragments
				if self.fragments == 'searchErrorMessage':
					print "Query syntax is invalid.\n\t>>>>Please check the syntax!!!!"
					self.debug(on=True)
					return False
			except AttributeError:
				self.p_query = self.p_url.query
				self.query_args = self.p_query.split("&")
				#transform params to dict (stores cookies and specific ids)
				self.params = [self.query_args[n].split("=") for n, i in enumerate(self.query_args) if self.query_args is not None]
				#print self.params
				for n in self.params:
					try:
						self.dict_params[n[0]] = n[1] 
					except IndexError:
						self.debug(on=True)
						self.qid = 1
						break
				#parse path
				self.p_path = self.p_url.path
				#parse netloc
				self.p_netloc = self.p_url.netloc
				return self
	
	def store_cookies(self):
		'''self-made method to store cookies from spynner(Netscape TXT) and send it to python-requests (dict) formats'''
		for l in re.split("\n",self.session.get_cookies())[2:]:
			domain = re.split("\t", l)[0]
			self.cookies[re.split("\t", l)[5]] = re.sub("\"", "", re.split("\t", l)[6])
		return self
	
	
	def connect(self):
		'''access to WOS website'''
		#print "connecting to", self.url
		# xephyr=Display(visible=0, size=(640, 480)).start()
		ENTER_PAGE = "https://apps-webofknowledge-com.fennec.u-pem.fr/MEDLINE_AdvancedSearch_input.do?&product=MEDLINE&search_mode=AdvancedSearch"
		self.url = ENTER_PAGE
		b = spynner.Browser()
		b.set_html_parser(PyQuery)
		try:
			b.load(self.url)
			if self.debug_opt is True:
				print "Connecting to the ENTER_PAGE"
			self.session = b
			return self.session
		except Exception, e:
			print "Error connecting the url:", self.url, e
			self.debug()
			try:
				print "Trying another time to connect in 10 minutes. Please wait", self.url
				time.sleep(60*10)
				self.connect()
			except Exception, e:
				print "Err.:500, Failed to connect...\nServer unreachable%s" %e
				return sys.exit()

	def authenticate(self):
		'''Authentication using defaut MLV authentication address and account or provided by the user'''
		self.session.wk_fill('input[id="username"]',self.username)
		self.session.wk_fill('input[id="password"]',self.password)
		self.session.click('input[name="submit"]')
		
		if self.debug_opt is True:
			print "Proceding to authentication..."
		self.debug()	
		if "SessionError" in self.session.url :
			self.session.click('a[target="_top"]')
			self.debug(on=True)
		self.session.wait(1)
		self.parse_params()
		try:
			self.ssid = self.dict_params['SID']
			# print self.ssid
			return True
		except Exception, e:
			self.session.wait(random.uniform(3, 7))
			self.parse_params()
			try:
				self.ssid = self.dict_params['SID']
				return True
			except Exception:
				print "Error Accessing Authentication Key SID"	
			return False
		

	def query(self):
		'''define advanced or basic search'''
		if self.debug_opt is True:
			print "Searching into Medline..."

		if "SessionError" in self.url :
			print "Error", b.url
			#~ b.click('a[target="_top"]')
			#~ self.session.wait(random.randint(2,5))
			sys.exit('Error in query format')
			
		#print "Query"
		self.store_cookies()
		self.adv_search()
		return self

	def adv_search(self):
		'''Advanced search method'''

		if self.debug_opt is True:
			print "Launching advanced search"
		self.url = "https://"+self.p_netloc+"/MEDLINE_AdvancedSearch_input.do?SID=%s&product=MEDLINE&search_mode=AdvancedSearch" %self.ssid
		self.session.load(self.url)
		#self.debug()
		#filling the advanced form
		self.session.wait(1)
		self.session.wk_fill('textarea[id="value(input1)"]', self.query_arg)
		self.session.click('input[title="Search"]')
		self.session.wait(2)
		self.session.click('a[title="Click to view the results"]',wait_load=True)
		self.parse_params()
		try:
			self.qid = self.dict_params['qid']
			self.max = self.resultsCount()
			print "Nombre de résultats :", self.max
			return self
		except KeyError:
			try:
				print BeautifulSoup(self.session.html.encode("utf-8")).text
				print BeautifulSoup(self.session.html.encode("utf-8").find({"id":"client_error_input_message"}))
				print BeautifulSoup(self.session.html.encode("utf-8").find("div", {"id":"client_error_input_message"}).text)
				return sys.exit("Search Error!. \nCheck your query...")
			except:
				self.debug()
				self.qid = 1
				self.max = 30877
				return self
			
	def __build__(self, markFrom, markTo, r_url):
		print markFrom, markTo
		data = {
				'SID': self.ssid,
				'colName':'MEDLINE',
				'count_new_items_marked':0,
				'displayCitedRefs':'true',
				'displayTimesCited':'true',
				'fields_selection': 'USAGEIND AUTHORSIDENTIFIERS SUBJECT_CATEGORY COMMENTS_NOTES NAME_SUBJECT_MISSION RECORD_OWNER CHEMICAL_AND_GENE_DATA ACCESSION_NUM NUM_OF_REF INVESTIGATORS KEYWORDS_CITATION_SUBSET ISSN GRANT_INFO LANGUAGE MESH_TERMS PROCESSING_DATES PUB_TYPE ADDRESSES ABSTRACT SOURCE TITLE AUTHORS',
				'filters':'USAGEIND AUTHORSIDENTIFIERS SUBJECT_CATEGORY COMMENTS_NOTES NAME_SUBJECT_MISSION RECORD_OWNER CHEMICAL_AND_GENE_DATA ACCESSION_NUM NUM_OF_REF INVESTIGATORS KEYWORDS_CITATION_SUBSET ISSN GRANT_INFO LANGUAGE MESH_TERMS PROCESSING_DATES PUB_TYPE ADDRESSES ABSTRACT SOURCE TITLE AUTHORS',  
				'format':'saveToFile',
				'locale':'en_US',
				'mark_from':markFrom,
				'mark_to':markTo,
				'mark_id':'MEDLINE',
				'mode':'OpenOutputService',
				'product':'MEDLINE',
				'qid':self.qid,
				'queryNatural': self.query_arg,
				'rurl':urllib.quote_plus(r_url),
				'save_options':'othersoftware',
				'search_mode':'AdvancedSearch',
				'selectedIds':'',
				'sortBy':'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A',
				'value(record_select_type)':'range',
				'viewType':'summary',
				'view_name':'MEDLINE-summary',
				}
		return data
		
	def export(self, markFrom, markTo):
		'''Export method: writing to a txt file '''
		
		if self.debug_opt is True:
			print "Exporting to %s" %self.local_filename
		print "exporting records from %d to %d"%(markFrom, markTo)
		r_url = "https://apps-webofknowledge-com.fennec.u-pem.fr/summary.do?product=MEDLINE&doc=1&qid="+self.qid+"&SID="+self.ssid+"&search_mode=AdvancedSearch"
		data = self.__build__(markFrom, markTo, r_url)
		print data['mark_from'], data['mark_to']
		
		post_url = "https://apps-webofknowledge-com.fennec.u-pem.fr/OutboundService.do?action=go&&"
		header={
				'Host': 'apps-webofknowledge-com.fennec.u-pem.fr', 
				'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
				'Accept-Language': 'fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3',
				'Accept-Encoding': 'gzip, deflate',
				'DNT': 1,
				'Referer': 'https://apps-webofknowledge-com.fennec.u-pem.fr/summary.do?product=MEDLINE&doc=1&qid=%s&SID=%s&search_mode=AdvancedSearch'%(self.qid, self.ssid),
				'Connection': 'keep-alive'
				}

		
				
		print '\b===',
		sys.stdout.flush()
		r = requests.get(post_url, params=data,headers=header, cookies=self.cookies)
		#redirects to #url = "http://ets.webofknowledge.com/ETS/ets.do?"
		print '\b===',
		sys.stdout.flush()
		final_r = requests.get(r.url, cookies=self.cookies, stream=True)
		print '\b===',
		sys.stdout.flush()
		#self.local_filename = "./wos_saved-recs.txt"
		with open(self.local_filename, 'a') as f:
			f.write(final_r.text.encode('utf-8'))
			print '\b===',
			sys.stdout.flush()
			return self.local_filename

	def resultsCount(self):
		'''for basic AND advanced search store the hitcount id provided by the interface'''
		return int(re.sub(",","", BeautifulSoup(self.session.html.encode("utf-8")).find("span", {"id": "hitCount.top"}).text))

def wos_extract(docopt_args):
	'''Command config'''
	#initiate session
	
	s = Session(docopt_args)
	start_time = time.time()
	print "Connecting to Medline..."
	c = s.connect()
	if c:
		print "Authentication ..."
		if s.authenticate():
			print "Send query ..."
			s.store_cookies()
			if s.adv_search():
				
				open(s.local_filename, 'w').close()
				s.export(0,500)
				l = list(range(500, s.max, 500))
				l.append(s.max)
				print "Exporting ..."
				for nb,count in enumerate(l):
					if count < max:
						try:
							s.export(count+1, l[nb+1])
						except:
							pass
						print '\b==\b',
						sys.stdout.flush()
				print "\n"
				total = time.time() - start_time, "seconds"
				raw_file = open(self.filename, 'r')
				for n in raw_file.readlines():
					print n
				raw_file_data = raw_file.read().decode("utf-8-sig").encode("utf-8")
				nb_occurence = len(raw_file_data.count("\nUT MEDLINE:"))
				print "Query %s had %d results: %d exported" %(s.query_arg, s.max, nb_occurence)
				print "sucessfully stored in file : %s\n" %(s.local_filename)
				print "Execution total time:", total[0], "seconds"			
				sys.exit(0)
	else:
		sys.exit("Error connecting ENTER_PAGE. Please check out your connexion and try again")



if __name__ == "__main__":
	wos_extract(docopt(__doc__))
	#wos(docopt(__doc__, version='0.2'))
	sys.exit()


