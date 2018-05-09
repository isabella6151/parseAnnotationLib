__author__ = 'isabella'

import os
import csv
import os.path
import datetime
import myLogger
from yaml import load_all, Loader
# import myLogger
import msvcrt as m
import pdb
import traceback as tb
import sys
import glob
def get_category_map(filename):
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
                category_map[row[0]] = row[1]
    except TypeError:
        # if the mapFile key in the opts file is empty (assuming that there was no map file created or an example of
        # oversight) then the type of filename is None. This in turn throws a TypeError when attempting to open
        pass
    return category_map


class ErrorCheck:
    def __init__(self,optsDict):
        self.logger = myLogger.Logger("errorCheckLog.log")
        self.optsDict = optsDict
    def errorCheck(self):

        self.__checkKeys()
        self.__checkCsvFile()
        self.logger.exit()
    def __checkCsvFile(self):
        errorFlag = 0
        col_keys = [key for key in self.optsDict if key.find('Col') != -1]
        filename = self.optsDict['csvFile'].split('\\')[-1]
        with open(self.optsDict['csvFile'], 'rb') as fp:
            csv_obj = csv.reader(fp)
            header = csv_obj.next()
            for key in col_keys:
                try:
                    index = header.index(self.optsDict[key])
                except:
                    if key == self.optsDict['entersRegion']:
                        #self.regionNotFound(self.optsDict[key],filename,False)
                        self.logger.warning("Enter Region not present in csv file - %r. Assumed to be a single region " %filename,False)
                    else:
                        # self.regionNotFound(self.optsDict[key],filename,True)
                        self.logger.error("%s field is not present in csv file - %s.Please rectify before proceding " %(self.optsDict[key],filename),False)
                        errorFlag = 1

        if errorFlag == 1:
            raise Exception("\n\nThere were errors in processing. Please check the log file\n\n")

    def __checkKeys(self):
        errorFlag  = 0
        errorLvl = 0

        try:
            enterEvent = self.optsDict['entersRegion']
        except:
            enterEvent = ''
            #self.optsKeyError('Enter',False)
            self.logger.warning("Enters Region is not provided in opts File. Assumed to be a single Region",False)
            # raise optsKeyError

        if enterEvent != '':
            try:
                event = self.optsDict[enterEvent]
            except:
                #self.optsKeyError('Enter',True)
                self.logger.error("Enters Region doesn't have corresponding key/val pair.Please correct this before proceding",False)
                errorFlag = 1
                # raise optsKeyError

        try:
            event = self.optsDict['shoppingBehaviorCol']
        except:
            #self.optsKeyError('Shopper Behavior',False)
            self.logger.warning("Shopper Behavior Column not provided in opts File.Assumed that Shopping Time is not needed",False)
            errorLvl += 1
            # raise optsKeyError

        try:
            event = self.optsDict['engagementCol']
        except:
            #self.optsKeyError('Engagement',False)
            self.logger.warning("Engagement column is not provided in opts File.",False)
            errorLvl += 1

        if errorLvl > 1:
            #self.optsKeyError('Shopper and Engagement',True)
            self.logger.warning("shoppingBehaviorCol,engagementCol both missing",False)
            # raise Exception("\n\nThere were errors in processing. Please check the log file\n\n")
        elif errorFlag == 1:
            raise Exception("\n\nThere were errors in processing. Please check the log file\n\n")


class parseAnnotationLib(object):
    def __init__(self, opts_file):
        self.opts_file = opts_file
        self.row_num = 0


    def __makeDict(self, data, dataDict,name):
        errorFlag = 0
        if name == 'Unit Count' and (data == '0.00,;' or data == '0,;' or data == ''):
            return errorFlag
        if name.lower() == 'size':
            if data == "":
                data = "0.00,"
        try:
            parts = data.split(';')
            if len(parts)== 1 and 'enters' in parts[0].lower():
                dataDict[0.00] =  parts[0]
                return errorFlag
            elif len(parts) == 1 and parts[0].split(',')[0] == '0.00' and parts[0].split(',')[1] == "":
                return errorFlag
            for part in parts:
                events = part.split(',')
                if len(events) == 2 and events[0] == '0.00' and events[1] == '':
                    continue
                if events[1] == '':
                    self.logger.warning("Some event has no attribute at time --> %r " %(self.start_time),False)
                    dataDict[float(events[0])] = ''
                    errorFlag = 1
                else:
                    dataDict[float(events[0])] = events[1]
        except:
            self.logger.error("Error while parsing data at time --> %s  Annotator --> %s" %(self.start_time,self.annotator),False)
            errorFlag = 1
        return errorFlag

    def __makeDictOtherCol(self, row, other_dict, data_dict):
        for key, idx in other_dict.iteritems():
            data_dict[key] = row[idx]
        #may need to change later
        try:
            data_dict['Start Time'] = datetime.datetime.strptime(data_dict['Start Time'], "%Y-%m-%dT%H:%M:%S.%f")
        except:
            data_dict['Start Time'] = datetime.datetime.strptime(data_dict['Start Time'][:19], "%Y-%m-%dT%H:%M:%S")
    def __getTimes(self, tsList, idx):
        startTs = tsList[idx]
        if idx + 1 == len(tsList):
            stopTs = -1
        else:
            stopTs = tsList[idx + 1]
        return startTs, stopTs


    def __get_events(self, src_data_dict, region_data_dict, start_ts, stop_ts, key,eventType,buyer_found,buyer_count):

        shopdict = {}
        eventdict = {}
        # if self.row_num == 17:
        #     print self.row_num
        errorFlag = 0
        for tIdx in src_data_dict:
            if 'shop' in src_data_dict[tIdx].lower():
                if src_data_dict[tIdx] in ['Start Shop', 'Stop Shop','Shopper','Start Shopping','Stop Shopping']:
                    shopdict[tIdx] = src_data_dict[tIdx]
                else:
                    #ec.dataFormatError('Shopper',self.row_num)
                    self.logger.error("Shopper event values not in the correct format",False)
                    errorFlag = 1
                    return errorFlag,buyer_found,buyer_count
            else:
                eventdict[tIdx] = src_data_dict[tIdx]
                if src_data_dict[tIdx].lower() == 'buy':
                    buyer_count+= 1
                    buyer_found = True
        # tsList will be populated only when key is 'Behaviour', it is empty when key is 'Engagement' or any other column
        # that does not contain shopping events
        tslist = sorted(map(float, shopdict.keys()))
        evlist = sorted(map(float, eventdict.keys()))
        if len(tslist) == 0 and len(evlist) == 0 and eventType != 'Other':
            errorFlag = 0
            return errorFlag,buyer_found,buyer_count

        if eventType == 'StartStop':
            evt = 'Shop'
            # get starting idx
            for tsIdx in range(0, len(tslist), 2):
                # if tsList[tsIdx] < startTs:

                if tslist[tsIdx] >= start_ts and 'Start' in shopdict[tslist[tsIdx]]: #and tslist[tsIdx] < stop_ts:
                    try:
                        if tslist[tsIdx + 1] <= stop_ts and 'Stop' in shopdict[tslist[tsIdx + 1]]:
                            if evt not in region_data_dict[key]:
                                region_data_dict[key][evt] = [tslist[tsIdx]]
                                region_data_dict[key][evt].append(tslist[tsIdx + 1])
                            else:
                                region_data_dict[key][evt].append(tslist[tsIdx])
                                region_data_dict[key][evt].append(tslist[tsIdx + 1])
                        # else:
                        #     if evt not in region_data_dict[key]:
                        #         region_data_dict[key][evt] = [tslist[tsIdx]]
                        #     else:
                        #         region_data_dict[key][evt].append(tslist[tsIdx])
                        #    raise BaseException
                    except IndexError:
                        #this error will occcur only if index of start shop is equal to end time of the region
                        if tslist[tsIdx] != stop_ts:
                            self.logger.error("Indexing error while parsing annotation file.Start/Stop shop missing at time --> %r. Annotator --> %s" %(self.start_time,self.annotator),False)
                            errorFlag = 1

                elif tslist[tsIdx] > start_ts and tslist[tsIdx] < stop_ts and shopdict[tslist[tsIdx]] == 'Stop Shop':
                    #ec.indexError('Start shop',self.row_num)
                    # if evt not in region_data_dict[key]:
                    #     region_data_dict[key][evt] = [tslist[tsIdx]]
                    # else:
                    #     region_data_dict[key][evt].append(tslist[tsIdx])
                    self.logger.error("Indexing error while parsing annotation file.Start shop missing at time --> %r. Annotator --> %s" %(self.start_time,self.annotator),False)
                    errorFlag = 1
                else:
                    continue
            behaviorKey = ""
            for key1 in region_data_dict:
                if 'Shop' in region_data_dict[key1].keys():
                    behaviorKey = key1
                    break

            for esIdx in range(len(evlist)):
                #first check whether all the events are within the shop dict range
                #if evList[esIdx] >= start_ts and evlist[esIdx] <= stop_ts:
                valAdded = False
                try:
                    if evlist[esIdx] >= start_ts and evlist[esIdx] <= stop_ts:
                        if behaviorKey != "":
                            for tIdx in range(0, len(region_data_dict[behaviorKey][evt]), 2):
                                if evlist[esIdx] >= region_data_dict[behaviorKey][evt][tIdx] and evlist[esIdx] <= region_data_dict[behaviorKey][evt][tIdx+1]:
                                    if eventdict[evlist[esIdx]] in region_data_dict[key]:
                                        region_data_dict[key][eventdict[evlist[esIdx]]].append(evlist[esIdx])
                                    else:
                                        region_data_dict[key][eventdict[evlist[esIdx]]] = [evlist[esIdx]]
                                    valAdded = True
                                    break
                        if  not valAdded:
                            if start_ts == 0.0 and stop_ts == 9999.99 and eventdict[evlist[esIdx]] != 'Buy':
                                region_data_dict[key][eventdict[evlist[esIdx]]] = [evlist[esIdx]]
                                continue
                            #ec.dataAddError('Engagement',self.row_num)
                            self.logger.error("Error while adding engagement events.Please check data at time --> %r. Annotator --> %s" %(self.start_time,self.annotator),False)
                            errorFlag = 1
                        #     pdb.set_trace()
                        #     raise Exception('Didnt add value')

                    else:
                        continue
                except:
                    if valAdded:
                        #ec.dataAddError('Engagement',self.row_num)
                        self.logger.error("Error while adding engagement events.Please check data at time --> %r. Annotator -->%s" %(self.start_time,self.annotator),False)
                        errorFlag = 1
        elif eventType == 'Shopper':

            evt = 'Shopper'
            # get starting idx
            for tsIdx in range(0, len(tslist), 1):
                    try:
                        if tslist[tsIdx] >= start_ts and tslist[tsIdx] < stop_ts and shopdict[tslist[tsIdx]] == 'Shopper':
                            if evt not in region_data_dict[key]:
                                region_data_dict[key][evt] = [tslist[tsIdx]]
                            else:
                                region_data_dict[key][evt].append(tslist[tsIdx])
                        else:
                            continue
                    except:
                        self.logger.error("Error while adding Shopper in region.Please check data at time --> %r. Annotator -->%s" %(self.start_time,self.annotator),False)
                        errorFlag = 1
            for esIdx in range(len(evlist)):
                #first check whether all the events are within the shop dict range
                #if evList[esIdx] >= start_ts and evlist[esIdx] <= stop_ts:
                try:
                    if evlist[esIdx] >= start_ts and evlist[esIdx] < stop_ts:
                        if eventdict[evlist[esIdx]] in region_data_dict[key]:
                            region_data_dict[key][eventdict[evlist[esIdx]]].append(evlist[esIdx])
                        else:
                            region_data_dict[key][eventdict[evlist[esIdx]]] = [evlist[esIdx]]
                    else:
                        continue
                except Exception, e:
                    self.logger.error("Error while adding Shopper events.Please check data at time --> %r. Annotator --> %s" %(self.start_time,self.annotator),False)
                    errorFlag = 1
        elif eventType == 'Other':
            if buyer_found and len(evlist)==0:
                self.logger.error("Missing %s.Please check data at time --> %r. Annotator --> %s" %(key,self.start_time,self.annotator),False)
                errorFlag = 1
            elif buyer_found and (len(evlist) != buyer_count):
                self.logger.error("Number of Buy events dont match %s.Please check data at time --> %r. Annotator --> %s" %(key,self.start_time,self.annotator),False)
                errorFlag = 1
            for esIdx in range(len(evlist)):
                #first check whether all the events are within the shop dict range
                #if evList[esIdx] >= start_ts and evlist[esIdx] <= stop_ts:
                    try:
                        if evlist[esIdx] >= start_ts and evlist[esIdx] < stop_ts:
                            if eventdict[evlist[esIdx]] in region_data_dict[key]:
                                region_data_dict[key][eventdict[evlist[esIdx]]].append(evlist[esIdx])
                            else:
                                region_data_dict[key][eventdict[evlist[esIdx]]] = [evlist[esIdx]]
                        else:
                            continue
                    except Exception, e:
                        self.logger.error("Error while adding other events.Please check data at time --> %r. Annotator --> %s" %(self.start_time,self.annotator),False)
                        errorFlag = 1
                    #raise Exception
        if errorFlag > 0:
            if self.annotator not in self.annotatorErrorDict:
                self.annotatorErrorDict[self.annotator] = [self.row_num]
            elif self.row_num not in self.annotatorErrorDict[self.annotator]:
                self.annotatorErrorDict[self.annotator].append(self.row_num)
        return int(errorFlag),buyer_found,buyer_count
    def __reset(self, d):
        d.clear()


    def __write_std_metrics(self, traffic, shopper, map_filename, filename,eventType):
        """
        Writes standard vision metrics such as traffic, shopper and average shopping time per region/color
        :param traffic: dict
        :param shopper: dict
        :param map_filename: str
        :param filename: str
        :rtype: none
        """
        # get mapping of colors to region/categories
        category_map = get_category_map(map_filename)
        # if mapFile is empty in the opts file, the returned category_map is also empty. The results can still be
        # computed but will be tabulated against the color rather than the category name
        if len(category_map) == 0:
            colors = traffic.keys()
            for color in colors:
                category_map[color] = color

        with open(filename, 'wb') as file_pointer:
            new_csv_file = csv.writer(file_pointer)
            row = ["Category", "Traffic", "Shopper", "Average Shopping Time"]
            new_csv_file.writerow(row)
            if eventType == 'StartStop':
                for category in category_map:
                    if category_map[category] in traffic:
                        traffic_count = traffic[category_map[category]]
                    else:
                        traffic_count = 0
                    if category_map[category] in shopper:
                        shopper_count = int(shopper[category_map[category]][0])
                        shopping_time = float(shopper[category_map[category]][1]) / shopper_count
                    else:
                        shopper_count = 0
                        shopping_time = 0
                    new_row = [category, traffic_count, shopper_count, shopping_time]
                    new_csv_file.writerow(new_row)
            elif eventType == 'Shopper':
                for category in category_map:
                    if category_map[category] in traffic:
                        traffic_count = traffic[category_map[category]]
                    else:
                        traffic_count = 0
                    if category_map[category] in shopper:
                        shopper_count = int(shopper[category_map[category]])
                    else:
                        shopper_count = 0
                    new_row = [category, traffic_count, shopper_count,'-']
                    new_csv_file.writerow(new_row)


    def __get_logfile_name(self, opts_dict):
        """
        function to construct the output filename
        filename = stdMetricsOutputDir + '_' + platform + '_' + store + '_' + date + '_' + time " '.csv'
        :param opts_dict:
        :type opts_dict: dict
        """
        import datetime

        dt = datetime.datetime.today()
        in_file = opts_dict['csvFile'].split(os.sep)[-1].split('.')[0]
        filename = '_'.join([in_file, dt.strftime("%Y%m%d"), dt.strftime("%H%M%S")])
        return os.sep.join([opts_dict['stdMetricsOutputDir'], filename + '.csv'])


    def __compute_std_metrics(self, data_dict, key, traffic, shopper,eventType):
        """
        Count traffic and shopper per region
        To get average shop time per region, divide the total shop time by the number of shoppers
        :type traffic: dict
        :param data_dict: dict
        :param key: str
        :param traffic: dict
        :param shopper: dict
        :return:
        """
        for region in data_dict:
            if region not in traffic:
                traffic[region] = 1
            else:
                traffic[region] += 1
            shop_time = 0
            try:
                if eventType == 'StartStop':
                    for tIdx in range(0, len(data_dict[region][key]['Shop']), 2):
                        shop_time += (data_dict[region][key]['Shop'][tIdx + 1] - data_dict[region][key]['Shop'][tIdx])
                    # this average is for 1 shopper across his shopping intervals
                    avg_shop_time = shop_time / (len(data_dict[region][key]['Shop']) * 0.5)
                    if region not in shopper:
                        # [#shoppers, shopping_time]
                        shopper[region] = [1, avg_shop_time]
                    else:
                        shopper[region][0] += 1
                        shopper[region][1] += avg_shop_time
                elif eventType == 'Shopper':
                    if 'Shopper' in data_dict[region][key]:
                        if region not in shopper:
                            shopper[region] = 1
                        else:
                            shopper[region] += 1
            except KeyError:
                continue
        return traffic, shopper


    def parse(self, *args):

        call_dict = {'status': '', 'data': '', 'docNum': '', 'row_num': ''}
        doc_num = 0

        #starting the log file for the current file
        filesWithErrorList = []
        for optsDict in load_all(open(self.opts_file, 'rb'), Loader=Loader):
            csvFileList = glob.glob(optsDict['csvFile'])
            for inputFile in csvFileList:
                optsDict['csvFile'] = inputFile
                main_errorFlag = 0
                self.logger = myLogger.Logger("parseAnnotationErrors.log")
                self.annotator = ''
                self.annotatorErrorDict = {}
                doc_num += 1
                call_dict['opts'] = optsDict
                call_dict['docNum'] = doc_num
                call_dict['status'] = 'processing'
                print optsDict['csvFile']
                self.logger.info('\nError log for the file--> %r' %optsDict['csvFile'],False)
                #first let us check for all the basic errors
                try:
                    ec = ErrorCheck(optsDict)
                    ec.errorCheck()
                    #ErrorCheck.errorCheck(optsDict)
                except:
                    raise

                # open the data csv file
                with open(optsDict['csvFile'], 'rb') as fp:
                    csv_obj = csv.reader(fp)
                    header = csv_obj.next()
                    try:
                        has_no_evt_idx = header.index('HasNoEvents')
                    except ValueError:
                        has_no_evt_idx = None

                    try:
                        if optsDict['stdMetrics']:
                            traffic = {}
                            shopper = {}
                    except KeyError:
                        pass
                    try:
                        annotatorIdx = header.index('AnnotatorID')
                    except:
                        annotatorIdx = -1
                        # raise Exception('AnnotatorID field is not present')
                    #startTime index is fixed as 0 for now since its always the first column in the csv. If this
                    #assumption changes in the future then change this part
                    startTimeIdx = 0
                    # resolve and cache all the keys with Col in
                    col_keys = [key for key in optsDict if key.find('Col') != -1 and key != optsDict['entersRegion']]
                    enter_key = optsDict['entersRegion']

                    # make dictionaries for each key
                    col_dict = {}
                    data_dict = {}
                    other_dict = {}
                    self.row_num = 1
                    singleEnterFlag = False
                    # data_dict['filename'] = os.path.basename(optsDict['csvFile']).split('.')[0]
                    for row in csv_obj:
                        if annotatorIdx != -1:
                            self.annotator = row[annotatorIdx]
                        else:
                            self.annotator = 'Annotator X'
                        self.start_time = row[startTimeIdx]
                        errorFlag = 0
                        self.row_num += 1
                        call_dict['rowNum'] = self.row_num
                        call_dict['row'] = row
                        call_dict['error'] = False
                        call_dict['main_cols'] = ''
                        call_dict['non_region_cols'] = ''
                        if not has_no_evt_idx == None:
                            if row[has_no_evt_idx]:
                                continue

                        for key in col_keys:
                            col_dict[key] = {'data': {}, 'idx': header.index(optsDict[key]), 'name': optsDict[key]}

                        try:
                            idx = header.index(optsDict[enter_key])
                            col_dict[enter_key] = {'data': {}, 'idx': idx, 'name': optsDict[enter_key]}
                        except:
                            if not singleEnterFlag:
                                self.logger.warning("No enters region present. Adding single region to group other data",False)
                                singleEnterFlag = True
                            col_dict[enter_key] = {'data': {}, 'idx': -1, 'name': optsDict[enter_key]}

                        other_cols = list(set(header).difference([col_dict[k]['name'] for k in col_dict]))
                        for col in other_cols:
                            other_dict[col] = header.index(col)


                        for key, valDict in col_dict.iteritems():
                            if valDict['idx'] != -1:
                                errorFlag += self.__makeDict(row[valDict['idx']], valDict['data'],valDict['name'])
                            else:
                                data = "0.00,Enter Blue"
                                errorFlag += self.__makeDict(data,valDict['data'],valDict['name'])
                        call_dict['main_cols'] = col_dict
                        #if there is val in errorFlag it means there has been some error while processing data
                        # if 'shoppingBehaviorCol' in optsDict:
                        #         try:
                        #             shopdata = col_dict['shoppingBehaviorCol']['data']
                        #             for tIdx in shopdata:
                        #                 if 'shop' in shopdata[tIdx].lower():
                        #
                        #                 if src_data_dict[tIdx] in ['Start Shop', 'Stop Shop','Shopper']:
                        #                     shopdict[tIdx] = src_data_dict[tIdx]
                        #                 else:
                        #                     eventdict[tIdx] = src_data_dict[tIdx]
                        #         except:

                        if errorFlag == 0:
                            # list of time stamps of entry and exit into regions
                            enters_region_key = optsDict['entersRegion']
                            ts_list = sorted(map(float, col_dict[enters_region_key]['data'].keys()))


                            # get the list of opts file entries for non region columns - data_dict will have as many
                            # dictionaries as there are regions and each non region in turn will have a dictionary associated
                            # with it
                            non_region_cols = [key for key in col_keys if key.find('region') == -1]
                            call_dict['non_region_cols'] = non_region_cols

                            # go over each time frame between two successive 'Enters <color>'
                            for idx in range(len(ts_list)):
                                # color of region
                                region = col_dict[enters_region_key]['data'][ts_list[idx]].split(' ')[-1]

                                if region not in data_dict:
                                    data_dict[region] = {}
                                    for key in non_region_cols:
                                        data_dict[region][optsDict[key]] = {}

                                # get entry and exit times for region under consideration
                                start_ts, stop_ts = self.__getTimes(ts_list, idx)
                                if stop_ts == -1:
                                    stop_ts = 9999.99
                                #buy_found part is specific only to display and has to be removed after project is over
                                buyer_found = False
                                buyer_count = 0
                                try:
                                    eventType = optsDict['eventType']
                                    behaviorCol = optsDict['shoppingBehaviorCol']
                                    errorFlagCtr,buyer_found,buyer_count =  self.__get_events(col_dict['shoppingBehaviorCol']['data'], data_dict[region], float(start_ts),
                                                          float(stop_ts), optsDict['shoppingBehaviorCol'],eventType,buyer_found,buyer_count)
                                    errorFlag += errorFlagCtr
                                except KeyError:
                                    pass
                                if 'engagementCol' in optsDict:
                                    try:
                                        engagementCol = optsDict['engagementCol']
                                        errorFlagCtr1,buyer_found,buyer_count = self.__get_events(col_dict['engagementCol']['data'], data_dict[region], float(start_ts),
                                                              float(stop_ts), engagementCol,eventType,buyer_found,buyer_count)
                                        errorFlag += errorFlagCtr1
                                    except Exception, e:
                                        #self.logger.error("Exception while parsing Engagement Column: Row Num -%r, !"%(longCat,self.catToAisleDict[shortCat]),False)
                                        #errorFlag = 1
                                        print tb.format_exc()

                                remCols = [col for col in non_region_cols if col not in ['shoppingBehaviorCol', 'engagementCol']]
                                for key in remCols:
                                    # __getEventsNew(behaviorDict, data_dict[region],float(startTs), float(stopTs), 'Behavior')
                                    try:
                                        eventType = 'Other'
                                        errorFlagCtr2,buyer_found,buyer_count = self.__get_events(col_dict[key]['data'], data_dict[region], float(start_ts),float(stop_ts),optsDict[key],eventType,buyer_found,buyer_count)
                                        errorFlag+= errorFlagCtr2

                                    except Exception, e:
                                        print self.row_num
                                        # print str(e)

                                        pdb.set_trace()

                        if errorFlag == 0:
                            try:
                                if optsDict['stdMetrics']:
                                    eventType = optsDict['eventType']
                                    self.__compute_std_metrics(data_dict, optsDict['shoppingBehaviorCol'], traffic, shopper,eventType)
                            except KeyError:
                                pass

                        else:
                            call_dict['error'] =  True
                            main_errorFlag += 1
                        # call any of the passed in function pointers
                        self.__makeDictOtherCol(row, other_dict, data_dict)
                        call_dict['data'] = data_dict
                        for arg in args:
                            arg(**call_dict)

                        # reset all dictionaries
                        self.__reset(data_dict)
                        for key in col_dict:
                            self.__reset(col_dict[key])

                if main_errorFlag > 0:
                    filesWithErrorList.append(optsDict['csvFile'])
                    call_dict['status'] = 'FinalError'
                    self.logger.exit()
                    if len(self.annotatorErrorDict) >0:
                        self.logger = myLogger.Logger("AnnotatorErrorCount.log")
                        self.logger.info('Annotator error count for the file--> %r' %optsDict['csvFile'],False)
                        for annotator in self.annotatorErrorDict:
                            self.logger.info('Annotator --> %s. Error Count --> %s' %(annotator,len(self.annotatorErrorDict[annotator])))
                        self.logger.exit()
                    for arg in args:
                        arg(**call_dict)
                   #raise Exception("\n\nThere were errors in processing. Please check the log file\n\n")
                try:
                    if optsDict['stdMetrics']:
                        filename = self.__get_logfile_name(optsDict)
                        self.__write_std_metrics(traffic, shopper, optsDict['mapFile'], filename,eventType)
                except KeyError:
                    pass
                if call_dict['status'] != 'FinalError':
                    call_dict['status'] = 'done'
                call_dict['rowNum'] = -1
                for arg in args:
                    arg(**call_dict)
        if len(filesWithErrorList) > 0:
            print "The following files have errors. Please check the log file for more details\n"
            for file in filesWithErrorList:
                print "%s " %file
            sys.exit()