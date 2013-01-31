What's this
===========
Font-end development always need techniques for replacing some request from the server, via altenative host or via local file replacement. This project aimed to facilitate all sorts of request replacement/redirection for front-end development, works the same way fiddler does.


TODO
====
typescript support 

Request viewer need a filter system.

Request builder

plug-ins
  #500
	#edit (intercept message and modify mechanism)
	#addfirebug
	#replace xxx aaa

folder match use beginwith

settings: group name use hostname match

ssl support

Features
========
Context menu added to Config window DONE
Context menu added to Log window    DONE
log with file and change log window to request response list    DONE
Python3 support		DONE
config reload	DONE
redirect ip support port	DONE
dir match default to index.html if no remainder exist	DONE
UI use Listbox instead of ScrolledText	DONE
Quit does not quit server	DONE


Settings
--------

config_sepperator	DONE
port                DONE
localhost_only::
    This is better done with server
section enabled     DONE::
    for line enabled just comment the line

redirection and 4xx, 5xx errors DONE


Bugs
====
exit sometimes block.
Logging algorithm use lock and huge iteration, may cause performance issues.

keep log using events, dont keep records in lib/blackhole   FIXED
log window is not top most window   FIXED
regenerate qzmin if deleted     FIXED
save config crash UI, save succeed
logging from threads sometimes block    FIXED
fiddler proxy setting prevent successful setting proxy	FIXED
