=========
StubShell
=========

Create an SSH Server, with a shell that provides Stubbed Commands

Purpose
-------
For testing, emulate a server's SSH Shell interface and commands

Installation
------------
Python:
=======
Runs on Python 2.7, until Twisted is updated to work on 3.4

conda_env.yaml is provided to set up a conda virtual environment

If you have miniconda or anaconda installed, run::
    conda create --name StubShell --file conda_env.yaml

package:
========

standard setup.py install::
    python setup.py install

this will create an executable entry-point in your site-packages/bin dir

run the server:
===============
if you installed the package you can use the executable entry-point::
    stubshell -c path/to/your/custom_executables

you can also run it manually with the run_stubshell.py helper script in the project directory::
    python run_stubshell.py -c path/to/your/custom_executables

Twisted
-------
Created using the [Twisted](https://twistedmatrix.com/trac/) framework

Esp. Twisted Conch for all the SSH magic.

Credits
-------
StubShell is derived from [MockSSH](https://github.com/ncouture/MockSSH),
which was derived from [kippo](https://github.com/desaster/kippo/), an SSH honeypot.

I used MockSSH for inspiration, and initial trials, but found it lacked some key features
that my application requires, so i am re-writing using TDD
