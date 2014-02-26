from lib.optparse_ext import OptionParser
import shlex 
import subprocess
import os
import sys
import lib.yaml as yaml


#############################
# Command Line Arguments
#############################
##def files_callback(option,opt,value,parser):
##    setattr(parser.values,option.dest,value.split(" "))

parser = OptionParser()
parser.add_option("-w","--workload",action="store",dest="wl_name", default=None,
                  help="workload name [default: %default] ")
parser.add_option("-p","--prefix",dest="prefix", default='psim',
                  help="OutFilePrefix used to run gsim [default: %default]")
parser.add_option("-o","--output-dir",dest="output_dir",default=None,
                  help="Path to the output directory where stat exists [default: %default]")
parser.add_option("-c","--cfg",dest="alps_config", default=None,
                  help="Path to ALPS Config File (alps_cfg.yaml) [default: %default]")
# parser.add_option("-i","--input",dest="input", default='/p/gat/tools/gsim_alps/inputs.txt',
#                   help="Path to inputs.txt [default: %default]")
# parser.add_option("-f","--formula",dest="formula", default='formula.txt',
#                   help="List all formulae to use seperated by space Format: \"<path_to_formula> <path_to_formula>...\"   [default: Formulae from central repo]")
parser.add_option("-l","--local",action="store_true",dest="run_local",default=False,
                  help="Run users scripts from user_dir [default: %default]")
parser.add_option("-q","--quiet",action="store_true",dest="quiet",default=False,
                  help="Run quietly [default: %default]")
parser.add_option("-b","--only-build-alps",action="store_true",dest="build_alps_only",default=False,
                  help="Run users scripts from current path [default: %default]")
parser.add_option("-a","--architecture",action="store", dest="dest_config", default=None,
                  help="Specify Gsim Config used for run. For e.g. bdw_gt2.cfg or just specify the three letter acronym For E.g. BDW, SKL, CNL, BXT [default: %default]")
parser.add_option("-d","--dir",action="store", dest="user_dir", default='.',
                  help=" user_dir where stat2res and build_alps scripts exist ( only used when --local is enabled) [default: %default]")
parser.add_option("-t","--tg_file",action="store", dest="tg_file", default='',
                  help=" Input Timegraph File. Please make sure the TG file has ALPS residencies as well. [default: %default]")
parser.add_option("--debug",action="store_true",dest="run_debug",default=False,
                  help="Run build_alps in debug mode [default: %default]")

(options,args) = parser.parse_args()

wd = ''
filename = ''
if not options.run_local:
    wd = '/p/gat/tools/gsim_alps'
else:
    wd = options.user_dir
#######################################
# Parsing ALPS CFG File
#######################################
if options.alps_config is not None:
    filename = options.alps_config
else:
    if options.dest_config.find('bdw') > -1 or  options.dest_config.find('chv') > -1:
        filename = '%s/alps_cfg_annealing.yaml' % wd
    else:	
        filename = '%s/alps_cfg.yaml' % wd

f = open(os.path.abspath(filename),'r')
cfg_data = yaml.load(f)
f.close()

if not options.quiet:
    print ("Building Alps model \n")
    print (options.wl_name)
    print (options.output_dir)
    print (options.dest_config)

res = options.output_dir + '/' + options.wl_name + '.res.csv'
log = options.output_dir + '/' + options.wl_name + '.res.log.txt'
stat = options.output_dir + '/' + options.prefix + '.stat'
yaml = options.output_dir + '/' + options.wl_name + '.yaml'
runalps_log = options.output_dir + '/' + 'runalps_' + options.wl_name + '.log'

alps_log = open(runalps_log,'w')

try:
    process = subprocess.Popen(['git','describe','--tags'], cwd='%s/' % (wd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    tag = process.communicate()[0]
    tag = (tag.rstrip()).decode("utf-8")
    ExitCode = process.wait()
except Exception:
    print("Not able to read git tag")

print ("Scripts Location:",os.path.abspath(wd),file=alps_log)
print ("Git Tag:",tag,file=alps_log)
print ("",file=alps_log)
print ("Output Directory:",os.path.abspath(options.output_dir),file=alps_log)
print ("StatFile: {0}.stat".format(options.prefix),file=alps_log)
print ("ResidencyFile: {0}_res.csv".format(options.wl_name),file=alps_log)
print ("ALPS Model: alps_{0}.yaml".format(options.wl_name),file=alps_log)
print ("Destination Architecture: {0}".format(options.dest_config),file=alps_log)
print ("",file=alps_log)
print("Command Line -->",file=alps_log)
print (" ".join(sys.argv),file=alps_log)
print("",file=alps_log)
alps_log.close()

if not options.run_local:
    stat_parser_cmd = ['/p/gat/tools/gsim_alps/StatParser/StatParser','-csv','-o', res, '-e', log, '-s', stat]
    for formula in cfg_data['Stat2Res Formula Files']:
        formula_file = '/p/gat/tools/gsim_alps/' + formula
        stat_parser_cmd += ['-i', formula_file]
   
    input_file = '/p/gat/tools/gsim_alps/' + cfg_data['ALPS Input File'][0]
    build_alps_cmd = ['/usr/intel/pkgs/python/3.1.2/bin/python', '/p/gat/tools/gsim_alps/build_alps.py', '-i', input_file, '-r', res, '-a', options.dest_config, '-o', yaml ]
    if(options.tg_file):
        build_alps_cmd += ['-t', '%s/%s' % (options.output_dir, options.tg_file), '-z', '%s/alps_Timegraph.txt' % options.output_dir]
    if(options.run_debug):
        build_alps_cmd += ['--debug']

else:
    try:
        process = subprocess.Popen('make', cwd='%s/%s' % (options.user_dir, 'StatParser'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        output = process.communicate()[0]
        ExitCode = process.wait()
    except Exception:
        print ('Error: StatParser compile failed to open subprocess')

    if ExitCode > 1:
        print ("StatParser compile failed with exitcode : ", ExitCode)
        exit(ExitCode) 

    stat_parser_script = options.user_dir + '/StatParser/StatParser'
    build_alps_script = options.user_dir + '/build_alps.py'
    stat_parser_cmd = [stat_parser_script,'-csv','-o', res, '-e', log, '-s', stat]
    for formula in cfg_data['Stat2Res Formula Files']:
        formula_file = options.user_dir + '/' + formula
        stat_parser_cmd += ['-i', formula_file]

    input_file = options.user_dir + '/' + cfg_data['ALPS Input File'][0]
    build_alps_cmd = ['/usr/intel/pkgs/python/3.1.2/bin/python', build_alps_script, '-i', input_file, '-r', res, '-a', options.dest_config, '-o', yaml ]
    if(options.tg_file):
        build_alps_cmd += ['-t', '%s/%s' % (options.output_dir, options.tg_file), '-z', '%s/alps_Timegraph.txt' % options.output_dir]
    if(options.run_debug):
        build_alps_cmd += ['--debug']

if not options.build_alps_only:
    try:
        env_vars = os.environ
        env_vars['LD_LIBRARY_PATH'] = '/p/gat/tools/boost/1.43.0/gcc4.3/lib64/'
        process = subprocess.Popen(stat_parser_cmd, env=env_vars, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        output = process.communicate()[0]
        ExitCode = process.wait()
    except Exception:
        print ('Error: StatParser failed to open subprocess')

    if ExitCode > 1:
        print ("StatParser failed with exitcode : ", ExitCode)
        exit(ExitCode) 

try:
    process = subprocess.Popen(build_alps_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    output = process.communicate()[0]
    ExitCode = process.wait()
except Exception:
    print ('Error: build_alps failed to open subprocess')

if ExitCode > 1:
    print ("build_alps failed with exitcode : ", ExitCode) 
    exit(ExitCode) 