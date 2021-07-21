# J2
::
    
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

