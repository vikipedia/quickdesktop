#!/usr/bin/python
import sys
import unittest
from quickdesktop import tool

HELP = """
This uitility script helps in creating new desktop tool using 
quickdesktop library.

qdesktop.py options [arguments]

available options for qdesktop.py are

create name:
	This creates folder structure and basic configuration to create 
new desktop tool. Name of the tool should be the next argument.

test:
	Run all unittests from quickdesktop.


"""

if __name__ == "__main__":
    if len(sys.argv)<2:
        print HELP
    elif sys.argv[1]=="create":
        tool.createTool(sys.argv[2])
    elif sys.argv[1]=="help":
        print HELP

