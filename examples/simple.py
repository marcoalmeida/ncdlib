#!/usr/bin/env python

# Copyright (C) 2013  Marco Almeida <marcoafalmeida@gmail.com>

# This file is part of ncdlib.

# ncdlib is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.

# ncdlib is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

# You should have received a copy of the GNU General Public License
# along with ncdlib.  If not, see <http://www.gnu.org/licenses/>.


import sys
import os
import ncdlib

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: %s <file1> <file2>" % sys.argv[0])
    ncd = ncdlib.compute_ncd(sys.argv[1], sys.argv[2], ncdlib.LZMA, verbose=False)
    print("NCD({0}, {1}) = {2:.4f}".format(sys.argv[1], sys.argv[2], ncd))
