" JUH - HUmanized Json file syntax file
" 20220209, Ing. Ondrej DURAS
" VERSION=2022.031701
" JSON files have comments removed by standard as to prevent
" metacommands within json files. It could be fine for machine-to-machine,
" but it's really unconfortable for human-to-machine communication.
" That's why ... I have allowed comments within my JSON files back.
" And before the file content is passed to machine, the comments are removed.
" These files are called .juh becose .huj is peiorative in east Slovak dialect.

set cursorline
set iskeyword+=.
set iskeyword+=/
set iskeyword+=:
set iskeyword+=-

syntax match juh_marker  /[:,\{\}\[\]]/
syntax match juh_comment /^\s\+#.*$/
syntax match juh_comment /#[^"]\+$/
syntax match juh_value   /".*",\?$/  contains=juh_marker


syntax match juh_first   /^"\S\+"\s*:/  contains=juh_marker
syntax match juh_second  /^ \+"\S\+"\s*:/

syntax match juh_red   /^.*<<r.*$/
syntax match juh_blue  /^.*<<b.*$/
syntax match juh_green /^.*<<g.*$/
syntax match juh_gray  /^.*<<k.*$/
syntax match juh_gray  /^.*<<<.*$/

"high Normal      ctermfg=grey     guifg=#808080 
"high juh_marker  ctermfg=red      guifg=#800000 
"high juh_comment ctermfg=green    guifg=#008000 
"high juh_first   ctermfg=cyan     guifg=#00e0e0 
"high juh_second  ctermfg=darkcyan guifg=#008080
"high juh_value   ctermfg=brown    guifg=#808000 
                                                
"high juh_red     ctermfg=red      guifg=#e00000 
"high juh_blue    ctermfg=blue     guifg=#0000e0 
"high juh_green   ctermfg=green    guifg=#00e000 
"high juh_gray    ctermfg=darkgray guifg=#404040


high Normal      ctermfg=grey     guifg=grey     
high juh_marker  ctermfg=red      guifg=red      
high juh_comment ctermfg=green    guifg=green    
high juh_first   ctermfg=cyan     guifg=cyan     
high juh_second  ctermfg=darkcyan guifg=darkcyan
high juh_value   ctermfg=brown    guifg=brown    
                                                 
high juh_red     ctermfg=red      guifg=red      
high juh_blue    ctermfg=blue     guifg=blue     
high juh_green   ctermfg=green    guifg=green    
high juh_gray    ctermfg=darkgray guifg=darkgray
" --- end ---
