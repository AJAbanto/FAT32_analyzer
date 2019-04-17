#!/usr/bin/python

import os
import re
import itertools
import array
import binascii
import struct
import pprint
DEV_Name = '/dev/sdb1'
#DEV_Name = 'sd_.img'
offset = int('0x0' ,0)
print('Offset is: '+str(offset))

#read from sd card
cmd = 'sudo dd if={} bs=512 count=1 skip={} >temp.raw'.format(DEV_Name,offset)
print(cmd)
os.system(cmd)

#dump hex into textfile in little endian format'
cmd = 'hexdump -C temp.raw > boot_part.txt'
print(cmd)
os.system(cmd)


#instantiate new lists
clean_list = list()
read_ln = list()


#--------get hexdump output for parsing--------------
with open('boot_part.txt') as f:

	#iterate through file per line
	for line in f:
		read_ln = line.split()	
		temp_list =  [i for ind,i in enumerate(read_ln) if(ind!= 0) if(ind < 17)]
		clean_list.append(temp_list)

clean_list = list(itertools.chain(*clean_list))

#-------------get MFT cluster------------------------
indx_hex = '0x30' 
indx = int(indx_hex,0)
width = 8

hex_str =''
chr_str =''
byte_list=list()

#get desired bits from list
for i in range(width):
	byte_list.append(clean_list[indx])
	indx+=1

print(hex_str)		#print little endian hex string
print('lil e', byte_list)	#print byte list

buf_list = list()	
for i in range(width):	#switching bytes
	buf_list.append(byte_list[width-1-i])
	
print('big e', buf_list)

big_en = list(itertools.chain(*buf_list))
big_en_str = '0x'+''.join(big_en)
#print(big_en_str)

mft_offset = int(big_en_str,0)
print('MFT offset: ',mft_offset)

#-----------get Sectors_in_claster cluster---------
indx_hex = '0x0d' 
indx = int(indx_hex,0)

hex_str = clean_list[indx] #index Sectors per cluster since only 1 byte long
S_in_c = int('0x'+hex_str,0)
print('Sectors per cluster: ', S_in_c)
print('MFT table offset:',S_in_c*mft_offset)

mft_tot_offset = S_in_c * mft_offset

#-----------retreaving actual MFT Table(1kb)------------

cmd = 'sudo dd if={} ibs=512 count=200 skip={} >MFT.raw'.format(DEV_Name,mft_tot_offset)
print(cmd)
os.system(cmd)

#for debugging
os.system('hexdump -C MFT.raw > MFT.txt')
#os.system('cat MFT.txt')



#-----------------open hexdump of MFT--------------------

New_entry = False #Flag for new entry

#Entry containers
MFT= list()
new_cont = list()


print('Retrieving clusters')
with open('MFT.txt') as f_o :

	for line in f_o:
				
		splitted = line.split()
		if any("FILE0" in s for s in splitted):
			#print('\n New entry \n')			
			MFT.append(new_cont)	#append to record
			new_cont = []			#clear entry
			new_cont.append(splitted)	#append new entry to container
		else:
			new_cont.append(splitted)
			#print('recording')
		#print(splitted)


#check how many lines till filename
z = 0
for i in MFT[7]:
	if any("$" in s for s in i):
		print(i)
		break
	z += 1	
	

print('num of lines before filename:{}'.format(z))

# through tests We found $AttrDef at MFT[5]
#confirming:
'''
for i in MFT[5]:
	print(i)
'''






 
