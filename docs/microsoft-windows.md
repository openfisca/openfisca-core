# OpenFisca on Microsoft Windows

## Installation

### Git

Install [Git](http://www.git-scm.com/) for Windows. It provides a "bash" shell.

### Python

Install [Python](http://www.python.org/) 2.7 for your architecture (32 or 64 bits).

> To know your architecture, open the "Control panel" then the "System" item. You'll see the architecture under the "System" heading and "System type" item.

> It is recommeneded to install the 32 bits version, some users had issues with numpy.

### Python pip

Python pip (the package installer) is provided by the Windows installer of Python. You don't need to install it by hand.

### Python compiled packages

Microsoft Windows users should install pre-compiled packages from
[Christoph Gohlke page](http://www.lfd.uci.edu/~gohlke/pythonlibs/): numpy and scipy.

Download the last versions of the packages, for Python 2.7 and corresponding to the architecture the Python binary was compiled (32 or 64 bits).

> To know the architecture of the Python binary, just launch `python` and read the first line.

You'll download [Python Wheels](https://wheel.readthedocs.org/) packages.

First, open the "bash" shell from the "Start" menu then type:

```
pip install <package>.whl
```

> Tip: you can drag & drop the files from the Windows Explorer to the "bash" command line terminal.

### Add Python in PATH

Microsoft Windows users should add the Python scripts directory to the system PATH.
This can be done:

* by the Python installer, enabling the corresponding option during the install wizard;
* or after the installation, see [this stackoverflow question](http://stackoverflow.com/a/20458590).
