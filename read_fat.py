#!/usr/bin/python

import os
import re
import itertools
import array
import struct

#function to flip list of bytes in little endian
def to_big_en(byte_list,width):
	buf_list = list()	
	for i in range(width):	#switching bytes
		buf_list.append(byte_list[width-1-i])
	return buf_list

#get desired bits from list
def get_bytes(clean_list,width,indx):
	byte_list = list()
	for i in range(width):
		byte_list.append(clean_list[indx])
		indx+=1
	return byte_list

#clean up hexdump output
def clean_hexdump(filename):
	
	clean_list = list()
	read_ln = list()
	with open(filename) as f:

	#iterate through file per line
		for line in f:
			read_ln = line.split()	
			temp_list =  [i for ind,i in enumerate(read_ln) if(ind!= 0) if(ind < 17)]
			clean_list.append(temp_list)

	clean_list = list(itertools.chain(*clean_list))
	return clean_list


def calculate_offset(N_input):
	First_sec_of_File = Start_Data_sector + (N_input -2) * BPB_SecPerClus
	First_sec_offset = First_sec_of_cluster * BPB_bytsPerSec

	return First_sec_offset




def print_root(root_list):
	root_len = len(root_list)
	ent_offset = 0
	high_lfn=''
	while ent_offset < root_len:
		
		print("\n")
		buff =[]
		#check if long file name
		DIR_Attr = root_list[ent_offset+ 11]

		if( DIR_Attr != '0f'):
			
			for i in root_list[ent_offset+0  : ent_offset+11]:
				buff.append(chr(int('0x'+i,0)))
	
			DIR_Name = ''.join(buff)
			

			#exit if reached the empty line
			if(len(root_list[ent_offset+ 20: ent_offset+ 22]) == 0):
				break

			DIR_FstClusHI = to_big_en(root_list[ent_offset+ 20: ent_offset+ 22],2)
			DIR_FstClusLO = to_big_en(root_list[ent_offset+ 26: ent_offset+ 28],2)
			DIR_FileSize = to_big_en(root_list[ent_offset + 26: ent_offset+ 33],4)

			print('DIR_Name:',DIR_Name)
			print('DIR_Attr:',DIR_Attr)

			if(DIR_Attr == '10'):
				file_type = 'Sub-directory'
			elif(DIR_Attr == '20'):
				file_type = 'Actual File'
			elif(DIR_Attr == '08'):
				file_type = 'Volume ID'

			print('FILE-TYPE:',file_type)
 
			#print('DIR_ClusHI:{}\nDIR_ClusLO:{}'.format(DIR_FstClusHI,DIR_FstClusLO))

			#Pointer to next cluster
			DIR_clus = ''.join(DIR_FstClusHI) + ''.join(DIR_FstClusLO)
			DIR_clus = int('0x'+DIR_clus,0)
			DIR_FileSize = int('0x'+''.join(DIR_FileSize),0)
			print("File size:{} bytes".format(DIR_FileSize))
			print('DIR_Cluster Num: ',DIR_clus)
			print('Cluster Byte offset:{} or {}'.format(hex(calculate_offset(DIR_clus)), calculate_offset(DIR_clus)))
		
		elif( DIR_Attr == '0f'):

			
			#LFN[0-5]
			for i in root_list[ent_offset+1  : ent_offset+11]:
				buff.append(chr(int('0x'+i,0)))


			#LFN[6-11]
			for i in root_list[ent_offset+14  : ent_offset+26]:
				if(i == 'ff'):  #avoid trash character
					break
				buff.append(chr(int('0x'+i,0)))




			#LFN[12-13]
			for i in root_list[ent_offset+28  : ent_offset+32]:
				if(i == 'ff'): #avoid trash character
					break				
				buff.append(chr(int('0x'+i,0)))

			DIR_Name = ''.join(buff)
			
			if(root_list[0+ent_offset] == '01'):
				high_lfn =DIR_Name
			elif(root_list[0+ent_offset] == '41'):
				whole_lfn = DIR_Name
				print('LFN:',whole_lfn)
				print('LFN checksum:',root_list[13+ent_offset])
			elif(root_list[0+ent_offset] == '42'):
				whole_lfn = high_lfn + DIR_Name
				print('LFN:',whole_lfn)
				print('LFN checksum:',root_list[13+ent_offset])				
			
			
			
		ent_offset += 32

def dump_file(N,file_size):

	
	First_sec_of_File = Start_Data_sector + (N -2) * BPB_SecPerClus
	File_offset = First_sec_of_File * BPB_bytsPerSec


	cmd = 'sudo dd if={} ibs=1 count={} skip={} > file_cont.raw'.format(DEV_Name,file_size,File_offset)
	print('command is:',cmd)
	os.system(cmd)
	os.system('hexdump -C file_cont.raw > file_cont.txt') #printing 32-bit fat entry
	os.system('cat file_cont.txt')

def parse_subdir(N):
	#read subdir

	dir_width = 4*1024  #read 4kb bytes               
	First_sec_of_cluster = Start_Data_sector + (N -2) * BPB_SecPerClus
	First_sec_offset = First_sec_of_cluster * BPB_bytsPerSec


	cmd = 'sudo dd if={} ibs=1 count={} skip={} > sub_dir.raw'.format(DEV_Name,dir_width,First_sec_offset)
	print('command is:',cmd)
	os.system(cmd)
	os.system('hexdump -C sub_dir.raw > sub_dir.txt') #printing 32-bit fat entry
	os.system('cat sub_dir.txt')

	root_list=clean_hexdump('sub_dir.txt')

	print_root(root_list)


def parse_fat(fat_list):
	fat_len = len(fat_list)
	ent_num = 0
	fat_offset = ent_num * 32
	
	while fat_offset < fat_len:
		buff = []
		
		fat_val = '0x' + ''.join(fat_list[0 + fat_offset : 5 + fat_offset])
		fat_val = int(fat_val,0) & 0xFFFFFFF
		print("Cluster{}: {}=>{}".format(ent_num , hex(fat_val),fat_val))
		ent_num += 1
		fat_offset = ent_num * 32
		
		

	
		

#------------------Main script----------------------------
print("Note: this script assumes that sd card is formatted in FAT32 and is recognized as /dev/sdb1")
DEV_Name = '/dev/sdb1'
offset = int('0x0' ,0)
print('Offset is: '+str(offset))

#read from sd card
cmd = 'sudo dd if={} bs=512 count=1 skip={} >temp.raw'.format(DEV_Name,offset)
print(cmd)
os.system(cmd)

#dump hex into textfile
cmd = 'hexdump -C temp.raw > boot_part.txt'
print(cmd)
os.system(cmd)


#instantiate new lists
clean_list = list()
read_ln = list()


#------------get hexdump output for parsing--------------------

clean_list = clean_hexdump('boot_part.txt')

#-------------get info from boot cluster------------------------

#relevant info to retrieve

BytsPerSec_indx = 11     #BPB_BytsPerSec offset
BPB_RsvdSecCnt_indx = 14 #BPB_RscvdSecCnt offset
BPB_SecPerClus_indx = 13 #BPB_SecPerClus offset      
BPB_NumFATs_indx = 16    #BPB_NumFATs offset
BPB_TotSec32_indx = 32   #Total number of sectors
BPB_FATSz32_indx = 36    #Size of FAT sectors
BPB_RootClus_indx = 44   #First cluster number of root

BPB_RootClus_width = 2
BPB_SecPerClus_width = 1
BPB_TotSec32_width = 4
BPB_RootEntCnt_width = 2
BPB_FATSz32_width = 4
BPB_NumFATs_width = 1
RsvdSecCnt_width = 2
BytsPerSec_width = 2



#-----------------get Bytes Per sector-------------------
lil_e = get_bytes(clean_list,BytsPerSec_width, BytsPerSec_indx)

big_e = to_big_en(lil_e, BytsPerSec_width)

big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_bytsPerSec = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []


#---------------getting Reserved Sector Count---------------
lil_e = get_bytes(clean_list,RsvdSecCnt_width,BPB_RsvdSecCnt_indx)
big_e = to_big_en(lil_e,RsvdSecCnt_width)

big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_RsvdSecCnt = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []

#-------------------getting FAT size-------------------
lil_e = get_bytes(clean_list,BPB_FATSz32_width,BPB_FATSz32_indx )
big_e = to_big_en(lil_e,BPB_FATSz32_width)

big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_FATSz = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []


#------------------getting Number of FAT--------------
lil_e = get_bytes(clean_list,BPB_NumFATs_width,BPB_NumFATs_indx )
big_e = to_big_en(lil_e,BPB_NumFATs_width)


big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_NumFAT = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []

#------------------getting Total Sectors-----------
lil_e = get_bytes(clean_list,BPB_TotSec32_width,BPB_TotSec32_indx)
big_e = to_big_en(lil_e,BPB_TotSec32_width)


big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_TotSec32 = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []



#---------------getting Sectors Per Cluster---------
lil_e = get_bytes(clean_list,BPB_SecPerClus_width,BPB_SecPerClus_indx)
big_e = to_big_en(lil_e,BPB_SecPerClus_width)


big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_SecPerClus = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []

#---------------Root Dir Cluster number-------------

lil_e = get_bytes(clean_list,BPB_RootClus_width, BPB_RootClus_indx)

big_e = to_big_en(lil_e, BPB_RootClus_width)

big_en = list(itertools.chain(*big_e)) #join retrieved bits
big_en_str = '0x'+''.join(big_en)      #turn into hex string


BPB_RootClus = int(big_en_str,0)
big_e = []                             #clear containers
big_en = []
lil_e = []




print('BPB_NumFats: {}'.format(BPB_NumFAT))
print('BPB_FATSz32: {}'.format(BPB_FATSz))
print('BPB_bytsPerSec: {}'.format(BPB_bytsPerSec))
print('BPB_RsvdSecCnt: {}'.format(BPB_RsvdSecCnt))
print('BPB_TotSec32: {}'.format(BPB_TotSec32))
print('BPB_SecPerClus: {}'.format(BPB_SecPerClus))

Start_Fat_sector = BPB_RsvdSecCnt
Tot_fat_sec = BPB_FATSz * BPB_NumFAT


Start_Data_sector = Start_Fat_sector + Tot_fat_sec
Tot_data_sec = BPB_TotSec32 - Start_Data_sector

count_of_clusters = Tot_data_sec / BPB_SecPerClus

                                       #confirming FAT type
if count_of_clusters >= 65526:
	print('its fat32 with clusters: ',count_of_clusters)
else:
	print('not fat32')


print('FAT offset: {} \nFAT size: {}'.format(Start_Fat_sector,Tot_fat_sec))
print('Data offset: {}\nData size: {}'.format(Start_Data_sector,Tot_data_sec))



#-------------------Retrieving FAT entries-----------
                   #Equation for first sector of N'th fat entry:
'''
N = 0              #FAT[N]
entry_width =  BPB_FATSz    #width of each FAT32 entry
read_mask = 0x0FFFFFF8

print('read mask: ',hex(read_mask))

Fat_sec_num = Start_Fat_sector+ int( N*4 / BPB_bytsPerSec)
Fat_ent_offset = (N*4) % BPB_bytsPerSec


cmd = 'sudo dd if={} ibs=1 count={} skip={} > fat.raw'.format(DEV_Name,entry_width,Start_Fat_sector)
print('command is:',cmd)
os.system(cmd)
os.system('hexdump -C fat.raw > fat_list.txt') #printing 32-bit fat entry


fat_list = clean_hexdump('fat_list.txt')
#print(fat_list)

#parse_fat(fat_list)

'''


#------------------Retrieving Root Dir--------------


print('\nReading root directory.......')


root_width = 512   #in bytes
N = BPB_RootClus   #root cluster

First_sec_of_cluster = Start_Data_sector + (N -2) * BPB_SecPerClus
First_sec_offset = First_sec_of_cluster * BPB_bytsPerSec


cmd = 'sudo dd if={} ibs=1 count={} skip={} > fat.raw'.format(DEV_Name,root_width,First_sec_offset)
print('command is:',cmd)
os.system(cmd)
os.system('hexdump -C fat.raw > root_dir.txt') #printing 32-bit fat entry
#os.system('cat root_dir.txt')


root_list=clean_hexdump('root_dir.txt')
print("\n------------ |CONTENTS OF ROOT DIR|-----------")
print_root(root_list)
print("\n------------ |END  OF ROOT DIR|---------------\n")


opt = input("Menu:\n[1]Access File (Hexdump)\n[2]Access Sub-directuory\n[3]Exit\n   Option:")
#----------------Retrieving arbitrary sub directory----------
if(opt =='2'):
	
	clusNum =input("Please Enter Directory Cluster Number: ")	
	print('\n----------|Printing Sub DIR|-------------\n')	

	try:	
		parse_subdir(int(clusNum))
	except:
		print("Error: Invalid cluster number")

	print('\n---------|Done Printing Sub DIR|-------------\n')	

elif(opt == '1'):
	filesz = input("Please Input File size: ")
	file_clusNum = input("Please Input File cluster number: ")

	print("Reading at byte offset:",calculate_offset(int(file_clusNum)))
	dump_file(int(file_clusNum),int(filesz))
	#parse_subdir(int(file_clusNum))
 
