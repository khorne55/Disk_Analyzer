# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 19:29:46 2020

@author: Piotr Kurzynoga

Partition Reader
"""

import sys

#Handle args passed, in this case the file name (if there is no file passed default to the path)
if(len(sys.argv)>1):
    file=sys.argv[1]
else:
    file="C:/Filepathtofile/Sample_1.dd" #The file to be read in case no argument passed

#Important Notes
#16 bytes row
#512 bytes sector

disktoRead=100000000 #Amount of bytes to be read, increasing this value can cause memory issues

#Codes
# 0 - Empty
# 1 - 12 bit FAT
# 4 - 16 bit FAT
# 5 - Ext MS-DOS Partition
# 6 - FAT-16 (32MB to 2GB) 
# 7 - NTFS
# B - FAT-32 (CHS) >> Legacy
# C - FAT-32 (LBA)
# E - FAT-16 (LBA)
partCodes=(
    "Empty","12-bit FAT","","","16 bit FAT","Ext MS-DOS Partition","FAT-16 (32MB to 2GB)",\
    "NTFS","","","","FAT-32 (CHS)","FAT-32 (LBA)","","FAT-16 (LBA)")
    
#User Interface
exit_flag=False #Exit flag
options = {1 : "List Partitions",
           2 : "Show Partitions Information",
           3 : "Exit"
           }

    
def get_sector(part):
    big_endian=part[8:12] #Get the Starting Sector
    big_endian.reverse()
    hexed=''.join(format(x, '02x') for x in big_endian)
    return int(hexed,16)
    
def get_partSize(part):
    big_endian=part[12:16] #Get the Partition Size
    big_endian.reverse()
    hexed=''.join(format(x, '02x') for x in big_endian)
    return int(hexed,16)

def get_partCode(part):
    return partCodes[part[4]]

def print_info(part):        
    print(f"Start Sector:{get_sector(part)} \nPartition Size:{get_partSize(part)} \nPartition Type:{get_partCode(part)}")
    return None

def get_FATInformation(part):
    volume=get_sector(part)*512-512  #(subtract 512 MBR)
    
    #Reserved Area bytes 15/16
    reserved_area=more_disk[volume+14:volume+16] #bytes 15/16 
    reserved_area.reverse()
    reserved_area=int(''.join(format(x, '02x') for x in reserved_area),16)
    print("Reserved Area: ",reserved_area) 
    
    #Fat Area size
    fat_area=more_disk[volume+22:volume+24] #bytes 23/24 31766 - 31768
    fat_area.reverse()
    fat_area=int(''.join(format(x, '02x') for x in fat_area),16)
    print("Fat Area: ",fat_area) 
    
    #Fat Copies
    fat_copies=more_disk[volume+16] #byte 17 31760
    print("Fat Copies: ",fat_copies)
    
    #Sectors per cluster 0D = 14
    per_cluster=more_disk[volume+13] #byte 14 31757
    print("Sectors Per Cluster: ",per_cluster)
    
    #Data Area - 2*512bytes
    data_area=get_sector(part_1)+reserved_area+fat_area*fat_copies
    print(f"Data Area is {data_area}")
    
    return data_area

#Directory Entry 32 bytes 
def directory_scan(data_area):
    directory_size=32 #32 bytes 
    start=(data_area*512)-512 #Start of root
    directory=[more_disk[start]]
    overflow=0 #Check in case the disk is incorrectly formatted.
    
    while(directory[0]!=0 and overflow<50):
        overflow+=1
        directory=more_disk[start:start+directory_size]
        directory_name=directory[0:11] #11 byte file name
        #print("Name: ",directory_name)
        print("Name: ",''.join(chr(x) for x in directory_name))
        start+=directory_size
        
        if(directory[0]==229): #229 = E5 File Deleted
            print("   Deleted File Information")
            deleted_info=directory[26:28]
            deleted_info.reverse()
            deleted_info=int(''.join(format(x, '02x') for x in deleted_info),16)
            print(f"   Starting Cluster: {deleted_info}")
            deleted_info=(deleted_info-2)*8+599
            print(f"   Starting Sector: {deleted_info}")
            
            deleted_size=directory[28:32]
            deleted_size.reverse()
            deleted_size=int(''.join(format(x, '02x') for x in deleted_size),16)
            print(f"   Size of file: {deleted_size} bytes")
            
            print("   First 16 Characters: ",''.join(chr(x) for x in more_disk[deleted_info*512-512:deleted_info*512-496]),"\n")
            #print(f"First 16 characters: {deleted_info}")          

    return None

def part_print(part_arr,flag=0):
    for p in partitions:
        if(flag==1):
            print(f"Partition {p}")
        else:
            print(f"\nPartition {p}")
            print_info(partitions[p])
    return None


#Open the disk image as bytes
raw=open(file,'rb')

#MBR is the first sector lets get the partitions
#446 bytes - Boot Code
mbr=list(raw.read(512))

part_1=mbr[446:462]#Partition 1 
part_2=mbr[462:478]#Partition 2 
part_3=mbr[478:494]#Partition 3 
part_4=mbr[494:510]#Partition 4 
partitions = {1 : part_1, 2: part_2,3 : part_3,4 : part_4} #Easier access

more_disk=list(raw.read(disktoRead)) #read further bytes 

#print(more_disk[volume:volume+512]) #31744 - 32256

#Close the file
raw.close()


for x in options:
    print (x,"-",options[x])
    
while(not exit_flag):
    user_select=input("Choose the option 1-3:")
    
    if(user_select=="1"):
        part_print(partitions)
    elif(user_select=="2"):
        print("Choose the partition 1-4:")
        part_print(partitions,1)
        part_select=int(input("Choose the partition 1-4:"))
        try:
            da=get_FATInformation(partitions[part_select])
        except ValueError: 
            print("Increase the disktoRead variable to a higher value")
            sys.exit()
        directory_scan(da)
    elif(user_select=="3"):
        exit_flag=True
    else:
        print("Please select a valid option")
    
    
