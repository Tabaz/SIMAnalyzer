#__author__ = 'MTabaz'

import sys
import serial
import re
import SMS_Parser
import pylab
import datetime

class SIMContent:
    def __init__(self, port):
        try:
            self.ser = serial.Serial(port= Port,baudrate= 115200,
                                     timeout=1 ,bytesize=serial.EIGHTBITS,
                                     parity= serial.PARITY_EVEN ,
                                     stopbits= serial.STOPBITS_ONE)
            self.init = 1
            self.ser.flushInput()
            self.MSG_State = {0:"received unread messages",
                              1:"received read messages",
                              2:"stored unsent messages",
                              3:"stored sent messages"}
            self.Phone_Activity_Status = { 0: "Ready",
                                           1: "Unavailable",
                                           2: "Unkown",
                                           3: "Ringing",
                                           4: "Call in Progress",
                                           5: "Asleep"}
            self.OperationMode = {0: "Data",
                                  1: "Fax class 1",
                                  2: "Fax class 2"}
            self.SMSParser = SMS_Parser.SMSParser()
            self.Timestamp = {}
            self.TimestampData = []
            self.Timeline = {}
            self.HistGraph = {}

        except:
            print "Can't Open the Provided Port, Please provide a correct one!"
            self.init = 0


    def FormatOutput(self,string):
        result = ""
        for i in range(0,len(string)-1,2):
            result += string[i+1]+string[i]
        return result

    def DrawTimeLine(self):
        # ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d '))
        # ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
        pylab.ylim(0,41)
        for key in self.Timeline.keys():
            #c = range(len(self.test[key]))
            #pylab.xticks(c, [x[0] for x in self.test[key]])
            date = [x[0] for x in self.Timeline[key]]
            value = [x[1] for x in self.Timeline[key]]
            pylab.plot(date,value)
            pylab.gcf().autofmt_xdate()
        pylab.xlabel("Timestamp")
        pylab.ylabel("SIM Locations")
        pylab.grid()
        pylab.show()

    def DrawHistTimeline(self):
        pylab.ylim(0,41)
        pylab.gcf().autofmt_xdate()
        for key in self.HistGraph.keys():
            if self.HistGraph[key] != 0:
                pylab.bar(self.HistGraph[key], key,alpha=.3,yerr=.25,error_kw={'ecolor': '1'})
        pylab.xlabel("Timestamp")
        pylab.ylabel("SIM Locations")
        pylab.grid()
        pylab.show()

    def DrawHistTimelineWithDeletedSMS(self):
        pylab.ylim(0,41)
        pylab.gcf().autofmt_xdate()

        maxIndex = -1
        maxIndexTime = ''

        Maxtime = ''
        MaxtimeIndex = -1

        map = {}
        map1 = {}
        index = 0

        for key in self.HistGraph.keys():
            if str(self.HistGraph[key] not in map.keys()) and self.HistGraph[key] != 0:
                map[str(self.HistGraph[key])] = index
                index += 1
        #mapping the timestamp string to integers
        index = 0
        for key in sorted(map.keys()):
            map1[key] = index
            index += 1
        for key in self.HistGraph.keys():
            if self.HistGraph[key] != 0:
                self.HistGraph[key] = map1[str(self.HistGraph[key])]
            else:
                self.HistGraph[key] = -1
        #setting the x axis with the timestamp values
        pylab.xticks(map1.values(),map1.keys())
        #Draw received SMS timeline
        for key in range(1,len(self.HistGraph)+1,1):
            if self.HistGraph[key] != -1:
                pylab.bar(self.HistGraph[key], key,alpha=.3 ,color='b', yerr=.25,error_kw={'ecolor': '1'},align='center')
                if key > maxIndex:
                    maxIndex = key
            # else:
            #     pylab.plot(int(len(map1.keys())/2),key,'ro')
        #Draw empty or deleted SMS Timeline
        for key in range(1,len(self.HistGraph)+1,1):
            if self.HistGraph[key] == -1:
                if key < maxIndex and maxIndex != -1:
                    pylab.plot(self.HistGraph[maxIndex],key, 'ro')
                elif key > maxIndex and maxIndex != -1:
                    pylab.plot(0, key,'ro')
        #Plot the graph
        pylab.xlabel("Timestamp")
        pylab.ylabel("SIM Locations")
        pylab.grid()
        pylab.show()
        #pylab.savefig("TimeLine.jpg", figsize=(800,1280), dpi=1000)

    def SIM_SMSInfo(self,details=0):#6F3C/6F42/6F43/6F47
        result = "SMS Information: "
        self.Timeline[0] = []
        self.Timeline[41] = []
        if details == 1:
            for RECORD_ID in range(1,41,1):
                self.ser.write('AT+CRSM=178,'+str(int(0x6F3C))+','+str(RECORD_ID)+',10,176\r')
                Content = self.ser.readall()
                MSG = re.search(r'\+CRSM:\s*\d+,\s*\d+,\s*\"(\w+)\"',Content)
                result += "\n"
                if MSG:
                    result += "Message ID     :"+str(RECORD_ID)+"\n"
                    result += "Message State  :"+MSG.group(1)[0:2]+"\n"
                    result += "Content        :"+str(MSG.group(1))+"\n\n"
                    #print str(MSG.group(1))
                    if MSG.group(1)[0:2] == "00":
                        self.Timestamp[""] = RECORD_ID
                        self.TimestampData.append(("",0))
                        self.HistGraph[RECORD_ID] = 0
                    elif MSG.group(1)[0:2] == "01" or MSG.group(1)[0:2] == "03":
                        timestamp = self.SMSParser.SMSDetails(str(MSG.group(1)))
                        self.HistGraph[RECORD_ID] = timestamp
                        if RECORD_ID not in self.Timeline.keys():
                            self.Timeline[RECORD_ID] = [(timestamp,RECORD_ID)]
                        if timestamp not in self.Timestamp.keys():
                            self.Timeline[RECORD_ID] = [(timestamp,RECORD_ID)]
                            for key in self.Timeline.keys():
                                if len(self.Timeline[key]) == 0:
                                    self.Timeline[key].append((timestamp,key))
                                if self.Timeline[key][0][0] < timestamp:
                                    self.Timeline[key].append((timestamp,self.Timeline[key][0][1]))
                        self.Timestamp[timestamp] = RECORD_ID
                        self.TimestampData.append((timestamp,RECORD_ID))

        else:
            self.ser.write('AT+CMGL=4\r')
            Content = self.ser.readall()
            MSG_List = re.finditer(r'\+CMGL:\s+(\d+),\s*(\d+),\s*.*,\s*(\d+)\r\n(\w+)',Content)
            if MSG_List:
                result += "\n"
                for msg in MSG_List:
                    result += "Message ID     :"+str(msg.group(1))+"\n"
                    result += "Message State  :"+self.MSG_State[int(msg.group(2))]+"\n"
                    result += "Length         :"+str(msg.group(3))+"\n"
                    result += "Content        :"+str(msg.group(4))+"\n\n"
            else:
                result += "Not Found!"


        for key in self.Timeline.keys():
            self.Timeline[key].append((datetime.datetime.now(),key))
        #print self.HistGraph

        ##self.DrawTimeLine()
        ##self.DrawHistTimeline()
       # self.DrawHistTimelineWithDeletedSMS()

        return result

    def SIM_IMSI(self):
        result = "SIM IMSI: "
        self.ser.flushInput()
        self.ser.write("AT+CIMI\r")
        Content = self.ser.readall()#.split("\n")[1].replace('"', "")
        IMSI = re.search(r'(\w+)',Content)
        self.ser.flushInput()
        if IMSI:
            result += IMSI.group(1)
        else:
            result += "Not Found!"
        return result

    def SIM_CCID(self): #2FE2
        result = "SIM CCID: "
        self.ser.flushInput()
        self.ser.write('AT+CRSM=176,'+str(int(0x2FE2))+',0,0,10\r')
        Content = self.ser.readall()
        CCID = re.search(r'\+CRSM:\s*\d+,\s*\d+,\s*\"(\w+)\"',Content)
        if CCID:
            result += self.FormatOutput(CCID.group(1))
        elif "NOT" in result or "ERROR" in result:
            self.ser.write("AT+CCID\r")
            result += self.ser.readall()
            self.ser.flushInput()
        else:
            result += "Not Found!"
        return result

    def SIM_PhoneBookInfo(self):
        result = "Phone Book Information:"
        self.ser.flushInput()
        self.ser.write('AT+CPBR=?\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CPBR:\s*\((\d+)\-(\d+)\),\s*\d+,\s*\d+',Content)
        if Param:
            self.ser.write('AT+CPBR='+str(Param.group(1))+','+str(Param.group(2))+'\r')
            Content = self.ser.readall()
            self.ser.flushInput()
            PB_List = re.finditer(r'\+CPBR:\s+(\d+),\s*(".+"),\s*(\d+),\s*"(.+)"',Content)
            if PB_List:
                result += "\n"
                for item in PB_List:
                    try:
                        result += item.group(1)+") Name: \""+item.group(4).replace("00","").decode("hex")+\
                                  "\",   Number: " + item.group(2)+"\n"
                    except:
                        result += item.group(1)+") Name: \""+item.group(4).replace("00","")+\
                                  "\",   Number: " + item.group(2)+"\n"
            else:
                result += "Not Found!"
        else:
            result+= "Not Found!"
        return result

    def SIM_MSISDN(self):#6F40
        result = "Phone MSISDN: "
        self.ser.write("AT+CNUM\r")
        Content = self.ser.readall()
        Param = re.search(r'\+CNUM\s*:\s*(.+)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Clear(self):
        self.ser.flushInput()
        self.ser.write('')

    def SIM_PIN_State(self):
        result = "PIN Status: "
        self.ser.write('AT+CPIN?\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CPIN:\s*(.*)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Reader_Manufacturer_ID(self):
        result = "Reader Manufactur ID: "
        self.ser.write('AT+CGMI\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CGMI:\s*(.*)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Reader_Model_ID(self):
        result = "Reader Model ID: "
        self.ser.write('AT+CGMM\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CGMM:\s*(.*)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Reader_Revision_ID(self):
        result = "Reader Revision ID: "
        self.ser.write('AT+CGMR\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CGMR:\s*(.*)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Reader_SN(self):
        result = "Reader SN: "
        self.ser.write('AT+CGSN\r')
        Content = self.ser.readall()
        Param = re.search(r'(\w+)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def SIM_Supported_SMS_Format(self):
        result = "Supported SMS Formats: "
        self.ser.write('AT+CSCS=?\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CSCS:\s*\((.*)\)',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Get_Phone_Activity_Status(self):
        result = "Phone Activity Status: "
        self.ser.write('AT+CPAS\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CPAS:\s*(\d+)',Content)
        if Param:
            result += self.Phone_Activity_Status[int(Param.group(1))]
        else:
            result += "Not Found!"
        return result

    def SIM_PIN_1_2_Status(self):
        result = "Pin 1: "
        self.ser.write('AT+CPIN?\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CPIN:\s*(.+)',Content)
        if Param:
            result += Param.group(1) + "\n"
        else:
            result += "Not Found!\n"
        self.Clear()
        self.ser.write('AT+CPIN2?\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CPIN2:\s*(.+)',Content)
        if Param:
            result += "Pin 2: " + Param.group(1) + "\n"
        else:
            result += "Pin 2: Not Found!\n"
        return result

    def SIM_Sevice_Provider(self):
        result = "Service provider name: "
        self.ser.write('AT+CRSM=176,'+str(int(0x6F46))+',0,0,17\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CRSM:\s*\d+,\s*\d+,\s*\"(\w+)\"',Content)
        if Param:
            result += Param.group(1).decode("hex")
        else:
            result += "Not Found!"
        return result

    def SIM_Sevice_Table(self):#6F38
        result = "SIM Service Table(SST): "
        self.ser.write('AT+CRSM=176,'+str(int(0x6F38))+',0,0,17\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CRSM:\s*\d+,\s*\d+,\s*\"(\w+)\"',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def Phone_Operation_Mode(self):
        result = "Operation Mode: "
        self.ser.write('AT+FCLASS?\r')
        Content = self.ser.readall()
        Param = re.search(r'\s*(\d+)',Content)
        if Param:
            result += self.OperationMode[int(Param.group(1))]
        else:
            result += "Not Found!"
        return result

    def Location_Information(self):#6F7E
        result = "Location Information: "
        self.ser.write('AT+CRSM=176,'+str(int(0x6F7E))+',0,0,11\r')
        Content = self.ser.readall()
        Param = re.search(r'\+CRSM:\s*\d+,\s*\d+,\s*\"(\w+)\"',Content)
        if Param:
            result += Param.group(1)
        else:
            result += "Not Found!"
        return result

    def GetAll_SIM_INFO(self):
        result = ""
        result += self.SIM_CCID()
        self.Clear()
        result += "\n\n" + self.SIM_IMSI()
        self.Clear()
        result += "\n\n" + self.SIM_PhoneBookInfo()
        self.Clear()
        result += "\n\n" + self.SIM_SMSInfo(1)
        self.Clear()
        result += "\n\n" + self.SIM_PIN_State()
        self.Clear()
        result += "\n" + self.SIM_PIN_1_2_Status()
        self.Clear()
        result += "\n\n" + self.SIM_MSISDN()
        self.Clear()
        result += "\n\n" + self.SIM_Supported_SMS_Format()
        self.Clear()
        result += "\n\n" + self.Phone_Operation_Mode()
        self.Clear()
        result += "\n\n" + self.Get_Phone_Activity_Status()
        self.Clear()
        result += "\n\n" + self.SIM_Sevice_Provider()
        self.Clear()
        result += "\n\n" + self.SIM_Sevice_Table()
        print result

    def GetAll_Reader_INFO(self):
        result =""
        result += self.Reader_Manufacturer_ID()
        self.Clear()
        result += "\n\n" + self.Reader_Model_ID()
        self.Clear()
        result += "\n\n" + self.Reader_SN()
        self.Clear()
        result += "\n\n" + self.Reader_Revision_ID()
        print result


if __name__ == "__main__":
    Port = sys.argv[1]
    if Port:
        print "Extraction of the information started..."
        print "****************************************"
        SIM = SIMContent(Port)
        if SIM.init:
            print "            SIM Information             "
            print "****************************************"
            SIM.Clear()
            SIM.GetAll_SIM_INFO()
            print "****************************************"
            print "           Reader Information           "
            print "****************************************"
            SIM.Clear()
            SIM.GetAll_Reader_INFO()
        print "****************************************"
        print "Extraction Completed!"
    else:
        print "Please Provide the Reader Port Name!"


