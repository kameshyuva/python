import logging
import time

class ElasticSearch:
      def __init__(self, es):
          self.es = es
      def postESData(self,bulkData,**args):
          try:
            #Optimizing bulk
            from elasticsearch import helpers
            helpers.bulk(self.es,bulkData,**args)
            #self.wait_until_good_health()
          except Exception, e:
            logging.error(" postESData : %s ", e)
            raise e
      def checkESStatus(self):
          return self.es.cluster.health()['status']
      def wait_until_good_health(self,retrySecs=3):
          logging.info('Waiting until cluster is green/yellow')
          while True:
            status = self.checkESStatus()
            if status == 'green' or status == 'yellow' :
               return True
            print "sleeping for {0} secs".format(retrySecs)
            time.sleep(retrySecs)
            print "sleep over"
      def getESData(self,**args):
          try:
            idVal = self.es.search(**args)
            return idVal
          except Exception, e:
            logging.error(" getESData : %s ",e)
            raise e
      def scrollESData(self,**args):
          try:
            idVal = self.es.scroll(**args)
            return idVal
          except Exception, e:
            logging.exception(" scrollESData : %s ",e)
            raise e
      def clearScroll(self,scroll_id):
          try:
            self.es.clear_scroll(body=scroll_id)
          except Exception, e:
            logging.exception(" scrollESData : %s ",e)
            raise e
      def getMapping(self,**args):
          try:
            from elasticsearch.client import IndicesClient
            getMap = IndicesClient(self.es)
            idxMapping = getMap.get_mapping(**args)
            return idxMapping
          except Exception, e:
            logging.error(" getmapping : %s ",e)
            raise e
      def createMapping(self,**args):
          try:
            from elasticsearch.client import IndicesClient
            getMap = IndicesClient(self.es)
            newMapping = getMap.create(**args)
          except Exception, e:
            logging.error(" createMapping : %s ",e)
            raise e
      def deleteIndex(self,**args):
          try:
            from elasticsearch.client import IndicesClient
            delIdx = IndicesClient(self.es)
            newMapping = delIdx.delete(**args)
          except Exception, e:
            logging.error(" deleteIndex : %s ",e)
            raise e
      def helperScan(self,fieldList,index=None):
          try:
            from elasticsearch import helpers
            return  helpers.scan( self.es,
                                  query={ "fields" : fieldList },
                                  index=index,
                                  scroll="1m"
                                 )
          except Exception, e:
            raise e
      def multiGet(self, **args ):
          try:
             return self.es.mget(**args)
          except Exception, e:
            raise e
      def getSettings(self,**args):
          from elasticsearch.client import IndicesClient
          getES = IndicesClient(self.es)
          return getES.get_settings(**args)
      def putSettings(self,**args):
          from elasticsearch.client import IndicesClient
          setES = IndicesClient(self.es)
          ret = setES.put_settings(**args)
          return ret['acknowledged'] is True
      def forceMerge(self,**args):
          from elasticsearch.client import IndicesClient
          fmES = IndicesClient(self.es)
          return fmES.forcemerge(**args)
      def deepPaginate(self,**args):
          """   Deep pagination is costly and the suggested scroll api actually failed in a test environment
                while retrieving data from an index where  doc count > 2 million.
                On a cluster with 3 nodes (4GB memory each), 2 ES masters, and each instance running with 2gb heap in each server with normal usage,
                the full dump fails with TransportError(404, u'search_phase_execution_exception) above 2million (scrolling works well until then though).
                This is primarily due to ES heap filling fast on scrolling before it could be GC-ed (atleast that is what i understand as of now:) ).
                Alternate logic to retrieve by id runs into same issue as scrolling is used there too.
                ES goes OOM above 2 million docs. Few other options that can be tried,
                  1. increase ES_MIN_MEM / ES_MAX_MEM heap ( considering the system specification , basically vertical scaling might help )
                  2. increase transient => index.max_result_window setting in ES ( 2.1.x and above limits by default to 10000 )
                  3. try from/size query pagination.
                  4. see if you can ignore/chunk any _type holding huge data.
                  5. Try search_after api.
                  6. distribute hits to different nodes rather than sending all the requests to a single node. use urllib3.connection_pool, sniff on ES host.
                  7. or, retrieve docs by time fields or try to frame a fresh logic.
          """
          try:
            #initialize scroll
            dumpIdxData = self.getESData(size=10000,scroll="1m",**args)
            scrollId = dumpIdxData['_scroll_id']
            scrollSize = dumpIdxData['hits']['total']
            while (scrollSize>0):
                  # persist scroll for an extra min after each hit. tune it if possible.
                  chunkIdxData = self.scrollESData(body=scrollId,scroll="1m")
                  scrollIdPrev = scrollId
                  scrollId = chunkIdxData['_scroll_id']
                  if scrollIdPrev != scrollId:
                     self.clearScroll(scrollIdPrev)
                  scrollSize = len(chunkIdxData['hits']['hits'])
                  if scrollSize == 0:
                     logging.info("scrolling complete..")
                     break
                  logging.info("scrolling size : %s ",scrollSize)
                  for chunkData in chunkIdxData['hits']['hits']:
                      dumpIdxData['hits']['hits'].append(chunkData)
            self.clearScroll(scrollId)
            return dumpIdxData
          except Exception,e:
            raise e
      def idGenerator(self,**args):
          try:
            #reset dumpIdxData
            dumpIdxData = self.getESData(size=0,request_timeout=60,**args)
            typeDict={}
            fieldList=["_id","_type"]
            for i, dObj in enumerate( self.helperScan( fieldList, index=args['index'] ) , start=1 ):
                typeDict.setdefault(dObj["_type"],[]).append(dObj["_id"])
                #get data for every 10000 records
                if i%10000 == 0 :
                   for t,v in typeDict.items():
                       chunkIdxData = self.multiGet(doc_type=t,body={ "ids" : v },**args)
                       for chunkData in chunkIdxData['docs']:
                           dumpIdxData['hits']['hits'].append(chunkData)
                           #flush current for a new set
                           typeDict={}
                       time.sleep(2)
            return dumpIdxData
          except Exception,e:
            raise e
