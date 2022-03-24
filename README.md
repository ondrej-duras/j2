# j2json
```
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

VERSION: 2022.032402 GPLv2
```
