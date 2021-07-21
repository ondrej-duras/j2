##!/usr/bin/env python
##!/usr/bin/env python2
##!/usr/bin/env python3
# 20210720, Ondrej DURAS (dury)
# .J2 helper

## MANUAL ############################################################# {{{ 1
VERSION = 2021.072102
MANUAL  = """
NAME: J2 - ansible .J2 template parser
FILE: j2.py

DESCRIPTION:
  Do you hate ansible ?
  For the preparation of some configuration 
  change have you been instructed to use 
  ansible .J2 templates only ?
  Ok. This script could help you.
  For the most basic cases you should 
  not need ansible anymore.
  This standalone script is for free.
  You need pure python2 or python3.
  None additional python modules are needed.

EXAMPLES:
  j2.py -g template.j2 >input.txt
  j2.py -l template.j2 >input.csv
  j2.py -s input.txt -t template.j2 >config.cfg
  j2.py -m input.txt -t template.j2 >config.cfg
  j2.py -x input.csv -t template.j2 >config.cfg

FILE TYPES:
  template.j2 - .J2 ansible template file
  config.cfg  - template based outp[ut file - change ticket
  input.csv   - input file, where each line contains all items
  input.txt   - input file, where each line contains one item
                If multiple inputs are contained, then
                particular inputs should be separated by "---"
    
PARAMETERS:
  -g - transforms a .J2 to its example input.txt (single)
  -l - transfroms a .J2 to its example input.csv (csv multiple)
  -s - uses input.txt as single input for single usage of template
  -m - uses input.txt as multiple input for multiple usage of template
  --vim - VIM editor customisation

SEE ALSO:
  https://github.com/ondrej-duras/

VERSION: %s GPL2
""" % (VERSION)

####################################################################### }}} 1
## DECLARATION ######################################################## {{{ 1

import sys
import datetime
import re

LAST_CONFIG = ""  # last parsed config
LAST_TABLE  = ""  # last parsed table
CONFIG      = ""  # configuration learned from file .TXT / .CSV
TEMPLATE    = ""  # template learned from file .J2
CONFIG_FN   = ""  # file name of config
TEMPLATE_FN = ""  # file name of template
MAX_SPLITS  = 0   # Maximal number of splitted items - mandatory value fo tableItems
ACTIONS     = []  # list of actions
DEBUG       = ""  # debugging class 

VIMEXT = False    # VIM text customisation
VIMADD = """
#=vim set iskeyword+={
#=vim set iskeyword+=}
#=vim syntax match Xansible /{{\S\+}}/
#=vim high Xansible ctermfg=darkred
#=vim high Comment ctermfg=darkgreen
"""
 
####################################################################### }}} 1
## COMMON LIBRARY ##################################################### {{{ 1


def debug(types,txt):
  global DEBUG
  if not DEBUG: return
  types2 = "all." + types
  if not (DEBUG in types2): return
  for line in str(txt).splitlines():
    print("#[%s]: %s" % (types,line))


def readFile(filename):
  debug("readfile.filename",filename)
  fh=open(filename,"r")
  txt=fh.read()
  fh.close()
  debug("readfile.content",txt)
  return txt


####################################################################### }}} 1
## EXTRACTION of .J2 ################################################## {{{ 1

def extractItems(template,format="j2"):
  # format=j2  {{item_xxx}} used by ansible (*default)
  # format=txt <ITEM_XXX>   used by PYCODE
  global TEMPLATE
  out={}
  for line in TEMPLATE.splitlines():
    #items=re.findall("\{\{[0-9A-Za-z_.]+\}\}",line) # {{[item}}
    #items=re.findall("<[0-9A-Za-z_.]+>",line)       # <ITEM>
    items=re.findall(r"\{\{[0-9A-Za-z_.]+\}\}",line)
    for item in items:
      if item in out.keys():
         out[item]+=1
      else:
         out[item]=1
  return out



def extract2txt(template,format="j2"):
  out = ""
  if isinstance(template,dict): src=template
  elif isinstance(template,str): src=extractItems(template,format)
  #for (key,val) in src.items():
  for key in sorted(src.keys()):
    val=src[key]
    out += "%-15s %2d\n" % (key,int(val))
  return out



def extract2csv(template,format="j2"):
  out = ""
  if isinstance(template,dict): src=template
  elif isinstance(template,str): src=extractItems(template,format)
  #for (key,val) in src.items():
  out += " ; ".join(sorted(src.keys())) + "\n"
  for key in sorted(src.keys()):
    val=str(src[key])
    val += " " * (len(key) - len(str(val)))
    out += val + " ; "
  out=re.sub(" ; $","\n",out)
  return out


####################################################################### }}} 1
## OUTPUT COMPOSITION ################################################# {{{ 1

def tableItems(template,table,maxsplits):
  out = ""
  global LAST_TABLE; LAST_TABLE = table
  for line in table.splitlines():
    if re.match("\s*#",line): continue
    if re.match("\s*$",line): continue
    aline = re.sub("#[^#]+$","",line)
    col = re.split("\s+",aline,maxsplits)
    if len(col) < (maxsplits+1): continue
    text = template
    for i in range(0,maxsplits+1):
      pat = "<COL_%d>" % (i)
      text = text.replace(pat,col[i])
    out += text
  return out



def learnItems(src):
  out={}
  for aline in src.splitlines():
    line = re.sub("#[^#]+$","",aline)
    if not re.match("\S+\s+\S+",line): continue
    (item,value) = re.split("\s+",line,1)
    if item[0:2] == "<&" : value=eval(value); item=item.replace("&","")
    debug("learnitems","'%s' == '%s'" % (item,value))
    out[item] = value
  return out


def learnMultipleCsvItems(src):
  global DEBUG
  outs=[]     # all inputs in one list
  out={}      # one input for one template application
  out_key=[]  # key of one input
  out_val=[]  # values of one input

  lines=[]    # valid lines of csv file only
  for line in src.splitlines():
    if re.match("^\s*$",line): continue
    if re.match("^\s*#",line): continue
    lines.append(line)
  debug("learncsvitems.lines.count",len(lines))

  out_key=re.split("\s*;\s*",lines[0])
  out_key_len=len(out_key)
  debug("learncsvitems.header.count",out_key_len)

  for inx in range(1,len(lines)):
    out={}
    out_val=re.split("\s*;\s*",lines[inx])
    if len(out_val) != out_key_len:
      debug("learncsvitems.row.count_mistmatch",inx)
      continue
    for iny in range(out_key_len):
      out[out_key[iny]]=out_val[iny]
    outs.append(out)
    if DEBUG:
      debug("learnmultiplecsvitems.csvline",out)
  return outs


def replaceItems(template,source):
  global LAST_CONFIG
  if isinstance(source,str): src=learnItems(source); LAST_CONFIG=source
  elif isinstance(source,dict): src=source; LAST_CONFIG=""
  else: print("Error !")
  out=template
  for item in src.keys():
    if item[0:2] == "<!": value=eval(src[item])
    else: value = src[item]
    out = out.replace(item,value)
  return out


def replaceMultipleItems(template,sources):
  out=""
  debug("replacemultipleitems.sources.count",len(sources))
  debug("replacemultipleitems.sources.content",sources)
  for source in sources:
    out += replaceItems(template,source)
    debug("replacemultipleitems.source",source)
    debug("replacemultipleitems.template",template)
  return out

####################################################################### }}} 1
## ACTIONS ############################################################ {{{ 1


def takeAction():
  global MANUAL,CONFIG,CONFIGS,TEMPLATE,CONFIN_FN,TEMPLATE_FN
  global VIMEXT,VIMADD
  FFLAG = 0
  debug("action.actions",str(ACTIONS))


  if "help" in ACTIONS:
    print(MANUAL)
    debug("action.manual","done")


  if "readConfig" in ACTIONS:
    CONFIG=readFile(CONFIG_FN)
    FFLAG += 1
    debug("action.readconfig",CONFIG_FN)


  if "readTemplate" in ACTIONS:
    TEMPLATE=readFile(TEMPLATE_FN)
    FFLAG += 2
    debug("action.readtemplate",TEMPLATE_FN)


  if "learnMultipleCsvItems" in ACTIONS:
    CONFIGS=learnMultipleCsvItems(CONFIG)
    FFLAG += 4
    debug("action.learnmultiplecsvitems",CONFIG_FN)


  if "replaceItems" in ACTIONS:
    debug("action.replaceitems",FFLAG)
    if FFLAG == 3:
      if VIMEXT: print(VIMADD)
      print(replaceItems(TEMPLATE,CONFIG))
      debug("action.replaceitems","done")


  if "replaceMultipleItems" in ACTIONS:
    debug("action.replacemultipleitems",FFLAG)
    if FFLAG == 7:
      if VIMEXT: print(VIMADD)
      print(replaceMultipleItems(TEMPLATE,CONFIGS))
      debug("action.replacemultipleitems","done")


  if "extract2txt" in ACTIONS:
    if FFLAG & 2:
      debug("action.extract2txt",TEMPLATE_FN)
      if VIMEXT: print(VIMADD)
      print(extract2txt(TEMPLATE))


  if "extract2csv" in ACTIONS:
    if FFLAG & 2:
      debug("action.extract2csv",TEMPLATE_FN)
      print(extract2csv(TEMPLATE))
      if VIMEXT: print(VIMADD)


####################################################################### }}} 1
## CLI ################################################################ {{{ 1

def cmdLine():
  global ACTIONS,MANUAL,DEBUG
  global TEMPLATE_FN,CONFIG_FN
  global VIMEXT,VIMADD
  argct=len(sys.argv)
  if argct < 2:
    ACTIONS.append("help")
    debug("cli.help","no-arg")
    return

  argi=1
  while argi < argct:
    argx=sys.argv[argi]
    argi+=1

    if argx in ("-v","--verbose","--debug"):
      DEBUG=sys.argv[argi]; argi+=1
      debug("cli.debug",DEBUG)
      continue

    if argx in ("--vim"):
      VIMEXT=True
      continue

    if argx in ("-?","-h","--help"):
      ACTIONS.append("help")
      debug("cli.help",argx)
      continue

    if argx in ("-s","--single"): 
      CONFIG_FN=sys.argv[argi]; argi+=1
      ACTIONS.append("readConfig")
      ACTIONS.append("replaceItems")
      debug("cli.input.single",CONFIG_FN)
      continue

    if argx in ("-t","--tmp","--template"): 
      TEMPLATE_FN=sys.argv[argi]; argi+=1
      ACTIONS.append("readTemplate")
      debug("cli.template",TEMPLATE_FN)
      continue

    if argx in ("-g","--2txt","--tmp2txt"): 
      TEMPLATE_FN=sys.argv[argi]; argi+=1
      ACTIONS.append("readTemplate")
      ACTIONS.append("extract2txt")
      debug("cli.extract2txt",TEMPLATE_FN)
      continue

    if argx in ("-l","--2csv","--tmp2csv"): 
      TEMPLATE_FN=sys.argv[argi]; argi+=1
      ACTIONS.append("readTemplate")
      ACTIONS.append("extract2csv")
      debug("cli.extract2csv",TEMPLATE_FN)
      continue

    if argx in ("-x","--csv",): 
      CONFIG_FN=sys.argv[argi]; argi+=1
      ACTIONS.append("readConfig")
      ACTIONS.append("learnMultipleCsvItems")
      ACTIONS.append("replaceMultipleItems")
      debug("cli.input.csv",CONFIG_FN)
      continue

    print("# Error! wrong argument '%s'" % (argx))
    exit()
    
####################################################################### }}} 1
## MAIN ############################################################### {{{ 1

if __name__ == "__main__":
  cmdLine()  
  takeAction()

####################################################################### }}} 1
# --- end ---
