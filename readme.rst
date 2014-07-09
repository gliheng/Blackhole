What's this
===========
Blackhole is a font-end proxy debugging tool, like fiddler. It intercept http requests, replace them with local alternatives or forward them to their backend server. A variaty of replacement/redirection scheme can be configured to allow for easier front-end development.

Requirements
============

- This project is built with python3.3. Other versions are not guaranteed to work.
- No installation of 3rd part library is needed.
- Works on both windows and mac


TODO
====
- Buildout system
- Hostmod utility
- Elevate promistion on windows
- Request/Response viewer
- Request builder
- project based configuration
- Request list need a filter system.
- ssl support

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
