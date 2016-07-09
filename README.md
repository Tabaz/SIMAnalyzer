# SIMAnalyzer
  SIMAnalyzer will help forensic investigators to analyze and extract useful artifacts from SIM cards. This tool developed to shed the light on how SIM cards forensic work and how to develop simple application to allow data extraction from SIM cards. This application give the idea on how to change the content of certain file and how to analyze the information on SIM card either by data interpretation or by using the raw data.
  
## Featuers:
  1) SIMScaner
  
  This will allow the investigator to scan the SIM address space and extract all files header, read the raw data for each file header extracted from the SIM card.
  
  2) SIMExtractor
  
  This will allow the investigator to extract known artifactes from SIM card e.g. CCID, SMS, IMSI, phonebook, SST, PIN state, SP and others.
  
  3) SMSParser
  
  This will allow the investigator to parse SMS meta data and content by extracting and interprating the data.
  
## Usage:

  1) Get SIM reader or unlocked USB modem
  
  2) Insert he SIM card in to the reader
  
  3) Plug the reader and identify the port connecting on
  
  4) Open terminal
  
  5)   
     
     a. python SIM_Extractor.py "Port name"
  
     b. python SIM_Scaner.py "port name"
     
