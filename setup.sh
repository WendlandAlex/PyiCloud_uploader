#!/bin/sh
set -e
python3 -m venv .
bin/python3 -m pip install -r requirements.txt >> /dev/null 2>&1
# do a sed expression to insert a code snippet of 2 new lines with indentation to set params before the drive service class init is called
PYTHON3_SITE_PACKAGES=$(find lib/ -type d -name 'python3*')/site-packages
sed -i '/if not self._drive:/a \
            if not \"clientId\" in self.params:\
                self.params[\"clientId\"] = self.client_id' \
${PYTHON3_SITE_PACKAGES}/pyicloud/base.py >> /dev/null 2>&1