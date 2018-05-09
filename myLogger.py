import logging
import os,sys,datetime,inspect

dt = datetime.datetime.today()

class Logger:
    def __init__(self,logFilePath):
        dateStr = '_'.join([dt.strftime("%Y%m%d"),dt.strftime("%H%M%S")])
        dirName = os.path.dirname(logFilePath)
        fileParts = os.path.splitext(os.path.basename(logFilePath))
        self.filePath = os.path.join(dirName,'%s_%s%s'%(fileParts[0],dateStr,fileParts[1]))

    def __initLogging__(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S',filename = self.filePath,level=logging.DEBUG)
        #logging.FileHandler(self.filePath)

    def info(self,cMsg,cRaiseException=False):
        self.__inspect__(cMsg,cRaiseException,logging.info)

    def warning(self,cMsg,cRaiseException=False):
        self.__inspect__(cMsg,cRaiseException,logging.warning)

    def critical(self,cMsg,cRaiseException=False):
        self.__inspect__(cMsg,cRaiseException,logging.critical)

    def error(self,cMsg,cRaiseException=True):
        self.__inspect__(cMsg,cRaiseException,logging.error)

    def exception(self,cMsg,cRaiseException=True):
        self.__inspect__(cMsg,cRaiseException,logging.exception)

    def exit(self):
        log = logging.getLogger()
        x = list(log.handlers)
        for i in x:
            log.removeHandler(i)
        i.flush()
        i.close()

    def __inspect__(self,cMsg,cRaiseException,cLogInst):
        self.__initLogging__()
        frm = inspect.stack()[1]
        funcName = frm[3]
        print '%s:%s'%(funcName,cMsg)
        cLogInst(cMsg)
        if cRaiseException:
            raise Exception(cMsg)

