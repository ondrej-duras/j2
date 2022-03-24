#!/usr/bin/env python2
# 20210908, Ing. Ondrej DURAS (dury)
# -*- coding: ascii -*-
#=vim source $VIM/backup.vim
#=vim call Backup("C:\\usr\\good-oldies")

## MANUAL ############################################################# {{{ 1

VERSION = "2022.032402"
MANUAL  = """
NAME: J2JSON Jinja2 Template + JSON Config = Configuration Ticket
FILE: j2json.py

DESCRIPTION:
  Mandatory Jinja2 template for ticket preparation ?
  None Ansible around ?
  This should help.

  Script needs two things on input:
   - simple Jinja2 template
   - json configuration (humanized .json works too)
  Humanized (.juh as extension) uses # comments

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
  j2json.py -E TEMPLATE.j2


PARAMETERS:
    -t  --template  - j2 file containing the template
    +t   +template  - adds another j2 file containing the template extension
    -c  --config    - json file with configuration parameters
    +c   +config    - adds another json file with configuration parameters
    -v  --value     - one variable=value added to configuration parameters
    -s  --sub       - sub-configuration / part-of-configuration
    -o  --output    - output file with prepared ticket
    -sed  --sed     - include a part of template only
    -cut  --cut     - exclude a part of template
    -m  --macro     - similar to -sed above, but works with marker based folds
    -l  --list      - list sub-configuration options
    -e  --extract   - extract all configuration items from a template - detail
    -E  --Extract   - extract all configuration items from a template - simplified
    -b  --batch     - prepares a batch for masive action
    -f1 -bra        - adds brackets to keys "{{key}}" /explicit
    -f0 -no         - suppress brackets in keys "key" /default
    -f3 --filters   - uses filters (default) (have a look to FILTERS dict)
    -f4 --nofilters - does not use filters 
    -h  --help      - this help
    -h2 --help2     - .json input file format - file example
    -h3 --help3     - usage of filters
    -sf --supported - lists supported filters
    -df --describe  - describe filter/s in detail  

SEE ALSO:
  https://github.com/ondrej-duras/

VERSION: %s GPLv2
""" % (VERSION)


MANUAL2 = """
# common section, included within all other sections
{
"common" : {
 "_TEMPLATE_URL": "https://straka.lab.orange.sk/templates/%", # link to templates
 "_CRQ": "CRQ000000967001", # ticket of configuration change
 "_CRQ_SUBJECT": "X-345-BA: STP_SIGTRAN for TestBed1",  # subject of ticket
 "site_id" : "X-345-BA",
 "bgp_as_osk" : "15962",
 "bgp_as_core": "65111" 
},

"c11-vpn-pri" : {
  "_TEMPLATE": "01-VPN_BGP.j2",
  "_OUTPUT":   "c11-VPN_BGP-SIGTRAN_PRI-CRQprocedure.txt",
  "vpn": "SIGTRAN_PRI",
  "target":       "15962:1000111", 
  "primary_rd":   "<IPSA_RD1_PRI>",
  "secondary_rd": "<IPSA_RD2_PRI>", 
  "local_preference_gw1": "200",
  "local_preference_gw2": "20"
},
"c56-foreign-sec2ims": {
  "_TEMPLATE": "05-FOREIGN.j2",
  "_OUTPUT":   "c56-FOREIGN-STP_SIG_SEC_T2IMS_SIGNALING_PRI-CRQprocedure.txt",
  "vpn": "IMS_SIGNALING_PRI",
  "core_vrf": "CORE_STP_SIG_SEC_T", 
  "uplink_vlan_id": "3095", 
  "uplink_vlan_name": "STP_SIG_SEC_T2IMS_SIGNALING_PRI", 
  "uplink_ip4": "172.17.111.1",
  "foreign_ipnet_m": [   # this kind assures multiple/multiline application.
    "172.16.77.185/32",  # Line, containing foreign_ipnet_m is applied 3 times.
    "172.16.77.190/32",  # each one with other value
    "172.16.77.225/32"
  ]
}
}
"""
MANUAL3 = """
CONFIG = {
  'net_a': '1.1.1.0/24', 
  'net_b': '2.2.2.16/24', 
  'uprava': 'KONIEC.', 
  'pozdrav': 'ahoj'
}
TEMPLATE = \"\"\"
  # private part
  {{pozdrav|upper()}}
  {{net_a|addhost(2)}} {{net_b|addhost(3)}}
  {{net_a|addhost(0)}} {{net_b|addhost(3)}}
  {{net_a|iphost(5)}} {{net_b|iphost(0)}}

  # ansible compactible part
  {{net_a|ansible.netcommon.nthhost(4)}}/{{net_a|ansible.netcommon.hostmask()}}
  {{net_a|ipaddr(3)}}
  {{uprava|lower()}}
\"\"\"

OUTPUT = \"\"\"
  # private part
  AHOJ
  1.1.1.2 2.2.2.19
  1.1.1.0 2.2.2.19
  1.1.1.5/24 2.2.2.16/24

  # ansible compactible part
  1.1.1.4/24
  1.1.1.3
  koniec.
\"\"\"

Each filter must be a function with two mandatory parameters:
The first is value of key from configuration, the second
is parameter, mentiond in .J2 template after pipe '|'

Have a look more at variable FILTERS in source code.
"""


####################################################################### }}} 1
## GLOBALs ############################################################ {{{ 1


import sys
import re
import json
import itertools
import time

ACTION      = []  # list of actions
TEMPLATE    = ""  # template (file content)
FN_TEMPLATE = ""  # template (file name)
CONFIG      = {}  # configuration (file content)
FN_CONFIG   = {}  # configuration (file name)
SUBCFG      = ""  # name of sub-configuration if used
OUTFILE     = ""  # output file if used (""=stdout by default)
FORMAT      = 0   # 1={{}} in cfg, 0=without {{}} in cfg
USE_FILTERS = 1   # 1=uses filters 0= does not use filters (-f3 / -f4)
DESC_FILTERS= ""  # regular expression to select filters they need to be described --describe

####################################################################### }}} 1
## Filters - Strings ################################################## {{{ 1
# filter_something(text,param)
# CONFIG:
#  "text_a" : "some_text_a",
# TEMPLATE
#  {{text_a|somethin(param_a)}}
#
# OUTPUT:
#  `filter_something("some_text_a","param_a")`

def filter_upper(text,param):
  return str(text).upper()

def filter_lower(text,param):
  return str(text).lower()


def filter_date(text,param):
  return time.strftime("%Y-%m-%d",time.localtime())

def filter_time(text,param):
  return time.strftime("%H:%M:%S",time.localtime())



def filter_debuger(text,param):
  return """
  DEBUGER
    text:  %s
    param: %s\n""" % (text,param)

####################################################################### }}} 1
## Filters - IP math _old ############################################# {{{ 1

def filter_dbghost_old(addr_p,sft):
  # IP IP/M IP/MASK => binary_ip
  sft = sft.strip("'\"")
  print(addr_p)
  addr_1 = re.sub("\/.*","",addr_p)
  if "/" in addr_p:
    mask = re.sub("^.*/","/",addr_p)
  else:
    mask = ""
  print(addr_1)
  print(mask)
  (a,b,c,d)=addr_1.split(".")
  print("%s %s %s %s" % (a,b,c,d))
  addr_i=((int(a)*256+int(b))*256+int(c))*256+int(d)
  print(addr_i)

  # binary_ip => string_ip
  sd=str(addr_i >>  0 & 255)
  sc=str(addr_i >>  8 & 255)
  sb=str(addr_i >> 16 & 255)
  sa=str(addr_i >> 24 & 255)
  addr_s="%s.%s.%s.%s%s" % (sa,sb,sc,sd,mask)
  print("%s >> %i >> %s" % (addr_p,addr_i,addr_s))

# nezachovana masku
# cuts off the mask on output even defined on input
def filter_addhost_old(addr_p,sft):
  # IP IP/M IP/MASK => binary_ip
  sft = sft.strip("'\"")
  addr_1 = re.sub("\/.*","",addr_p)
  (a,b,c,d)=addr_1.split(".")
  addr_i=((int(a)*256+int(b))*256+int(c))*256+int(d)

  addr_i += int(sft)

  # binary_ip => string_ip
  sd=str(addr_i >>  0 & 255)
  sc=str(addr_i >>  8 & 255)
  sb=str(addr_i >> 16 & 255)
  sa=str(addr_i >> 24 & 255)
  addr_s="%s.%s.%s.%s" % (sa,sb,sc,sd)
  return addr_s

# zachovava masku, ak bola definovana
# keeps mask on output if defined on input
def filter_iphost_old(addr_p,sft):
  # IP IP/M IP/MASK => binary_ip
  sft = sft.strip("'\"")
  addr_1 = re.sub("\/.*","",addr_p)
  if "/" in addr_p:
    mask = re.sub("^.*/","/",addr_p)
  else:
    mask = ""
  (a,b,c,d)=addr_1.split(".")
  addr_i=((int(a)*256+int(b))*256+int(c))*256+int(d)

  addr_i += int(sft)

  # binary_ip => string_ip
  sd=str(addr_i >>  0 & 255)
  sc=str(addr_i >>  8 & 255)
  sb=str(addr_i >> 16 & 255)
  sa=str(addr_i >> 24 & 255)
  addr_s="%s.%s.%s.%s%s" % (sa,sb,sc,sd,mask)
  return addr_s

# returns ip_mask only
# example
# {{net_a}} => 10.0.0.0/8
# {{net_a|ipmask()}} => /8
# {{net_a|addhost(1)}}{{net_a|ipmask()}} => 10.0.0.1/8
def filter_ipmask_old(addr_p,parm):
  if "/" in addr_p:
    mask = re.sub("^.*/","/",addr_p)
  else:
    mask = ""
  return mask 

def filter_hostmask_old(addr_p,parm):
  if "/" in addr_p:
    mask = re.sub("^.*/","",addr_p)
  else:
    mask = ""
  return mask 

####################################################################### }}} 1
## Filters - IP math ################################################## {{{ 1


def filter_ip_addr(text,param):
  pass

def filter_ip_host(text,param):
  pass

# cuts off the mask on output even defined on input
def filter_ip_plus(addr_p,sft):
  # IP IP/M IP/MASK => binary_ip
  sft = sft.strip("'\"")
  addr_1 = re.sub("\/.*","",addr_p)
  (a,b,c,d)=addr_1.split(".")
  addr_i=((int(a)*256+int(b))*256+int(c))*256+int(d)

  addr_i += int(sft)

  # binary_ip => string_ip
  sd=str(addr_i >>  0 & 255)
  sc=str(addr_i >>  8 & 255)
  sb=str(addr_i >> 16 & 255)
  sa=str(addr_i >> 24 & 255)
  addr_s="%s.%s.%s.%s" % (sa,sb,sc,sd)
  return addr_s

def filter_ip_prefix(text,param):
  pass

def filter_ip_mask(text,param):
  pass

def filter_ip_wild(text,param):
  pass

def filter_ip_network(text,param):
  pass

def filter_ip_netonly(text,param):
  pass

def filter_ip_bcast(text,param):
  pass

def filter_ip_first(text,param):
  pass

def filter_ip_last(text,param):
  pass

####################################################################### }}} 1
## Filters - references to implementation ############################# {{{ 1


FILTERS={
  # input for ip_* firlers should be allways in two possible formats 1.1.1.1 or 1.1.1.1/2
  # where 1 are octets of IPv4 address, 2 is a prefix.
  "ip_addr":[filter_ip_addr,"{{10.1.1.1/24|ip_addr(4)}} => 10.1.1.4/24 ...draft"],
  "ip_host":[filter_ip_host,"{{10.1.1.1/24|ip_host(4)}} => 10.1.1.4 ...draft"],
  "ip_plus":[filter_ip_plus,"{{10.1.1.1/24|ip_plus(4)}} => 10.1.1.5"],
  "ip_prefix":[filter_ip_prefix,"{{10.1.1.1/24|ip_prefix()}} => 24 ...draft"],
  "ip_mask":[filter_ip_mask,"{{10.1.1.1/24|ip_mask()}} => 255.255.255.0 ...draft"],
  "ip_wild":[filter_ip_wild,"{{10.1.1.1/24|ip_wild()}} => 0.0.0.255 ...draft"],
  "ip_network":[filter_ip_network,"{{10.1.1.1/24|ip_network()}} => 10.1.1.0/24 ...draft"],
  "ip_netonly":[filter_ip_netonly,"{{10.1.1.1/24|ip_netonly()}} => 10.1.1.0 ...draft"],
  "ip_bcast":[filter_ip_bcast,"{{10.1.1.1/24|ip_bcast()}} => 10.1.1.255 ..draft"],
  "ip_first":[filter_ip_first,"{{10.1.1.8/24|ip_first()}} => 10.1.1.1 ..draft"],
  "ip_last":[filter_ip_last,"{{10.1.1.8/24|ip_last()}} => 10.1.1.254 ..draft"],

  "addhost":[filter_addhost_old,"DEPRECATED. - used in v02 templates"],
  "iphost":[filter_iphost_old,"DEPRECATED. - used in v02 templates"],
  "ipmask":[filter_ipmask_old,"DEPRECATED. - used in v02 templates"],
  "ipaddr":[filter_addhost_old,"DEPRECATED. - used in v02 templates"],
  "prefix":[filter_hostmask_old,"DEPRECATED. - used in v02 templates"],
  "hostmask":[filter_hostmask_old,"DEPRECATED. - used in v02 templates"],
  "ansible.netcommon.nthhost":[filter_addhost_old,"not used yet. intended for ansible compatibility"],
  "ansible.netcommon.hostmask":[filter_hostmask_old,"not used yet. intended for ansible compatibility"],
  "ansible.netcommon.next_nth_usable":[filter_addhost_old,"not used yet. intended for ansible compatibility"],
  "ansible.netcommon.prefix":[filter_hostmask_old,"not used yet. intended for ansible compatibility"],
  "upper":[filter_upper,"{{Something|upper()}} => SOMETHING"],
  "lower":[filter_lower,"{{Something|lower()}} => something"],
  "date":[filter_date,"{{Something|date()}} => 2022-03-24 ...actual date ..untested"],
  "time":[filter_time,"{{Something|time()()}} => 22:11:00 ...actual time ..untested"]
}

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



def prepareFilters(template,config,filters=FILTERS):
  OUTPUT=config.copy()
  for item in itertools.product(config.keys(),filters.keys()):
    config_key=item[0] ; config_val=config[config_key]
    filter_key=item[1] ; filter_val=filters[filter_key][0]
    pattern = "\\{\\{%s\\|%s\\([^)]*\\)\\}\\}" % (config_key,filter_key)
    #print("---")
    #print(pattern)
    for found in re.finditer(pattern,template):
       found_str=found.group(0)
       filter_par = re.sub(r"^.*\(","",found_str)
       filter_par = re.sub(r"\)\}\}$","",filter_par)
       filter_out = filter_val(config_val,filter_par)
       found_str = re.sub(r"^\{\{","",found_str)
       found_str = re.sub(r"\}\}$","",found_str)
       #print("%s ==> %s" % (found_str,filter_out))
       OUTPUT[found_str] = filter_out
  return OUTPUT




# provide a list of parameters/variables required 
# to prepare final configuration correctly
def extractConfigDetailed(template,format=0):
  global TEMPLATE
  out={}
  for line in TEMPLATE.splitlines():
    #items=re.findall(r"\{\{[0-9A-Za-z_.]+\}\}",line)
    items=re.findall(r"\{\{[0-9A-Za-z_.|()']+\}\}",line)
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

# provide a list of parameters/variables required 
# to prepare final configuration correctly
def extractConfigSimplified(template,format=0):
  global TEMPLATE
  out={}
  for line in TEMPLATE.splitlines():
    #items=re.findall(r"\{\{[0-9A-Za-z_.]+\}\}",line)
    items=re.findall(r"\{\{[0-9A-Za-z_.]+[}|]",line)
    for item in items:
      if item in out.keys():
         out[item]+=1
      else:
         out[item]=1
  if format == 1 :  return out

  xout = {}
  for i in out.keys():
    y=re.sub("[{|}]","",i)
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

# list supported filters
def listFilters(filters=FILTERS):
  for item in sorted(filters.keys()):
    method=filters[item][0]
    descr=filters[item][1]
    print("%s :: %s" % (str(item),str(descr)))

# describe filters
def describeFilters(filter_name,filters=FILTERS):
  for item in sorted(filters.keys()):
    if not re.match(filter_name,item):
      continue
    method=filters[item][0]
    descr=filters[item][1]
    print("NAME: %s" % (str(item)))
    print("REF:  %s" % (str(method)))
    print("DESCR:") 
    print("  %s" % (str(descr)))
    if(len(filters[item])>2):
      print(filters[item][2])
    print("")

# for 2.x compatibility reasons
# joins two Dicts together into one Dict
def mergeDict(x,y):
   z = x.copy()
   z.update(y)
   return z

# # loads a .json file
# def loadJson(fname):
#   fh=open(fname,"r")
#   output = json.load(fh)
#   fh.close()
#   return output

# loads humanized .json
# "humanized" means it may contain some comments
def loadJson(fname):
  fh = open(fname,"r")
  text1 = fh.read()
  text2 = ""
  fh.close()
  for line in text1.splitlines():
    if re.match(r"\s*#",line): continue
    line = re.sub(r'#[^"]+$','',line)
    text2 += line + "\n"
  #print(text2)
  output = {}
  try:
    output = json.loads(text2)
  except ValueError as err:
    print(err)  # this exception
    lerr=re.sub("^.*line ","",str(err))
    lerr=re.sub(" col.*$","",lerr)
    lerr=int(lerr)
    try:
      print("Error is at:" + (text2.splitlines()[lerr])) 
    except:
      pass
    exit()      # shows where the error is
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
  self_name = re.sub(r"^.*[/\\]","",str(__file__))
  #print(":: %s" % (__file__))
  #print(":: %s" % (self_name))
  
  for item in listSubConfig(config):
    if item is None : continue
    try:
      template=config[item]["_TEMPLATE"]
      output=config[item]["_OUTPUT"]
    except:
      continue
    cmd = self_name
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
  global FILTERS,DESC_FILTERS

  # if none action defined, then manual is shown only
  if len(ACTION) == 0:
    print(MANUAL)
    print("Error: wrong command-line prameters !")

  if "help" in ACTION:
    print(MANUAL)

  if "help2" in ACTION:
    print(MANUAL2)

  if "help3" in ACTION:
    print(MANUAL3)

  # prepares the particular sub/configuration
  if "prepare" in ACTION:
    cfg={}
  
    if SUBCFG in CONFIG.keys():
      cfg.update(CONFIG[SUBCFG])
    if "common" in CONFIG.keys():
      cfg.update(CONFIG["common"])
    if SUBCFG == "":
      cfg = CONFIG

    if USE_FILTERS == 1:
      cfg = prepareFilters(TEMPLATE,cfg,FILTERS)
  
    output = prepareConfig(TEMPLATE,cfg,FORMAT)
    writeFile(OUTFILE,output)

  # prepares a list of required parameters in a json template
  if "extract_detail" in ACTION:
    print(json.dumps(extractConfigDetailed(TEMPLATE,FORMAT),indent=2))

  # prepares a list of required parameters in a json template
  if "extract_simple" in ACTION:
    print(json.dumps(extractConfigSimplified(TEMPLATE,FORMAT),indent=2))

  # list all sub-configurations (each should be callable separatelly)
  if "list" in ACTION:
    # listSubConfig(CONFIG)
    print("\n".join(listSubConfig(CONFIG)))

  # lists commands to call all sub-configs in a sequence
  if "batch" in ACTION:
    prepareBatch(CONFIG)

  # list all supported filters
  if "list_filters" in ACTION:
    listFilters()

  # describe supported filters
  if "descr_filters" in ACTION:
    describeFilters(DESC_FILTERS,FILTERS)

####################################################################### }}} 1
## COMMAND-LINE ####################################################### {{{ 1
# based on content of commandline parameters it prepares a list of actions called later

def commandLine(args=sys.argv):
  global ACTION,TEMPLATE,FN_TEMPLATE,CONFIG,FN_CONFIG,SUBCFG,OUTFILE,FORMAT 
  global FILTERS,DESC_FILTERS

  argx=args.pop(0)
  if not len(args):
    print MANUAL
    exit()

  while len(args):
    argx=args.pop(0)
    if argx in ("-h","--help","-?"):
      ACTION.append("help")
      continue 
    if argx in ("-h2","--help2","-?2"):
      ACTION.append("help2")
      continue 
    if argx in ("-h3","--help3","-?3"):
      ACTION.append("help3")
      continue 
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
      ACTION.append("extract_detail")
      continue
    if argx in ("-E","--Extract"): 
      FN_TEMPLATE=args.pop(0)
      TEMPLATE=loadFile(FN_TEMPLATE)
      ACTION.append("extract_simple")
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

    if argx in ("-f3","--filters","-fil"):
      USE_FILTERS=1
      continue
    if argx in ("-f4","--nofilters","-nofil"):
      USE_FILTERS=0
      continue

    if argx in ("-b","--batch"):
      ACTION.append("batch")
      continue

    if argx in ("-sf","--supported","--supported-filters"):
      ACTION.append("list_filters")
      continue

    if argx in ("-df","--describe","--describe-filters"):
      ACTION.append("descr_filters")
      DESC_FILTERS=args.pop(0)
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
