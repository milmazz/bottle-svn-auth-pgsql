import os
import sys
import site

# Remember original sys.path
prev_sys_path = sys.path

# Tell WSGI to add the Python site-packages to its path
site.addsitedir('/srv/virtualenvs/recover.example.com/lib/python2.7/site-packages')

# Reorder sys.path so new directories at the front
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

# Append the root directory in your python system path
sys.path.append('/srv/www/recover.example.com/site')

# activate the virtual environment
activate_this = '/srv/virtualenvs/recover.example.com/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import bottle
import passwd

bottle.TEMPLATE_PATH.insert(0,'/srv/www/recover.example.com/site/views/')

application = bottle.default_app()