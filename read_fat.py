#!/usr/bin/python

import os
import re
import itertools
import array
import struct

rootdir_byte_offset = 0 #global

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


#clean up fat hexdump output
def clean_fat(filename):
	clean_fat = list()
	read_fatln = list()
	with open(filename) as f_fat:
		for line in f_fat:
			read_fatln = line.split()
			temp_fatln = [i for ind,i in enumerate(read_fatln) if(ind!=0) if(ind < 5)]
			clean_fat.append(temp_fatln)
	clean_fat = list(itertools.chain(*clean_fat))
	return clean_fat


#Note: this only calculates the byte offset of data in the DATA REGION
def calculate_offset(N_input):
	First_sec_of_File = Start_Data_sector + (N_input-2) * BPB_SecPerClus
	File_offset = First_sec_of_File * BPB_bytsPerSec
	return File_offset




def print_root(root_list):
	root_len = len(root_list)
	ent_offset = 0
	high_lfn=''
	LFN_complete = False #LFN search flag
	LFN_ended = False
	LFN_start = False
	LFN_reverse = False
	LFN =[]
			

	while ent_offset != root_len:
		print("\n")
		buff =[]
		

		#Skip files marked unused
		if(root_list[ent_offset+0]=='e5'):
			ent_offset += 32			
			continue
	
		#check Attribute if long file name
		DIR_Attr = root_list[ent_offset+ 11]

		
		

		if( DIR_Attr != '0f'):
			
			for i in root_list[ent_offset+0  : ent_offset+11]:
				buff.append(chr(int('0x'+i,0)))
	
			DIR_Name = ''.join(buff)
			

			#exit if reached the empty line
			if(len(root_list[ent_offset+ 20: ent_offset+ 22]) == 0):
				break

			DIR_FstClusHI = to_big_en(root_list[ent_offset+ 20: ent_offset+ 22],2)
			DIR_FstClusLO = to_big_en(root_list[ent_offset+ 26: ent_offset+ 29],2)
			DIR_FileSize = to_big_en(root_list[ent_offset + 28: ent_offset+ 32],4)

			print('DIR_Name:',DIR_Name)
			print('DIR_Attr:',DIR_Attr)
			
			if(DIR_Attr == '10'):
				file_type = 'Sub-directory'
			elif(DIR_Attr == '20'):
				file_type = 'Actual File'
			elif(DIR_Attr == '08'):
				file_type = 'Volume ID'

			print('FILE-TYPE:',file_type)

			#Pointer to next cluster
			DIR_clus = ''.join(DIR_FstClusHI) + ''.join(DIR_FstClusLO)
			DIR_clus = int('0x'+DIR_clus,0)
			DIR_FileSize = int('0x'+''.join(DIR_FileSize),0)
			print("File size:{} bytes".format(DIR_FileSize))
			print('Content_DIR_Cluster Num: ',DIR_clus)
			print('Content_Byte offset:{} '.format(calculate_offset(DIR_clus)))
			print('Content_512-block sized offset:{}'.format(int((calculate_offset(DIR_clus))/512)))

			if record:

				if not LFN_start or not LFN_reverse:
					os.system('echo  >> files.log')
				os.system('echo DIR_Name: {} >> files.log'.format(DIR_Name))
				os.system('echo Attr: {} >> files.log'.format(DIR_Attr))
				os.system('echo FILE-TYPE: {} >> files.log'.format(file_type))
				os.system("echo File size:{} bytes >> files.log".format(DIR_FileSize))
				os.system('echo Content_DIR_Cluster Num:{} >>files.log'.format(DIR_clus))
				os.system('echo Content_Byte offset hex:{}  >>files.log '.format(calculate_offset(DIR_clus) + ent_offset))
				os.system('echo Content_512-block sized offset:{} >>files.log'.format(int((calculate_offset(DIR_clus)+ent_offset)/512)))

		elif( DIR_Attr == '0f'):

			#LFN[0-5]
			for i in root_list[ent_offset+1  : ent_offset+11]:
				buff.append(chr(int('0x'+i,0)))


			#LFN[6-11]
			for i in root_list[ent_offset+14  : ent_offset+27]:
				if(i == 'ff'):  #avoid trash character
					break
				buff.append(chr(int('0x'+i,0)))

			#LFN[12-13]
			for i in root_list[ent_offset+28  : ent_offset+32]:
				if(i == 'ff'): #avoid trash character
					break				
				buff.append(chr(int('0x'+i,0)))

			DIR_Name_LFN = ''.join(buff)
			#print(DIR_Name_LFN,root_list[0+ent_offset])
			seqNum = int(root_list[0+ent_offset][1])
			
			seqNum_stat = int(root_list[0+ent_offset][0])
			#print('seqNum',seqNum)

			if(seqNum_stat == 4 and LFN_start):	  #Encountered last part of lfn last
				#record lfn normally
				LFN.append(DIR_Name_LFN)
				LFN_ended = True
				LFN_complete = True

			elif(seqNum_stat == 4 and not LFN_start): #Encountered last part of lfn first
				#record lfn in reverse
				LFN.append(DIR_Name_LFN)
				LFN_reverse = True
				if(seqNum == 1):
					LFN_ended = True
					LFN_complete = True
				else:
					LFN_ended = False
					LFN_complete = False
				
			elif(LFN_reverse):
				LFN.insert(0,DIR_Name_LFN)
				if(seqNum == 1):
					LFN_ended = True
					LFN_complete = True
				
				
			
			else:
				LFN.append(DIR_Name_LFN)
				LFN_start = True				
				
				

			if(LFN_ended and LFN_complete):
				print('LFN:',''.join(LFN))
				LFN_str = ''.join(LFN)

				if record:
					with open('files.txt','a') as f_out:
						f_out.write('\nLFN:{} \n'.format(LFN_str))				
				LFN = []				
				LFN_complete = False
				LFN_ended = False
				LFN_reverse = False
				LFN_start = False
				
		ent_offset += 32
			
			
		
#Note: LFNs might not be matched

def dump_file(N,file_size):

	dump_offset = calculate_offset(N)
	cmd = 'sudo dd if={} ibs=1 count={} skip={} status=none > file_cont.raw'.format(DEV_Name,file_size,dump_offset)
	print('command is:',cmd)
	os.system(cmd)
	os.system('hexdump -C file_cont.raw > file_cont.txt') #printing 32-bit fat entry
	os.system('cat file_cont.txt')

def parse_subdir(N):
	#read subdir

	dir_width = BPB_bytsPerSec * BPB_SecPerClus  #read 1 cluster worth of data               
	

	First_sec_offset = calculate_offset(N)
	cmd = 'sudo dd if={} ibs=1 count={} skip={} status=none > sub_dir.raw'.format(DEV_Name,dir_width,First_sec_offset)
	print('command is:',cmd)
	os.system(cmd)
	os.system('hexdump -C sub_dir.raw > sub_dir.txt') #printing 32-bit fat entry
	os.system('cat sub_dir.txt')

	sub_list=clean_hexdump('sub_dir.txt')

	print_root(sub_list)


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
		
def get_fat_en(Nth):
	#-------------------Retrieving FAT entries-----------
                   #Equation for first sector of N'th fat entry:


	N = Nth              #FAT[N]
	entry_width = 4    #4bytes = 32bits


	Fat_sec_num = Start_Fat_sector+ int( N*4 / BPB_bytsPerSec)
	Fat_ent_offset = (N*4) % BPB_bytsPerSec + Start_Fat_offset


	cmd = 'sudo dd if={} ibs=1 count={} skip={} status=none > fat.raw'.format(DEV_Name,entry_width,Fat_ent_offset)
	#print('command is:',cmd)
	os.system(cmd)
	os.system('hexdump -C fat.raw > fat_list.txt') #printing 32-bit fat entry
	#os.system('cat fat_list.txt')
	fat_list = clean_fat('fat_list.txt')

	big_en_fat = to_big_en(fat_list,4)
	fat_en = '0x'+''.join(big_en_fat)

	return int(fat_en,0)

		
def clean_files():
	os.system('sudo rm -f file_* fat* root_* root* sub_* boot_* temp*')





class fat_obj:			#class for sorting through the fat
	#flen =0
	#fnum =0
	#first_sec=''
	chain=[]

	def __init__(self,fnum,flen,first_sec): 
		self.fnum = fnum	#int
		self.flen = flen	#int
		self.first_sec = first_sec	#hex string 
		self.chain.append(first_sec) 	#hex string

	def add_to_chain(clus_num):
		chain.append(clus_num)
		flen += 1	
	



def make_new_files(fileName,DEV_Name_in):

	file_num = 0
	buff = DEV_Name_in.split('/')
	partition = buff.pop()
	
	cmd = 'lsblk > devices.txt'
	os.system(cmd)

	cmd = 'grep {} devices.txt > dev_dir.txt'.format(partition)
	os.system(cmd)

	f_devdir = open('dev_dir.txt','r')
	buff = f_devdir.read()
	f_devdir.close()

	buff = buff.split()
	dir_str = buff.pop() + '/'
	print(dir_str)

	dir_optn = input('Make new Subdirectory?\n[1]Yes\n[2]No\n Option: ')

	if dir_optn == '1':
		subdir_str = input('\nEnter sub-directory name: ')
		subdir_str = subdir_str + '/'
		os.system('mkdir {}{}'.format(dir_str,subdir_str))

		while file_num < 10:
			f_o = open(dir_str+subdir_str+fileName + str(file_num) + '.txt','w+')
			f_o.write('tesstingggg')
			f_o.close()
			file_num += 1

	elif dir_optn == '2':
		while file_num < 10:
			f_o = open(dir_str+fileName + str(file_num) + '.txt','w+')
			f_o.write('tesstingggg')
			f_o.close()
			file_num += 1
	else:
		print('invalid')


	
	


def get_all_fat():
	print('\nReading FAT')
	cmd = 'sudo dd if={} ibs=1 count={} skip={} status=progress > All_fat.raw'.format(DEV_Name,BPB_FATSz32*BPB_bytsPerSec,Start_Fat_offset)
	print('FAT Command:',cmd)
	os.system(cmd)
	os.system('hexdump -C All_fat.raw > All_fat.txt')

	#get all fat entries
	fat_bytes = clean_hexdump('All_fat.txt')
	
	return fat_bytes



def sort_fat(all_fat_list):
	cur_clus = 0
	clus_count = 0
	file_num = 0
	fat_ent = []
	buff = []

	while cur_clus < len(all_fat_list):
		
		#print(file_num)
		N_fat_entry = cur_clus
		entry_val = all_fat_list[N_fat_entry+0:N_fat_entry+4]       #get_bytes(all_fat_list,4,4*N_fat_entry)
		big_en_val = to_big_en(entry_val,4)
		fat_val = '0x'+''.join(big_en_val)

		if fat_val == '0x0fffffff':
			buff.append(fat_val)			#record file cluster chain
			fat_ent.append(buff)
			buff = []	
			
		elif fat_val == '0x0ffffff7'or fat_val == '0x00000000':    #not bad cluster or free 
			#do nothing
			cur_clus += 4
			continue
		else:
			buff.append(fat_val)			#append to chain
				
		clus_count += 1
		cur_clus += 4
		

	print('Num Entries: {} , last cluster: {}'.format(len(fat_ent),clus_count))
	filesz = 0
	for e in fat_ent:
		filesz = (len(e)*BPB_bytsPerSec*BPB_SecPerClus)
		if filesz > 10**3 and filesz < 10**6 :
			sz_str = 'kb'
			filesz *= 1/10**3

		elif filesz > 10**6:
			sz_str = 'Mb'
			filesz *= 1/10**6
		else:
			sz_str = 'bytes'

		print('File[{}] Cluster Size: {} {}'.format(file_num,filesz,sz_str))
		file_num += 1				
		

#------------------Main script----------------------------
#print("Note: this script assumes that sd card is formatted in FAT32 and is recognized as /dev/sdb1")


DEV_Name = input('please input device name (i.e: /dev/sdb1): ')

while True:
	record_optn = input('Record output?\n[1]Yes\n[2]No\n Option:')
	if record_optn == '1':
		record = True
		break
	elif record_optn == '2':
		record = False
		break
	else:
		print('Invalid option, please try again\n')
		continue


offset = int('0x0' ,0)
print('\nReading Boot sector')
#read from sd card
cmd = 'sudo dd if={} bs=512 count=1 skip={} status=none >temp.raw'.format(DEV_Name,offset)
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


BPB_FATSz32 = int(big_en_str,0)
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


print('\nBPB_NumFats: {}'.format(BPB_NumFAT))
print('BPB_FATSz32: {}'.format(BPB_FATSz32))
print('BPB_bytsPerSec: {}'.format(BPB_bytsPerSec))
print('BPB_RsvdSecCnt: {}'.format(BPB_RsvdSecCnt))
print('BPB_TotSec32: {}'.format(BPB_TotSec32))
print('BPB_SecPerClus: {}'.format(BPB_SecPerClus))

Start_Fat_sector = BPB_RsvdSecCnt     #Byte offset
Start_Fat_offset = Start_Fat_sector * BPB_bytsPerSec
FAT_area_sec = BPB_FATSz32 * BPB_NumFAT


Start_Data_sector = Start_Fat_sector + FAT_area_sec
Tot_data_sec = BPB_TotSec32 - Start_Data_sector

count_of_clusters = Tot_data_sec / BPB_SecPerClus

                                       #confirming FAT type

print('FAT sector: {} \nFAT size: {}'.format(Start_Fat_sector,FAT_area_sec))
print('Data offset: {}\nData size: {}'.format(Start_Data_sector,Tot_data_sec))


#-------------------Get All FAT------------------

all_fat_list = get_all_fat()
sort_fat(all_fat_list)


#------------------Retrieving Root Dir--------------


print('\nReading root directory.......')


root_width = BPB_bytsPerSec * BPB_SecPerClus   #in bytes
N = BPB_RootClus   #root cluster

First_sec_of_cluster = Start_Data_sector + (N -2) * BPB_SecPerClus
First_sec_offset = First_sec_of_cluster * BPB_bytsPerSec


cmd = 'sudo dd if={} ibs=1 count={} skip={} status=none > root.raw'.format(DEV_Name,root_width,First_sec_offset)
print('command is:',cmd)
os.system(cmd)
os.system('hexdump -C root.raw > root_dir.txt') #printing 32-bit fat entry



root_list=clean_hexdump('root_dir.txt')
print("\n------------ |CONTENTS OF ROOT DIR|-----------")
print_root(root_list)
print("\n------------ |END  OF ROOT DIR|---------------\n")


#----------------Retrieving arbitrary sub directory----------
while True:
	opt = input("Menu:\n[1]Access File (Hexdump)\n[2]Access Sub-directuory\n[3]Back to Root\n[4]Make Empty Files\n[5]Exit\n   Option:")

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
		
	elif(opt == '3'):
		print('\n----------|Printing Root DIR|-------------\n')	
		parse_subdir(2)
		print('\n---------|Done Printing Root DIR|----------\n')
	elif(opt == '4'):
		print('\n---------|Making new Empty Files|----------\n')
		make_new_files('Empty',DEV_Name)	
	elif(opt == '5'):
		clean_files()		
		exit()
	else:
		
		print("Invalid option, please try again\n")
		pass

