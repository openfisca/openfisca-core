"""
    OpenFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenFisca.  If not, see <http://www.gnu.org/licenses/>.
"""



import os

__version__ = "0.1.4"
__project_url__ = "http://www.openfisca.fr/"
__forum_url__  = "http://github.com/openfisca/openfisca/issues?state=open"

DATAPATH = LOCALEPATH = DOCPATH = ''

SRC_PATH = os.path.join(os.path.dirname(os.path.abspath( __file__ )))