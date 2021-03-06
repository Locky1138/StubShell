"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import re

#get __version__ from _version.py
version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('stubshell/StubShell.py').read(),
    re.M
    ).group(1)




# Get the long description from the relevant file
with open('DESCRIPTION.rst') as f:
    long_description = f.read()


setup(
    # Application name:
    name="StubShell",

    # Version number (initial):
    version=version,

    # Application author details:
    author="Locky",
    author_email="Locky1138@gmail.com",

    license='MIT',

    # Packages
    #packages=["ipcentermodules"],
    packages=find_packages(),

    # entry points, to generate executables in python/bin/
    entry_points = {
        "console_scripts": ['stubshell = stubshell.RunServer:main']
        },

    # Include additional files into the package
    # WARNING not a distutils option
    #include_package_data=True,

    # Details
    url="https://github.com/Locky1138/StubShell",

    #
    # license="LICENSE.txt",
    description="Create a fake bash shell for testing purposes",

    long_description=long_description,

    # Dependent packages (distributions)
    install_requires=[
        'twisted',
        'pexpect'
    ],
)
