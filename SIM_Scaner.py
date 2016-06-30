#__author__ = 'MTabaz'
import re
import serial
import sys

class SIMScan:
    def __init__(self):
        #List of all addresses with invalid parameters query
        self.lis_103 = []
        #List of all invalid addresses (indicates unused location)
        self.lis_148 = []
        #List of all valid Headers with the header content
        self.lis_144 = {}
        #List of all unknown responses
        self.lis_oth = []

    def Scan(self,ser,startindex):
        state = False

        for i in range(startindex,int(0xFFFF),1):
            try:
                index = "{:04x}".format(i)
                print index
                #Read MF/DF/EF Header
                ser.write('AT+CRSM=192,'+str(int(index,16))+',0,0\r')
                res = ser.readall()
                print res
                #Invalid Prameter
                match_103 = re.search(r'\+CRSM:\s*103',res)

                # Found Header
                # i.e: +CRSM: 144, 0, "0000000E6F53040011FFBB01020000"
                match_144 = re.search(r'\+CRSM:\s*14[45],\s*\d+,\s*\"(\w+)\"',res)

                # Address not found
                match_148 = re.search(r'\+CRSM:\s*148',res)

                if match_103:
                    self.lis_103.append(index)
                elif match_144:
                    #Add valid Header
                    self.lis_144[index] = match_144.group(1)
                    print res
                elif match_148:
                    self.lis_148.append(index)
                else:
                    self.lis_oth.append(index)
            except:
                print "Scaning Not Compeleted, Program stopped at address: 0x" + "{:04x}".format(i)
                return (state,self.lis_144)
        state = True
        return (state,self.lis_144)

    def ReadEF_File(self,id,len,conn):
        #input checker
        if len == 0 or conn == None:
            return ""
        #read file data
        conn.write('AT+CRSM=178,'+str(int(id,16))+',0,0,'+str(len)+'\r')
        res = conn.readall()
        #print res
        #check of successful execution
        match = re.search(r'\+CRSM:\s*144,\s*\d+,\s*\"(\w+)\"',res)
        if match:
            return match.group(1)
        else:
            return ""

    def ReadEF_Record(self,id,filesize, recordlen,conn = None):
        RECORD_ID = 1
        Records = {}
        State = 0
        #input checker before execution
        if recordlen == 0 or conn == None:
            return (-1,{})

        #Loop over number of records
        while RECORD_ID <= filesize/recordlen:
            #Read record data
            conn.write('AT+CRSM=178,'+str(int(id,16))+','+str(RECORD_ID)+',10,'+str(recordlen)+'\r')
            res = conn.readall()
            #print res
            if res:
                #check if command execution was successful or not
                match_ok = re.search(r'\+CRSM:\s*144,\s*\d+,\s*\"(\w+)\"',res)
                match_Nok = re.search(r'(\+CRSM:\s*148)|(\+CRSM:\s*152)',res)
                if match_ok:
                    Records[RECORD_ID] = match_ok.group(1)
                    State = 1
                elif match_Nok:
                    break
                else:
                    break
                #To Read the next record
                RECORD_ID += 1

        return (State, Records)

    def ReadRawData(self,conn):
        for key in self.lis_144.keys():
            #parse header data
            SIMTYPE = int(self.lis_144[key][0:4],16)
            #handling SIM/USIM headers
            if SIMTYPE == 0:
                print "\nFile ID: "+ key + ", File Header: " +  self.lis_144[key]
                #Convert file size from hex to int
                FileSize = int(self.lis_144[key][4:8],16)
                #Convert File type from hex to int
                FileType = int(self.lis_144[key][26:28],16)
                #Convert Record size from hex to int
                RecordSize = int(self.lis_144[key][28:30],16)

                #read Elementary file dare in case of plan data
                if FileType == 0:
                    RawData = self.ReadEF_File(key, FileSize,conn)
                    print "File Size: "+ str(FileSize) + " ,Raw Data: " + RawData
                elif FileType < 3 and RecordSize != 0:
                    #If file type is an array of data or DF/MF Header
                    RawData = {}
                    (state, RawData) = self.ReadEF_Record(key,FileSize,RecordSize,conn)
                    if len(RawData) > 0:
                        print "File Size: " + str(FileSize)
                        for ele in RawData.keys():
                            print "Record ID: "+ str(ele) + " ,Record Size: "+ str(RecordSize) + " ,Raw Data: " + RawData[ele]
                    else:
                        #If MF/DF header which doesn't condain any body
                        print "File Size: " + str(FileSize)
            #Handling UICC SIM
            else:
                print "\nFile ID: "+ key + ", File Header: " +  self.lis_144[key]
                Type = int(self.lis_144[key][12:14],16)
                RecordSize = int(self.lis_144[key][14:16],16)
                NumberOfRecords = int(self.lis_144[key][16:18],16)
                FileSize = NumberOfRecords * RecordSize
                if Type == 0:
                    (state, RawData) = self.ReadEF_Record(key,FileSize,RecordSize,conn)
                    if len(RawData) > 0:
                        print "File Size: " + str(FileSize)
                        for ele in RawData.keys():
                            print "Record ID: "+ str(ele) + " ,Record Size: "+ str(RecordSize) + " ,Raw Data: " + RawData[ele]
                    else:
                        #If MF/DF header which doesn't condain any body
                        print "File Size: " + str(FileSize)
                else:
                    match = re.search(r'\w+00200?(\w\w)(\w\w)+',self.lis_144[key])
                    if match:
                        FileSize = int(match.group(1),16)
                        RawData = self.ReadEF_File(key, FileSize,conn)
                        print "File Size: "+ str(FileSize) + " ,Raw Data: " + RawData

        return 1

if __name__ == "__main__":
    Port = sys.argv[1]
    ser = ''
    Scanner = SIMScan()
    if Port:
        try:
            ser = serial.Serial(port= Port,baudrate= 115200, timeout=1 ,bytesize=serial.EIGHTBITS, parity= serial.PARITY_EVEN , stopbits= serial.STOPBITS_ONE)
        except:
            print "Can't Open the Provided Port, Please provide a correct one!"
            exit()

        print "####################################"
        print "Scanning SIM Address Space...."
        print "####################################"

        Headers = {}
        
        #Scan the SIM address space from "0000" to "FFFF"
        #Should start from "0" but in some cases the first
        #index is RST request to the SIM so the process 
        #should start from "1"
        (state,headers) = Scanner.Scan(ser,1)

        if state == True:
            print "Parsing Headers Completed..."
        else:
            print "Parsing Headers Completed with Error !!!"
        print "Reading SIM Raw Data!"

        #Reade Raw data for the carved headers
        Scanner.ReadRawData(ser)

        print "####################################"
        print "Scanning Completed!"
        print "####################################"

    else:
        print "Please Enter the connection port name"
