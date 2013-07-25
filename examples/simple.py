#!/usr/bin/env python3

# Copyright (C) 2013  Marco Almeida <mfa@ncc.up.pt>

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
# make sure the lib is available
cur_path = os.path.realpath(__file__)
cur_dir = os.path.dirname(cur_path)
sys.path.append(os.path.join(cur_dir, ".."))
import ncdlib

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: %s <file1> <file2>" % sys.argv[0])
    ncd = ncdlib.compute_ncd(sys.argv[1], sys.argv[2], verbose=False)
    print("NCD({}, {}) = {}".format(sys.argv[1], sys.argv[2], ncd))
    
