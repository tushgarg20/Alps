# -*- coding: utf-8 -*-
"""
Created on Tue Jun  5 17:52:34 2018

@author: santoshn
"""
import gzip
import re

#Extract the instruction count from the opcode line
def instr_count(line):
    instr = re.search("\s\d+\s|$", line).group()
    if instr:
      instr_cnt = int(instr)
    else:
      instr_cnt = 0
    return(instr_cnt)
    
def all_same(items):
    return all(x == items[0] for x in items)

   
#Stride pattern extractor from an opcode line
#Input arguments: Line from the .stat file, Index --> 1:DST,2:SRC0,3:SRC1,4:SRC2     
def stride_pattern_extractor(line, pos):
    di = {}     
    if '<' in line:
        l = line.replace('>','<').split('<')
        for position in range(1,len(l),2):
            flag = False
            vals = l[position].replace(';',',').split(',')
            for digit in '0123456789':
                if digit in vals:
                    flag = True
            if flag:
                di[(position+1)//2] = l[position].replace(';',',').split(',')
    test = di.get(pos)
    if test:
       pattern = [int(x) for x in test]
    else:
        pattern = []
    num_elements = len(pattern)
    return(num_elements, pattern)

#Extract the exec size flag
#0:SIMD8, 1:SIMD16
def extract_exec_size(line):
    simd8_flag = 0
    simd16_flag = 0
    exec_size = re.findall("\(\d+\)", line)
    if exec_size == ['(8)']:
       simd8_flag = 1
    if exec_size == ['(16)']:
       simd16_flag = 1
    return(simd8_flag, simd16_flag)   


# =============================================================================
# with open("Instr_snapshot_test.txt","r") as f:
#             gSimFile = f.readlines()
# datatype_sw_count = 0 
# total_opcode_count = 0
# exp_list = r"(mad|mac|mul|add|mov)\s+\(\d+\)"
# #opcode_expr = r"(mov|mad|mul|add|mac|or|not|send|sends|math|cmp)\s+\(\d+\)"
# opcode_expr = r"\w+\s+\(\d+\)"
# opcode_list = r":(hf|f)"
# exp1 = r"<(\d+); ?(\d+),(\d+)>"
# exp2 = r"\d+"
# pattern_count = 0
# for line in gSimFile:
#     instr_cnt = instr_count(line)
#     print(instr_cnt)
#     if instr:
#         instr_cnt = int(instr)
#         print(instr_cnt)
#     for m in re.findall(exp2, line):  # find all patterns
#             #pattern = map(int, m)                            # convert to int
#             #pattern = [int(x) for x in m]
#             pattern_count += 1
#             print(m)
#     for m in re.findall("<(\d+); (\d+)>", line):  # find all patterns
#             #pattern = map(int, m)                            # convert to int
#             pattern = [int(x) for x in m]
#             print(pattern)
# 
# curr_datatype = []
# last_hf_flag = 0
# total_opcode_count = 0
# no_of_lines = len(gSimFile)
# for line in gSimFile:
#     if re.search(opcode_expr, line):
#        total_opcode_count += 1   
#        #Extract all the individual dataypes of the source and dest operands
#        curr_datatype = re.findall(opcode_list, line)
#        hf_flag = all(x == ':hf' for x in curr_datatype)# Datatype is HF if all operands are HF
#        #Check if there a switch from HF to F 
#        if last_hf_flag == 1 and hf_flag == 0:
#            datatype_sw_count += 1
#        last_hf_flag = hf_flag   
# dtype_sw_percentage = datatype_sw_count/total_opcode_count
# #return(datatype_sw_count, dtype_sw_percentage)
# =============================================================================

#Estimates the number and percentage of opcode switches that 
#have an impact on Cdyn power. mul, mac, mad and add opcodes
#in FPU units of EU are considered in this computation
def opcode_switch_count_estimator(file):
    with gzip.open(file,"rb") as f:
            gSimFile = f.readlines()
    opcode_sw_count = 0 
    total_opcode_count = 0
    opcode_count = 0
    last_opcode_count = 0
    mad_mul_sw = 0
    mul_mad_sw = 0
    mad_add_sw = 0
    add_mad_sw = 0
    exp_list = r"(mad|mac|mul|add)\s+\(\d+\)"
    opcode_list = r"(mad|mac|mul|add)"
    curr_opcode = []
    last_opcode = []
    for line in gSimFile:
        line = line.strip().decode('ascii')
        #Estimate the opcode count
        opcode_count = instr_count(line)
        total_opcode_count += opcode_count
        if re.search(exp_list, line):
           #total_opcode_count += 1   
           curr_opcode = re.findall(opcode_list, line)
           #Whether there is an opcode switch
           if last_opcode != curr_opcode and last_opcode != []:
               opcode_sw_count += min(opcode_count, last_opcode_count)
               if last_opcode == ['mad'] and curr_opcode == ['mul']:
                   mad_mul_sw += min(opcode_count, last_opcode_count)
               if last_opcode == ['mul'] and curr_opcode == ['mad']:
                   mul_mad_sw += min(opcode_count, last_opcode_count)
               if last_opcode == ['mad'] and curr_opcode == ['add']:
                   mad_add_sw += min(opcode_count, last_opcode_count)
               if last_opcode == ['add'] and curr_opcode == ['mad']:
                   add_mad_sw += min(opcode_count, last_opcode_count)
           last_opcode = curr_opcode
           last_opcode_count = opcode_count
    opcode_sw_percentage = opcode_sw_count/total_opcode_count
    mad_mul_percent = (mad_mul_sw + mul_mad_sw)/total_opcode_count
    mad_add_percent = (mad_add_sw + add_mad_sw)/total_opcode_count
    return(opcode_sw_count, opcode_sw_percentage, mad_mul_percent, mad_add_percent)
   

#Estimates the number and percentage of datatype switches that 
#have an impact on Cdyn power. mul, mac, mad and add opcodes
#in FPU units of EU are considered in this computation
def datatype_switch_count_estimator(file):
    with gzip.open(file,"rb") as f:
            gSimFile = f.readlines()
    datatype_sw_count = 0 
    total_opcode_count = 0
    last_opcode_count = 0
    opcode_count = 0
    exp_list = r"(mad|mac|mul|add|mov)\s+\(\d+\)"
    opcode_list = r":(hf|f)"
    curr_datatype = []
    last_hf_flag = 0
    for line in gSimFile:
        line = line.strip().decode('ascii')
        #Estimate the opcode count
        opcode_count = instr_count(line)
        total_opcode_count += opcode_count
        if re.search(exp_list, line):
           #Extract all the individual dataypes of the source and dest operands
           curr_datatype = re.findall(opcode_list, line)
           #print(curr_datatype)
           hf_flag = all(x == ':hf' for x in curr_datatype)# Datatype is HF if all operands are HF
           #Check if there a switch from HF to F 
           if last_hf_flag == 1 and hf_flag == 0:
               datatype_sw_count += min(opcode_count, last_opcode_count)
           last_hf_flag = hf_flag
           last_opcode_count = opcode_count
    dtype_sw_percentage = (datatype_sw_count)/total_opcode_count
    return(datatype_sw_count,dtype_sw_percentage)
    

# =============================================================================
# #    raw_mov = all(x == m[0] for x in m)
# #    if raw_mov:
# #        raw_mov_count +=1
#         #oneLine.extend(m)
#         
# #    lines.append(oneLine)    
#         
# 
# #Swizzle detector framework
# 
# import re
# 
# #Swizzle count detector function
# def swizzle_count_estimator(file):
#     #Read the file 
#     with open(file,"r") as f:
#         gSimFile = f.readlines()
#     lines = []    # all the line results 
#     pattern = []
#     swizzle_count = 0 
#     total_opcode_count = 0
#     opcode_expr = r"\w+\s+\(\d+\)"
#     for line in gSimFile:  # go over each line
#         oneLine = []       # matches for one line 
#         swizzle_flag = 0   # Reset the flag to detect swizzle in next line
#         if re.search(opcode_expr, line):
#             total_opcode_count +=1
#         #Detect and analyze all the <VS; W, HS> patterns and look for swizzle or Scalar
#         for m in re.findall("<(\d+); ?(\d+),(\d+)>", line):  # find all patterns
#             # convert to int
#             pattern = [int(x) for x in m] #convert to integer
#             #Any regioning that is not flat involves a swizzle
#             if pattern[0] != pattern[1]*pattern[2] and (pattern != [1,1,0] ):
#                 swizzle_flag = 1
#             #Scalar case as well
#             if pattern == [0,1,0]:
#                 swizzle_flag = 1
#             
#             oneLine.extend(map(int,m))
#         #Detect and analyze all the <VS; HS> patterns and look for swizzle or Scalar
#         for m in re.findall("<(\d+); ?(\d+)>", line):  # find all patterns
#             pattern = [int(x) for x in m]
#             #Any regioning that is not flat involves a swizzle
#             if pattern[0] != 8 or pattern[1] != 1:
#                 swizzle_flag = 1
#             oneLine.extend(map(int,m))
#         #Detect and analyze all the <W> patterns and look for swizzle or Scalar
#         for m in re.findall("<(\d)>", line):  # find all patterns
#             pattern = [int(x) for x in m]
#             #Any regioning that is not flat involves a swizzle
#             if pattern[0] != 1:
#                 swizzle_flag = 1
#             oneLine.extend(map(int,m))                       # convert to int, extend oneLine
#         if swizzle_flag:
#            swizzle_count += 1
#            lines.append(oneLine) #Collect all the lines that have swizzle
#     #Estimate the swizzle percentage
#     swizzle_percentage = (swizzle_count*100)/total_opcode_count
#     return(swizzle_count, lines, swizzle_percentage)
# 
# 
# swizzle_patterns = []   
# swizzle_count, swizzle_patterns, swizzle_percentage = swizzle_count_estimator('Instr_snapshot_test.txt')
# 
# =============================================================================


#Swizzle count detector function
def swizzle_count_estimator(file):
    #Read the file 
    with gzip.open(file,"rb") as f:
        gSimFile = f.readlines()
    #lines = []    # all the line results 
    pattern = []
    swizzle_count = [0,0,0]
    scalar_count = [0,0,0]
    swizzle_percentage = [0,0,0]
    scalar_percentage = [0,0,0]
    total_opcode_count = 0
    opcode_count = 0
    simd16_flag = 0
    simd8_flag = 0
    num_elem = 0
    opcode_expr = r"\w+\s+\(\d+\)"
    for line in gSimFile:  # go over each line
        line = line.strip().decode('ascii')
        #oneLine = []       # matches for one line 
        #swizzle_flag = 0   # Reset the flag to detect swizzle in next line
        #Estimate the opcode count
        if re.search(opcode_expr, line):
           #Estimate the opcode count
           opcode_count = instr_count(line)
           total_opcode_count += opcode_count
           if opcode_count:
                # Extract the SIMD-ness of the opcode
                simd8_flag, simd16_flag = extract_exec_size(line)
                #Extract the stride pattern for each source
                for m in range(2,5):
                    num_elem, pattern = stride_pattern_extractor(line,m)          
                    if pattern and num_elem == 3:
                        #Any regioning that is not flat involves a swizzle
                        if pattern[0] != pattern[1]*pattern[2] and (pattern != [1,1,0] ):
                            swizzle_count[m-2] += opcode_count
                        #Scalar case as well
                        if pattern == [0,1,0]:
                            scalar_count[m-2] += opcode_count
                    if pattern and num_elem <= 2:
                        if pattern != [8,1] or pattern != 1:
                            swizzle_count[m-2] += opcode_count
                    if m==4 and num_elem == 0: #2 Src operand case
                        src0_pattern = stride_pattern_extractor(line,2)
                        src1_pattern = stride_pattern_extractor(line,3)
                        if src0_pattern:
                           if src0_pattern == [8,8,1] and simd16_flag: 
                              swizzle_count[0] += opcode_count
                           if src0_pattern == [16,16,1] and simd8_flag: 
                              swizzle_count[0] += opcode_count  
                           if src1_pattern:
                              if src1_pattern == [8,8,1] and simd16_flag: 
                                swizzle_count[1] += opcode_count      
                              if src1_pattern == [16,16,1] and simd8_flag: 
                                swizzle_count[1] += opcode_count              
    #Calculate the overall swizzle and scalar percentages for each source
    for i in range(0,3):
        swizzle_percentage[i] = swizzle_count[i]/total_opcode_count
        scalar_percentage[i] = scalar_count[i]/total_opcode_count
    return(swizzle_count, swizzle_percentage, scalar_count, scalar_percentage)
    
    
#Raw mov counts estimator
def raw_mov_count_estimator(file):
    #Read the file 
    with gzip.open(file,"rb") as f:
        gSimFile = f.readlines()
    #text  = ["<92; 29,17><99; 8,3>","no match here","<2; 9,1><999;18,3>"]
    lines = []    # all the line results 
    pattern = []
    raw_mov_count = 0
    total_opcode_count = 0
    opcode_count = 0
    opcode_expr = r"\w+\s+\(\d+\)"
    for line in gSimFile:  # go over each line
        line = line.strip().decode('ascii')
        oneLine = []       # matches for one line 
        raw_mov_flag = 0   # Reset the flag to detect swizzle in next line
        flat_regioning = 0    
        if re.search(opcode_expr, line):
            #Estimate the opcode count
            opcode_count = instr_count(line)
            total_opcode_count += opcode_count
        if re.search(r"mov\s+\(\d+\)", line):
            for m in re.findall("<(\d+); ?(\d+),(\d+)>", line):  # find all patterns
                #pattern = map(int, m)                            # convert to int
                pattern = [int(x) for x in m]
                #Flat regioning
                if pattern[0] == pattern[1]*pattern[2] or (pattern[0] == 1 and pattern[1] == 1 and pattern[2] ==0):
                   flat_regioning = 1
            m = re.findall(r">:\w+", line) #find all patterns of the datatypes
            raw_mov_flag = all(x == m[0] for x in m)# find all patterns
            if raw_mov_flag == 1 and flat_regioning == 1:
               raw_mov_count += opcode_count
            lines.append(line) #Collect all the lines that have swizzle
    #Estimate the swizzle percentage
    raw_mov_percentage = raw_mov_count/total_opcode_count
    return(raw_mov_count, lines, raw_mov_percentage)