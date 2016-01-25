#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="wos.log", format=FORMAT, level=logging.INFO)
from private import private

import sys, os, re
import random, time
import requests, urllib
from urlparse import urlparse
from bs4 import BeautifulSoup
from splinter import Browser
#~ import spynner
#~ from pyquery import PyQuery
#from docopt import docopt
#from pyvirtualdisplay import Display


class WOS(object):
    """ A little module for exporting Web of Science search results into a txt file """
    def __init__(self, **kwargs):
        """
        Construct a new WOS object given a query, an export file (without ".isi")
        a username and a password for authentication
        eg :
            WOS(query="TS=(epigenetic*", outfile="epigenetic", user="myuser", passw="mypassw")
        """
        #defining params
        self.query = kwargs["query"]
        self.outfile = kwargs["outfile"]+".isi"
        try:
            self.product = kwargs["product"]
        except:
            self.product = "WOS"
        try:
            self.user=kwargs["user"]
            self.passw = kwargs["passw"]
        except:
            self.user, self.passw = private
        try:
            self.browser_app = kwargs["browser"]
        except:
            self.browser_app = "splinter"
        #using MLV Auth Server
        
        self.auth_url = "https://apps-webofknowledge-com.fennec.u-pem.fr/%s_AdvancedSearch_input.do?&product=WOS&search_mode=AdvancedSearch" %self.product
        print self.auth_url
        #Firefox Browser
        if self.browser_app == "splinter":
            self.browser = Browser()
        else:
            self.browser = spynner.Browser()
            self.browser.set_html_parser(PyQuery)
        
        #Session params
        self.session = None
        self.cookies = {}
        
        
        
        
        if self.query is None:
            sys.exit("No query provided")
        if "=" not in self.query:
            #or "(" not in self.query
            
            logging.warning("Syntax is not WOS compliant. Check Query Syntax")
            sys.exit("Query Syntax Error")
        if self.outfile is None:
            self.outfile = str(re.sub(re.compile("[^0-9a-zA-Z]+"),"_", self.query))+".isi"
            
        if self.user is None and self.passw is None:
            self.user, self.passw = private
        logging.info("Search parameters:\n\t-product: %s \n\t- query: %s\n\t- outfile: %s\n\t- user: %s\n\t- password: %s" %(self.product, self.query, self.outfile, self.user, self.passw))
        self.run()
        
    def auth(self):
        """ authentification throught auth_url to get the session id SID """
        #Loading url
        if self.browser_app == "splinter":
            self.browser.visit(self.auth_url)
            self.browser.fill('username', self.user)
            self.browser.fill('password', self.passw)
            self.browser.find_by_name("submit").click()
            self.cookies =  self.browser.cookies.all()
            
        else:
            self.browser = self.browser.load(self.url)
            self.browser.wk_fill('input[id="username"]',self.username)
            self.browser.wk_fill('input[id="password"]',self.password)
            self.browser.click('input[name="submit"]')
        
        #~ if self.debug is True:
            #~ print "Proceding to authentication..."
        
            if "SessionError" in self.session.url :
                self.session.click('a[target="_top"]')
                self.session.wait(random.uniform(1, 3))
        
        p_url = urlparse(self.browser.url)
        
        if p_url.netloc == "apps-webofknowledge-com.fennec.u-pem.fr":
            #print p_url.scheme+"//"+p_url.netloc+"/WOS_GeneralSearch_input.do?"+p_url.query
            expr = "product\=%s\&search_mode\=(?P<search_mode>.*?)\&SID=(?P<ssid>.*?)\&preferencesSaved\=" %self.product 
            print expr
            match = re.match(re.compile(expr), str(p_url.query))
            if match is not None:
                
                self.ssid = match.group("ssid")
                self.search_mode = re.sub("General", "Advanced", match.group("search_mode"))
                #self.search_mode = match.group("search_mode")
                self.search_url = "%s://%s/%s_%s_input.do?product=%s&search_mode=%s&SID=%s" %(p_url.scheme, p_url.netloc, self.product,self.search_mode,self.product,self.search_mode,self.ssid)        
                if self.browser_app == "splinter":
                    self.browser.visit(self.search_url)
                    print self.browser.url
                else:
                    self.browser.load(self.search_url)
                    print self.browser.url
                return self
            else:
                return sys.exit("Session Id could not be found")    
        else:
            logging.info("No redirection to service")
            return sys.exit("Invalid credentials")
        
    def launch_search(self):
        """ Filling the query form found into advanced search page """
        logging.info("Launching search")
        
        if self.browser_app == "splinter":
            self.browser.fill("value(input1)", self.query)
            self.browser.find_by_xpath("/html/body/div[1]/form/div[1]/table/tbody/tr/td[1]/div[2]/div[1]/table/tbody/tr/td[1]/span[1]/input").click()
            bs = BeautifulSoup(self.browser.html)
            
        else:
            self.session.wk_fill('textarea[id="value(input1)"]', self.query)
            self.session.click('input[title="Search"]')
            self.session.wait(random.randint(2,5))
            
            bs = BeautifulSoup(self.browser.html.encode("utf-8"))
        
        query_history = bs.find_all("div", {"class":"historyResults"})
        self.nb_search = len(query_history)
        try:
            self.nb_results = int(re.sub(",", "", query_history[0].text))
        except IndexError:
            self.nb_results = int(re.sub(",", "", query_history.text))
            print self.nb_results
            
        logging.warning("Your search \"%s\" gave %i results"%(self.query, self.nb_results))
        logging.info("Your SSID is : %s" %self.ssid)
        if self.browser_app == "splinter":
            self.browser.click_link_by_partial_href('/summary.do?')
        else:
            self.session.click('a[title="Click to view the results"]',wait_load=True)
            
        print urlparse(self.browser.url).query
        match = re.search(re.compile("product=(?P<product>.*)&doc\=(?P<doc>.*?)\&qid\=(?P<qid>.*?)&SID"), urlparse(self.browser.url).query)        
        if match is not None:
            print match.group()
            self.product, self.doc, self.qid = match.group("doc"), match.group('qid')
            print self.product, self.doc, self.qid
            return self
        else:
            
            self.doc, self.qid = self.parse_params()
            return self
            
    
    def load_results(self, markFrom, markTo, i):
        """ Load_results(markFrom, markTo) 500 by 500 given the nb of results """
        logging.info("loading results")
        #print "exporting"
        #p_url0= "http://apps.webofknowledge.com/AutoSave_UA_output.do?action=saveForm&SID=%s&product=UA&search_mode=output" %self.ssid
        #r0 = requests.post(p_url0, headers= headers, cookies=self.cookies)
        # print p_url0
        #print r0
        #p_url1= "http://apps.webofknowledge.com/AutoSave_UA_output.do?action=saveForm&SID=%s&product=UA&search_mode=results" %self.ssid
        # print p_url1
        #r1 = requests.post(p_url1, headers= headers, cookies=self.cookies)
        #print r1
        r_url = "https://apps-webofknowledge-com.fennec.u-pem.fr/summary.do?product=WOS&doc=1&qid="+self.qid+"&SID="+self.ssid+"&search_mode=AdvancedSearch"
        post_url = "https://apps-webofknowledge-com.fennec.u-pem.fr/OutboundService.do?action=go&&"
        #r2 = requests.post()

        header={
                'Host': 'apps-webofknowledge-com.fennec.u-pem.fr',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': 1,
                'Referer': 'https://apps-webofknowledge-com.fennec.u-pem.fr/summary.do?product=%s&doc=1&qid=%s&SID=%s&search_mode=AdvancedSearch'%(self.product, self.qid, self.ssid),
                'Connection': 'keep-alive'
                }
        # markTo = 500
        # markFrom = 1
        view = self.product+"-summary"
        data = {
                'SID': self.ssid,
                'colName':'WOS',
                'count_new_items_marked':0,
                'displayCitedRefs':'true',
                'displayTimesCited':'true',
                'fields_selection':'USAGEIND AUTHORSIDENTIFIERS ACCESSION_NUM FUNDING SUBJECT_CATEGORY JCR_CATEGORY LANG IDS PAGEC SABBR CITREFC ISSN PUBINFO KEYWORDS CITTIMES ADDRS CONFERENCE_SPONSORS DOCTYPE CITREF ABSTRACT CONFERENCE_INFO SOURCE TITLE AUTHORS',
                'filters':'USAGEIND AUTHORSIDENTIFIERS ACCESSION_NUM FUNDING SUBJECT_CATEGORY JCR_CATEGORY LANG IDS PAGEC SABBR CITREFC ISSN PUBINFO KEYWORDS CITTIMES ADDRS CONFERENCE_SPONSORS DOCTYPE CITREF ABSTRACT CONFERENCE_INFO SOURCE TITLE AUTHORS',
                'format':'saveToFile',
                'locale':'en_US',
                'markFrom':1,
                'markTo':markTo,
                'mark_from':markFrom,
                'product':'WOS',
                'mark_to':markTo,
                'mode':'OpenOutputService',
                'product':self.product,
                'qid':self.qid,
                'startYear':'2015',
                'endYear':'2014',
                #rurl:'http%3A%2F%2Fapps.webofknowledge.com%2Fsummary.do%3FSID%3DT1WYtnvIngPkHzI4ShI%26product%3DWOS%26doc%3D1%26qid%3D1%26search_mode%3DAd
                'rurl':urllib.quote_plus(r_url),
                'save_options':'othersoftware',
                'search_mode':'AdvancedSearch',
                'selectedIds':'',
                'sortBy':'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A',
                'value(record_select_type)':'range',
                'viewType':'summary',
                'view_name':view,
                }
        
        
        r = requests.get(post_url, params=data,headers=header, cookies=self.cookies)
        #redirects to #url = "http://ets.webofknowledge.com/ETS/ets.do?"
        
        
        final_r = requests.get(r.url, cookies=self.cookies, stream=True)
        with open( self.outfile.split('.isi')[0]+'_'+str(i) +'.isi' , 'w') as f:
            final_r.text
            f.write(final_r.text.encode('utf-8'))
        return self.outfile
    
    def export(self):
        """Writing results into outfile (defaut is normalized query)"""
        start_time = time.time()
        open(self.outfile, 'w').close()
        l = list(range(0, self.nb_results, 500))
        l.append(self.nb_results)
    
        logging.info("Exporting %s 500 by 500..." %self.nb_results)
        for i,n in enumerate(l):
            if l[i]+1 < self.nb_results:
                self.load_results(l[i]+1, l[i+1],str(l[i]+1)+'-'+str(l[i+1]))
        
        total = time.time() - start_time, "seconds"
        # raw_file = open(self.outfile, 'r')
        # raw_file_data = raw_file.read().decode("utf-8-sig").encode("utf-8")
        # nb_occurence = len(raw_file_data.split("\n\n"))-1
        logging.info("Query \"%s\" had %d results: %d has been exported" %(self.query, self.nb_results))
        logging.info("Sucessfully stored in file : %s\n" %(self.outfile))
        #logging.info("Execution total time:"+str(" ".join(total)))
        return 
        
    def run(self):
        """ Generic method that encapsulates the WOS extract process """
        self.auth()
        self.launch_search()
        self.export()
        self.browser.close()
        return


if __name__=="__main__":
    #WOS(query='TS=(complexity OR "complex system*")',outfile="wos.txt")
    WOS(query='TS="synthetic biology" AND PY=(2010-2012)',outfile="sbdeuxans")
    
