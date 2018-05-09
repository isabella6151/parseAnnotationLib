__author__ = 'isabella'

import sys
import os
import csv
import datetime
import logging
import myLogger
import copy
import sys, traceback
import parseSupport
pth = os.sep.join(os.path.abspath(os.path.dirname(__file__)).split(os.sep)[:-1])
sys.path.append(pth)

import parseAnnotationLibUnitCheck as pLib
class regionNotFound(Exception):
    pass
class indexingError(Exception):
    pass
class dataAddError(Exception):
    pass
class dataFormatError(Exception):
    pass
class valueNotFoundError(Exception):
    pass
class shopValueError(Exception):
    pass
class computeStdMetrics(object):
    def __init__(self):

        # hdlr = logging.FileHandler("serverLog.log")
        # self.logger.addHandler(hdlr)
        self.first = True
        self.packCount = 0
        self.singleCount = 0
        self.lineCount = 1
        self.shop_buyer= {}
        self.shop_nonbuyer = {}
        self.dateOfShop = {}
        self.day_dict_buyer = {}
        self.day_dict_nonbuyer = {}
        self.dept_traffic = {}
        self.dept_shopper = {}
        self.dept_buyer = {}
        self.non_region_cols = {}
        self.store_dict = {}
        self.col_dict = {}
        self.data = {}
        call_dict = {'status': '', 'data': '', 'docNum': '', 'row_num': ''}

    def get_category_map(self,filename):
        """
        :param : filename : str
        :rtype : dict
        """
        category_map = dict()
        try:
            with open(filename) as f:
                print "Reading file %r" % filename
                csv_file = csv.reader(f)
                for row in csv_file:
                    if row[0] == "Category":
                        continue
                    category_map[row[1]] = row[0]
        except TypeError:
            # if the mapFile key in the opts file is empty (assuming that there was no map file created or an example of
            # oversight) then the type of filename is None. This in turn throws a TypeError when attempting to open
            pass
        return category_map

    def __get_logfile_name(self, opts_dict):
        """
        function to construct the output filename
        filename = stdMetricsOutputDir + '_' + platform + '_' + store + '_' + date + '_' + time " '.csv'
        :param opts_dict:
        :type opts_dict: dict
        """

        dt = datetime.datetime.today()
        # in_file = opts_dict['csvFile'].split(os.sep)[-1].split('.')[0]
        in_file = 'HersheySalty_1751'
        filename = '_'.join([in_file,dt.strftime("%H%M%S")])
        return os.sep.join([opts_dict['stdMetricsOutputDir'], in_file + '.csv'])

    def __call__(self, **kwargs):
        self.lineCount+= 1

        if kwargs['status'] == 'done':
            opts_dict = kwargs['opts'] # args[1]
            map_file = opts_dict['mapFile']
            filename = self.__get_logfile_name(opts_dict)
            self.__write_std_metrics(map_file, filename,opts_dict['csvFile'])
            self.lineCount = 1
            self.store_dict = {}

        elif kwargs['status'] == 'FinalError':
            self.non_region_cols = kwargs['non_region_cols']
            opts_dict = kwargs['opts']
            self.lineCount = 1
            self.store_dict = {}
            # raise Exception('Please check the log files for errors')
            #self.__checkForErrors(opts_dict)
        else:
            if not kwargs['error']:
                data_dict = kwargs['data']
                opts_dict = kwargs['opts']
                self.__computer_metrics(data_dict,opts_dict)
            else:
                data_dict = kwargs['data']
                opts_dict = kwargs['opts']
                rowNum = kwargs['rowNum']
                self.data[rowNum] = copy.deepcopy(data_dict)
                self.col_dict[rowNum] = copy.deepcopy(kwargs['main_cols'])



    def __getCount(self,data_dict):
        key1 = 'Pack Count'
        key2 = 'Single Count'
        for region in data_dict:
            if len(data_dict[region][key1]) > 0:
                self.packCount+= 1
            if len(data_dict[region][key2]) > 0:
                self.singleCount += 1

    def _evalutateExpression(self,exp1,evt,valDict,evt1,exp2):
        dict1 = valDict
        exp1 = exp1.replace("<event1>",evt)
        result = eval(exp1)
        if result:
            list1 = valDict[evt1]
            shopTime = eval(exp2)
            print list1


        print result
        #if result
    def __computer_metrics(self,data_dict,opts_dict):

        bKey = 'Behavior'
        curDate = data_dict['Start Time']
        # ignoreList = ("Comments","HasNoEvents","Issues","Outside Door","Duration","SplitEventID","Start Time","AnnotatorID","Txn_ID","Age","Gender","Ethnicity","Clips","Clip","Region","Txn_ID")
        neededVal = 'Blue'
        startTime = datetime.datetime.strftime(data_dict['Start Time'],"%Y-%m-%d:%H%M%S")

        shoppingTime = 0
        buyer = False
        shopper = False
        for category in data_dict:
            if category in neededVal:
                if 'Shop' in data_dict[category][bKey]:
                    shopper = True
                if len(data_dict[category][bKey])!= 0:
                    buyer,shoppingTime = parseSupport.getBuyerShopTime(data_dict[category][bKey],'Buy','Shop')
                else:
                    shopper = False
                    buyer = False

        unitCount = ''
        for val in data_dict['Blue']['Unit Count'].keys():
            unitCount = val

        if not shopper and not buyer:
            self.store_dict[self.lineCount - 1] = {"StartTime": startTime, 'Shopper': False,"Category":data_dict['Category'], "Buyer": False,'Time In Category':data_dict['Duration'],
                                                    'Shopping Time': shoppingTime,'Age': data_dict['Age'],
                                                   "Gender": data_dict['Gender'],
                                                   'At-Shelf Interaction': data_dict['At-Shelf Interaction'],
                                                   "Ethnicity": data_dict['Ethnicity'], "Unit Count": unitCount,
                                                   'GroupID': data_dict['GroupID'],'Group Interaction': data_dict['Groupd Interaction']}

        if shopper:
            self.store_dict[self.lineCount - 1] = {"StartTime": startTime,"Category":data_dict['Category'], 'Shopper': True, "Buyer": False,'Time In Category':data_dict['Duration'],
                                                    'Shopping Time': shoppingTime,'Age': data_dict['Age'],
                                                   "Gender": data_dict['Gender'],
                                                   'At-Shelf Interaction': data_dict['At-Shelf Interaction'],
                                                   "Ethnicity": data_dict['Ethnicity'], "Unit Count": unitCount}
        if buyer:
            self.store_dict[self.lineCount-1]['Buyer']= True
            # self.store_dict[self.lineCount-1]['Shopping-Buyer']= shoppingTime



    def __write_std_metrics(self,map_filename, filename,csvFile):

        with open(filename, 'ab') as file_pointer:
            try:
                store = csvFile.split("\\")[-1].split(" ")[1].split('_')[0]
                new_csv_file = csv.writer(file_pointer)
                if self.first:
                    row = ["Store","Region","Date","Shopper","Buyer",'Time In Category','Shopping Time',"Unit Count","Age","Gender","At-Shelf Interaction","Ethnicity"]
                    new_csv_file.writerow(row)
                    # file_pointer.write(row)
                    self.first = False
                for lineNum in self.store_dict:
                    # buyerAvgShop = 0
                    # nonBuyerAvgShop = 0
                    new_row = [store,self.store_dict[lineNum]['Category'],self.store_dict[lineNum]['StartTime'],self.store_dict[lineNum]['Shopper'],self.store_dict[lineNum]['Buyer'],
                               self.store_dict[lineNum]['Time In Category'], self.store_dict[lineNum]['Shopping Time'],self.store_dict[lineNum]['Unit Count'],
                               self.store_dict[lineNum]['Age'],self.store_dict[lineNum]['Gender'],self.store_dict[lineNum]['At-Shelf Interaction'],
                               self.store_dict[lineNum]['Ethnicity']]
                    # file_pointer.write(row)
                    new_csv_file.writerow(new_row)
                    #new_csv_file.close()
                self.store_dict = {}

            except Exception,ex:
                print ex
                print "hi"



if __name__ == "__main__":
    obj = computeStdMetrics()
    pLib.parseAnnotationLib(os.path.abspath(sys.argv[1])).parse(obj)