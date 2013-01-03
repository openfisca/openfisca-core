# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

import os

if os.environ['QT_API'] == 'pyqt':
    from PyQt4.QtCore import *  # analysis:ignore
    from PyQt4.Qt import QCoreApplication  # analysis:ignore
    from PyQt4.Qt import Qt  # analysis:ignore
    from PyQt4.QtCore import pyqtSignal as Signal  # analysis:ignore
    from PyQt4.QtCore import pyqtSlot as Slot  # analysis:ignore
    from PyQt4.QtCore import pyqtProperty as Property  # analysis:ignore
    from PyQt4.QtCore import QT_VERSION_STR as __version__
    try:  
        from PyQt4.QtCore import QString  
    except ImportError:  
        # we are using PyQt4 >= 4.6  so QString is not defined  
        QString = unicode  
        
else:
    import PySide.QtCore
    __version__ = PySide.QtCore.__version__  # analysis:ignore
    from PySide.QtCore import *  # analysis:ignore
