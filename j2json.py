#!/usr/bin/env python2
# 20210908, Ing. Ondrej DURAS (dury)
# -*- coding: ascii -*-
#=vim source $VIM/backup.vim
#=vim call Backup("C:\\usr\\good-oldies")

## MANUAL ############################################################# {{{ 1

VERSION = "2021.111703"
MANUAL  = """
NAME: J2JSON Jinja2 Template + JSON Config = Configuration Ticket
FILE: j2json.py

DESCRIPTION:
  Mandatory Jinja2 template for ticket preparation ?
  None Ansible around ?
  This should help.

  Script needs two things on input:
   - simple Jinja2 template
   - json configuration


USAGE:
  j2json.py -t TEMPLATE.j2 -c CONFIG.json -o CONFIG-TICKET.txt
  j2json.py -t TEMPLATE.j2 -c CONFIG.json -s site-x -o CONFIG-TICKET.txt
  j2json.py -t TEMPLATE.j2 -c COMMAN.json +c SITE-X.json -o CONFIG.txt
  j2json.py -t VLANS.j2 -v BA_VLAN_ID=100 -v BA_VLAN_NAME=WIFI
  j2json.py -t TEMPLATE.j2 -sed =begin,=end -c CFG.json 
  j2json.py -t TEMPLATE.j2 -cut =pod,=cut -c CFG.json 
  j2json.py -t TEMPLATE.j2 -m CRQ -c CFG.json
  j2json.py -c CONFIG.json -l
  j2json.py -c CONFIG.json -b
  j2json.py -e TEMPLATE.j2


PARAMETERS:
    -t  --template - j2 file containing the template
    +t   +template - adds another j2 file containing the template extension
    -c  --config   - json file with configuration parameters
    +c   +config   - adds another json file with configuration parameters
    -v  --value    - one variable=value added to configuration parameters
    -s  --sub      - sub-configuration / part-of-configuration
    -o  --output   - output file with prepared ticket
    -sed  --sed    - include a part of template only
    -cut  --cut    - exclude a part of template
    -m  --macro    - similar to -sed above, but works with marker based folds
    -l  --list     - list sub-configuration options
    -e  --extract  - extract all configuration items from a template
    -b  --batch    - prepares a batch for masive action
    -f1 -bra       - adds brackets to keys "{{key}}" /explicit
    -f0 -no        - suppress brackets in keys "key" /default

SEE ALSO:
  https://github.com/ondrej-duras/

VERSION: %s GPLv2
""" % (VERSION)


####################################################################### }}} 1
## GLOBALs ############################################################ {{{ 1


import sys
import re
import json

ACTION      = []  # list of actions
TEMPLATE    = ""  # template (file content)
FN_TEMPLATE = ""  # template (file name)
CONFIG      = {}  # configuration (file content)
FN_CONFIG   = {}  # configuration (file name)
SUBCFG      = ""  # name of sub-configuration if used
OUTFILE     = ""  # output file if used (""=stdout by default)
FORMAT      = 0   # 1={{}} in cfg, 0=without {{}} in cfg

####################################################################### }}} 1
## LIBRARY ############################################################ {{{ 1

# called by prepareConfig when input value is a list of values.
# expands template-lines into multilines, where each line contain one value of the input list of values.
# values: nets=[1.1.1.1/32,2.2.2.2/32]
# template: network {{nets}}
# output: network 1.1.1.1/32
#         network 2.2.2.2/32
def prepareMultiline(template,item,values,format=0):
  if format == 1 :
    item = item  # expected item "{{key}}"
  else:
    item = str("{{" + item + "}}") # expected item "key"
  output = ""
  for line in template.splitlines():
    if item in line:
      for value in values:
        newline = line
        output += newline.replace(item,value) + "\n"
    else:
      output += line + "\n"
  return output

# prepares a final particular configuration, 
# based on template and config.json
def prepareConfig(template,config,format=0):
  output = template
  multi  = False
  for item in config.keys():
    value=config[item]
    if isinstance(value,dict):
      print("Error: Hierarchycal configuration ( -s need to be used).")
      print("Error: Item '%s' is subconfig." % (item))
      exit()
    if isinstance(value,list):
      multi = True
      output = prepareMultiline(output,item,value,format)
      continue
    if format == 1 :
      output=output.replace(str(item),str(value))
    else:
      ritem=str("{{" + item + "}}")
      output=output.replace(ritem,str(value))
  return output

# provide a list of parameters/variables required 
# to prepare final configuration correctly
def extractConfig(template,format=0):
  global TEMPLATE
  out={}
  for line in TEMPLATE.splitlines():
    items=re.findall(r"\{\{[0-9A-Za-z_.]+\}\}",line)
    for item in items:
      if item in out.keys():
         out[item]+=1
      else:
         out[item]=1
  if format == 1 :  return out

  xout = {}
  for i in out.keys():
    y=re.sub("[{}]","",i)
    xout[y]=out[i]
  return xout

# list of .json sub-configurations
def listSubConfig(config):
  output = []
  for item in config.keys():
    if isinstance(config[item],dict):
      if item == "common":
        continue
      #print(item)
      output.append(item)
  return sorted(output)

# for 2.x compatibility reasons
# joins two Dicts together into one Dict
def mergeDict(x,y):
   z = x.copy()
   z.update(y)
   return z

# loads a .json file
def loadJson(fname):
  fh=open(fname,"r")
  output = json.load(fh)
  fh.close()
  return output


def loadFile(fname):
  fh=open(fname,"r")
  output=fh.read()
  fh.close()
  return output


def writeFile(fname,output):
  if not fname:
    print(output)
  else:
    fh=open(fname,"w")
    fh.write(output)
    fh.close()
    print("written to '%s'." % (fname))
  return

# output is a part of template cut from start-line to stop-line
def textSed(template,start,stop):
  output=""
  fflag=False
  lena = len(start)
  lenb = len(stop)
  if lena == 0: fflag=True
  for line in template.splitlines():
    if (lena<>0) and re.match(start,line): fflag=True;  continue  # copying=ON
    if (lenb<>0) and re.match(stop,line):  fflag=False; continue  # copying=OFF
    if not fflag: continue
    output += line + "\n";
  return output

# cut out a part of template from start-line to stop-line
def textCut(template,start,stop):
  output=""
  fflag=False
  lena = len(start)
  lenb = len(stop)
  if lena == 0: fflag=True
  for line in template.splitlines():
    if (lena<>0) and re.match(start,line): fflag=True;  continue  # copying=ON
    if (lenb<>0) and re.match(stop,line):  fflag=False; continue  # copying=OFF
    if fflag: continue
    output += line + "\n";
  return output

# if config.json contains more subConfiguration parts,
# then following j2json -c config.json -b
# may prepare batch of whole the project rebuild
def prepareBatch(config):
  global FN_CONFIG
  for item in listSubConfig(config):
    if item is None : continue
    try:
      template=config[item]["_TEMPLATE"]
      output=config[item]["_OUTPUT"]
    except:
      continue
    cmd = str(__file__)
    cmd += " -c %s" % (FN_CONFIG)
    cmd += " -s %s" % (item)
    cmd += " -t %s" % (template)
    cmd += " >%s"   % (output)
    print(cmd)

####################################################################### }}} 1
## ACTIONS ############################################################ {{{ 1
# all actions done at this point are the result of previosly called commandLine

def takeAction():
  global ACTION,TEMPLATE,CONFIG,SUBCFG,OUTFILE,FORMAT 

  # if none action defined, then manual is shown only
  if len(ACTION) == 0:
    print(MANUAL)
    print("Error: wrong command-line prameters !")

  # prepares the particular sub/configuration
  if "prepare" in ACTION:
    cfg={}
  
    if SUBCFG in CONFIG.keys():
      cfg.update(CONFIG[SUBCFG])
    if "common" in CONFIG.keys():
      cfg.update(CONFIG["common"])
    if SUBCFG == "":
      cfg = CONFIG
  
    output = prepareConfig(TEMPLATE,cfg,FORMAT)
    writeFile(OUTFILE,output)

  # prepares a list of required parameters in a json template
  if "extract" in ACTION:
    print(json.dumps(extractConfig(TEMPLATE,FORMAT),indent=2))

  # list all sub-configurations (each should be callable separatelly)
  if "list" in ACTION:
    # listSubConfig(CONFIG)
    print("\n".join(listSubConfig(CONFIG)))

  # lists commands to call all sub-configs in a sequence
  if "batch" in ACTION:
    prepareBatch(CONFIG)


####################################################################### }}} 1
## COMMAND-LINE ####################################################### {{{ 1
# based on content of commandline parameters it prepares a list of actions called later

def commandLine(args=sys.argv):
  global ACTION,TEMPLATE,FN_TEMPLATE,CONFIG,FN_CONFIG,SUBCFG,OUTFILE,FORMAT 

  argx=args.pop(0)
  if not len(args):
    print MANUAL
    exit()

  while len(args):
    argx=args.pop(0)
    if argx in ("-t","--template"): 
      FN_TEMPLATE=args.pop(0)
      TEMPLATE=loadFile(FN_TEMPLATE)
      ACTION.append("prepare")
      continue
    if argx in ("+t","+template"): 
      FN_TEMPLATE=args.pop(0)
      TEMPLATE+=loadFile(FN_TEMPLATE)
      ACTION.append("prepare")
      continue
    if argx in ("-sed","--sed"):
      (START,STOP)=str(args.pop(0)).split(",",1)
      TEMPLATE=textSed(TEMPLATE,START,STOP)
      continue
    if argx in ("-cut","--cut"):
      (START,STOP)=str(args.pop(0)).split(",",1)
      TEMPLATE=textCut(TEMPLATE,START,STOP)
      continue
    if argx in ("-start","--start"):
      START=args.pop(0)
      TEMPLATE=textSed(TEMPLATE,START,"")
      continue
    if argx in ("-stop","--stop"):
      STOP=args.pop(0)
      TEMPLATE=textSed(TEMPLATE,"",STOP)
      continue
    if argx in ("-m","-macro","--macro"):
      MACRO=args.pop(0)
      TEMPLATE=textSed(TEMPLATE,"## "+MACRO,"#####")
      continue
    if argx in ("-e","--extract"): 
      FN_TEMPLATE=args.pop(0)
      TEMPLATE=loadFile(FN_TEMPLATE)
      ACTION.append("extract")
      continue
    if argx in ("-c","--config"):
      FN_CONFIG=args.pop(0)
      CONFIG=loadJson(FN_CONFIG)
      continue
    if argx in ("+c","+config"):
      FN_CONFIG=args.pop(0)
      CONFIG=mergeDict(CONFIG,loadJson(FN_CONFIG))
      continue
    if argx in ("-v","--value","--variable","-val","-var"):
      PARAM=args.pop(0)
      (KEY,VAL)=PARAM.split("=",1)
      CONFIG[KEY]=VAL
      continue
    if argx in ("-s","--part","--site","--sub"):
      SUBCFG=args.pop(0)
      continue
    if argx in ("-o","--output","-out"):
      OUTFILE=args.pop(0)
      continue
    if argx in ("-l","--list"):
      ACTION.append("list")
      continue
    if argx in ("-f1","--format=1","-bra"):
      FORMAT=1
      continue
    if argx in ("-f0","--format=0","-no"):
      FORMAT=0
      continue
    if argx in ("-b","--batch"):
      ACTION.append("batch")
      continue
    else:
      print("Error: wrong parameter %s" % (argx))
      exit()
    

####################################################################### }}} 1
## MAIN ############################################################### {{{ 1

if __name__ == "__main__":
  commandLine()
  takeAction()


####################################################################### }}} 1
# --- end ---
