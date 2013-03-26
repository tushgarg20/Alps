from optparse import OptionParser
import yaml
import re


#############################
# Command Line Arguments
#############################
##def files_callback(option,opt,value,parser):
##    setattr(parser.values,option.dest,value.split(" "))

parser = OptionParser()
parser.add_option("-i","--input",dest="input_file",
                  help="Input file containing path to all input files")
parser.add_option("-r","--residency",dest="residency_file",
                  help="Name of input Residency file")
parser.add_option("-o","--output",dest="output_file",
                  help="Name of output YAML file")
parser.add_option("-a","--architecture",dest="dest_config",
                  help="Specify target architecture. For e.g. Gen9LPCLient,Gen8SoC")

(options,args) = parser.parse_args()
##print options.input_file
##print options.residency_file
##print options.output_file
##print options.dest_config

#################################
# Global Variables
#################################
I = {}
C = {}
cdyn_precedence = ['Gen7','Gen7.5','Gen8','Gen8SoC','Gen9LPClient','Gen9LPSoC','Gen10LP']
new_gc = {}
process_hash = {}
voltage_hash = {}
cdyn_cagr_hash = {'syn':{},'ebb':{}}
stepping_hash = {}
cfg = options.dest_config
#path = []
paths = []

#################################
# Subroutines
#################################
def get_data(line, separator):
    res = line.split(separator)
    i = 0
    while(i < len(res)):
        res[i] = res[i].strip()
        i = i + 1
    return res

def dfs(adict, path=[]):
    if(type(adict) is not dict):
        path.append(adict)
        paths.append(path + [])
        path.pop()
        return
    for key in adict:
        path.append(key)
        dfs(adict[key],path)
        if(path):
            path.pop()
    return

def split_string(source, splitlist):
    index = 0
    flag = True
    result = []
    word = ""
    while(index < len(source)):
        char = source[index]
        if char in splitlist:
            if(word):
                result.append(word)
                word = ""
            result.append(char)
            char = ""

        word = word + char
        index = index + 1
    if(word):
        result.append(word)
    return result

def get_base_config(stat):
    if(stat not in cdyn_hash):
        print "No cdyn weight is available for " + stat
        return None,None
    i = cdyn_precedence.index(cfg)
    while(i >= 0):
        config = cdyn_precedence[i]
        if(config in cdyn_hash[stat]):
            if('B0' in cdyn_hash[stat][config]):
                return config,'B0'
            elif('A0' in cdyn_hash[stat][config]):
                return config,'A0'
            else:
                print "Stepping is unknown for " + stat + " for config - " + config
                return config, None
        i = i-1

    print "Not able to find matching cdyn weight for " + stat
    return None,None
    
def get_eff_cdyn(cluster,unit,stat):
    base_cfg,stepping = get_base_config(stat)
    if(base_cfg == None or stepping == None):
        return 0
    #print stat,base_cfg,stepping
    base_cdyn = cdyn_hash[stat][base_cfg][stepping]['weight']
    cdyn_type = cdyn_hash[stat][base_cfg][stepping]['type']
    ref_gc = cdyn_hash[stat][base_cfg][stepping]['ref_gc']
    process_sf = process_hash[base_cfg][cfg]
    if(process_sf == 'NA'):
        process_sf = 0
    voltage_sf = voltage_hash[base_cfg][cfg]
    if(voltage_sf == 'NA'):
        voltage_sf = 0
    stepping_sf = stepping_hash[base_cfg]['A0']['B0'] if stepping =='A0' else 1
    cdyn_cagr_sf = cdyn_cagr_hash[cdyn_type][cluster][base_cfg][cfg]
    if(unit not in I):
        print "Number of instances for " + unit + " are unknown"
        instances = 0
    else:
        instances = I[unit]
    if(cdyn_type == 'syn'):
        if((cluster not in new_gc) or (unit not in new_gc[cluster]) or (cfg not in new_gc[cluster][unit])):
            print "Gate count is not available for " + cluster + " , " + unit
            newproduct_gc = 0
        else:
            newproduct_gc = new_gc[cluster][unit][cfg]
    else:
        newproduct_gc = 1
    gc_sf = newproduct_gc/ref_gc
    eff_cdyn = base_cdyn*instances*gc_sf*process_sf*voltage_sf*stepping_sf*cdyn_cagr_sf
        
    #print base_cdyn, eff_cdyn
    return eff_cdyn

def eval_formula(alist):
    result = 0
    formula = alist[-1]
    formula = "".join(formula.split())
    power_stat = alist[-2]
    cluster = alist[0]
    unit = alist[1]
    formula_data = split_string(formula,"+-/*()")
    cdyn_vars = []
    res_vars = []
    i = 0
    while(i < len(formula_data)):
        if(formula_data[i] == 'R'):
            formula_data[i] = 'R['+power_stat+']'
            res_vars.append(formula_data[i])
        elif(formula_data[i] == 'C'):
            formula_data[i] = 'C['+power_stat+']'
            cdyn_vars.append(formula_data[i])
        elif(re.search(r'^R\[.*\]',formula_data[i])):
            res_vars.append(formula_data[i])
        elif(re.search(r'^C\[.*\]',formula_data[i])):
            cdyn_vars.append(formula_data[i])
        i = i+1

    for elem in res_vars:
        key = split_string(elem,"[]")[2]
        if(key not in R):
            print "Residency for " + key + " is not there!!"
            return 0

    for elem in cdyn_vars:
        key = split_string(elem,"[]")[2]
        C[key] = get_eff_cdyn(cluster,unit,key)

    formula = "".join(formula_data)
    formula = formula.replace("[","['")
    formula = formula.replace("]","']")
    result = eval(formula)
    return result


####################################
# Parsing Build ALPS Config File
####################################

input_hash = {}
infile = open(options.input_file,'r')
for line in infile:
    data = get_data(line,"=")
    input_hash[data[0]] = data[1]

#print input_hash

##############################
# Parsing Residency File
##############################
R = {}
resfile = open(options.residency_file,'r')
for line in resfile:
    data = get_data(line,",")
    test = data[0]
    if(re.search(r'^num_.*',test)):
        I[data[0].split("_")[1]] = float(data[1])
    else:
        R[data[0]] = float(data[1])
resfile.close()
#for key in R:
    #print key + "," + R[key]
#print I

##############################
# Parsing Cdyn File
##############################
cdyn_hash = {}
cdyn_file = open(input_hash['Cdyn'],'r')
first_line = cdyn_file.readline()
for line in cdyn_file:
    data = get_data(line,",")
    if(data[0] not in cdyn_hash):
        cdyn_hash[data[0]] = {}
    if(data[1] not in cdyn_hash[data[0]]):
        cdyn_hash[data[0]][data[1]] = {}
    if(data[2] not in cdyn_hash[data[0]][data[1]]):
        cdyn_hash[data[0]][data[1]][data[2]] = {}
    cdyn_hash[data[0]][data[1]][data[2]]['weight'] = float(data[3])
    cdyn_hash[data[0]][data[1]][data[2]]['type'] = data[4]
    cdyn_hash[data[0]][data[1]][data[2]]['ref_gc'] = float(data[5])
cdyn_file.close()
#print cdyn_hash

################################
# Parsing Gate Count File
################################
gc_file = open(input_hash['GateCount'],'r')
header_line = gc_file.readline()
header_data = get_data(header_line,",")[2:]
for line in gc_file:
    data = get_data(line,",")
    length = len(data)
    if(data[1] not in new_gc):
        new_gc[data[1]] = {}
    if(data[0] not in new_gc[data[1]]):
        new_gc[data[1]][data[0]] = {}
    for i in range(2,length):
        new_gc[data[1]][data[0]][header_data[i-2]] = float(data[i])
        
gc_file.close()
#print new_gc

################################
# Parsing Scaling Factor Files
################################
# Process Scaling Factor
process_file = open(input_hash['Process_Scaling_Factors'],'r')
first_line = process_file.readline()
for line in process_file:
    data = get_data(line,",")
    if(data[0] not in process_hash):
        process_hash[data[0]] = {}
    if(data[1] not in process_hash[data[0]]):
        process_hash[data[0]][data[1]] = {}
    process_hash[data[0]][data[1]] = float(data[2]) if data[2] != 'NA' else data[2]
process_file.close()
#print process_hash

voltage_file = open(input_hash['Voltage_Scaling_Factors'],'r')
first_line = voltage_file.readline()
for line in voltage_file:
    data = get_data(line,",")
    if(data[0] not in voltage_hash):
        voltage_hash[data[0]] = {}
    if(data[1] not in voltage_hash[data[0]]):
        voltage_hash[data[0]][data[1]] = {}
    voltage_hash[data[0]][data[1]] = float(data[2]) if data[2] != 'NA' else data[2]
voltage_file.close()
#print voltage_hash

syn_cdyn_cagr_file = open(input_hash['syn_cdyn_cagr'],'r')
first_line = syn_cdyn_cagr_file.readline()
for line in syn_cdyn_cagr_file:
    data = get_data(line,",")
    if(data[0] not in cdyn_cagr_hash['syn']):
        cdyn_cagr_hash['syn'][data[0]] = {}
    if(data[1] not in cdyn_cagr_hash['syn'][data[0]]):
        cdyn_cagr_hash['syn'][data[0]][data[1]] = {}
    cdyn_cagr_hash['syn'][data[0]][data[1]][data[2]] = float(data[3]) if data[3]!='NA' else data[3]
syn_cdyn_cagr_file.close()
#print cdyn_cagr_hash['syn']

ebb_cdyn_cagr_file = open(input_hash['ebb_cdyn_cagr'],'r')
first_line = ebb_cdyn_cagr_file.readline()
for line in ebb_cdyn_cagr_file:
    data = get_data(line,",")
    if(data[0] not in cdyn_cagr_hash['ebb']):
        cdyn_cagr_hash['ebb'][data[0]] = {}
    if(data[1] not in cdyn_cagr_hash['ebb'][data[0]]):
        cdyn_cagr_hash['ebb'][data[0]][data[1]] = {}
    cdyn_cagr_hash['ebb'][data[0]][data[1]][data[2]] = float(data[3]) if data[3]!='NA' else data[3]
ebb_cdyn_cagr_file.close()
#print cdyn_cagr_hash['ebb']

stepping_file = open(input_hash['cdyn_stepping'],'r')
first_line = stepping_file.readline()
for line in stepping_file:
    data = get_data(line,",")
    if(data[0] not in stepping_hash):
        stepping_hash[data[0]] = {}
    if(data[1] not in stepping_hash[data[0]]):
        stepping_hash[data[0]][data[1]] = {}
    stepping_hash[data[0]][data[1]][data[2]] = float(data[3]) if data[3]!='NA' else data[3]
stepping_file.close()

#############################
# Parse ALPS Formula File
#############################
formula_files = get_data(input_hash['ALPS_formula_file'],",")
for ff in formula_files:
    f = open(ff,'r')
    yaml_data = yaml.load(f)
    f.close()
    ##print yaml_data
    dfs(yaml_data)

output_list = paths + []
output_yaml_data = {'GT':{}}
overview_data = {'cdyn':{}}

for path in output_list:
    path[-1] = eval_formula(path)
    d = output_yaml_data['GT']
    i = 0
    while(True):
        if('cdyn' not in d):
            d['cdyn'] = 0
        d['cdyn'] += path[-1]
        if(i == len(path)-2):
            d[path[i]] = float('%.3f'%float(path[i+1]))
            break
        else:
            if(path[i] in d):
                d = d[path[i]]
                i = i+1
                continue
            else:
                d[path[i]] = {}
        d = d[path[i]]
        i = i+1

#print output_yaml_data

####################################
# Generating output YAML file
####################################
of = open(options.output_file,'w')
yaml.dump(output_yaml_data,of,default_flow_style=False)
of.close()


