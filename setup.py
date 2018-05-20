"""Setup file for typedargs."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

# Caveats and possible issues
# Mac OS X
# - when using a virtualenv, readline is not properly installed into the virtualenv
#   and cannot be imported.  You need to install it using easy_install as described here
#   http://calvinx.com/tag/readline/


from setuptools import setup, find_packages
from version import version

setup(
    name="typedargs",
    packages=find_packages(exclude=("test",)),
    version=version,
    license="LGPLv3",
    install_requires=[
        "decorator>=3.4.0",
        "future>=0.16.0",
        "pyreadline>=2.1.0;platform_system==\"Windows\""
    ],
    description="A typechecking and shell generation program for python APIs",
    author="Arch",
    author_email="info@arch-iot.com",
    url="https://github.com/iotile/typedargs",
    keywords=[""],
    classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    long_description="""\
TypedArgs
---------

TypedArgs provides a way to annotate python 2.7 functions with type information that allows
the quick creation of custom command line shells.
"""
)
