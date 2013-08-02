#!/usr/bin/env python
"""
Python implementation of the Normalized Compression Distance
"""

# Copyright (C) 2013  Marco Almeida <marcoafalmeida@gmail.com>

# This file is part of ncdlib.

# ncdlib is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ncdlib is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ncdlib.  If not, see <http://www.gnu.org/licenses/>.


import os
import logging
import shutil
import subprocess
import tempfile


# static constants to ease compressor specification
LZMA = "lzip"
BZIP2 = "bzip2"
LZ77 = "gzip"
LZW = "compress"
PPMZ = "ppmz"
PPMD = "ppmd"
PAQ8l = "paq8l"

# known compressors list, to be used when searching to available
# compressors installed on the system
KNOWN_COMPRESSORS = [LZMA, BZIP2, LZ77, LZW, PPMZ, PPMD, PAQ8l]


def _cmd_exists(cmd):
    """Return True iff the command cmd is available and can be
    executed."""
    try:
        subprocess.check_output("which %s" % cmd, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def _enable_verbose(enable=True):
    """Enable/disable verbose output."""
    if enable:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.WARNING)

# search the system for available (usable) compressors
def available_compressors():
    """Search the system for usable compressors. Return a subset of
    KNOWN_COMPRESSORS."""
    compressors = []
    for compressor in KNOWN_COMPRESSORS:
        if _cmd_exists(compressor):
            compressors.append(compressor)
    return compressors

def _compress_any(cmd, result):
    """Apply a given compressor with cmd. Return the full path to the
    resulting compressed file or None if something fails."""
    try:
        logging.info("Trying '%s'", cmd)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as p_err:
        logging.info("Failed '%s': %s\n\t%s", cmd, p_err, p_err.output)
        # try to cleanup
        try:
            logging.info("Trying to remove '%s'", result)
            os.remove(result)
        except OSError as os_err:
            # doesn't really matter
            logging.info("Failed to remove '%s': %s", result, os_err)
        return None
    # return the full path to the compressed file
    return result

def _compress_lzip(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s -f --best %s" % (binary, infile)
    result = "%s.lz" % infile
    return _compress_any(cmd, result)

def _compress_bzip2(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s -z -f --best %s" % (binary, infile)
    result = "%s.bz2" % infile
    return _compress_any(cmd, result)

def _compress_gzip(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s -f --best %s" % (binary, infile)
    result = "%s.gz" % infile
    return _compress_any(cmd, result)

def _compress_compress(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s -f %s" % (binary, infile)
    result = "%s.Z" % infile
    return _compress_any(cmd, result)

def _compress_ppmz(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s -b %s %s.ppmz" % (binary, infile, infile)
    result = "%s.ppmz" % infile
    return _compress_any(cmd, result)

def _compress_ppmd(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s e -d -m256 -o16 -r1 -f%s.ppmd %s" % (binary, infile, infile)
    result = "%s.ppmd" % infile
    return _compress_any(cmd, result)

def _compress_paq8l(infile, binary):
    """Compress infile and return the size of the resulting compressed
    file. The argument binary is the name/path of the command line
    tool that implements the chosen compressor."""
    cmd = "%s -8 %s" % (binary, infile)
    result = "%s.paq8l" % infile
    return _compress_any(cmd, result)

def _concat(file1, file2, tmp_dir):
    """Concatenate file1 and file2 into a new (temporary) file created
    in working directory tmp_dir. Return the full path to the new
    file."""
    # create a new temporary file
    (tmp_file, tmp_path) = tempfile.mkstemp(dir=tmp_dir)
    # concatenate file1 and file2 into tmpfl
    os.system("cat %s %s > %s" % (file1, file2, tmp_path))
    # close the file
    os.fdopen(tmp_file).close()
    # return the full path to tmpfl (it's the caller function's
    # responsability to delete it)
    return tmp_path

def _compress(infile, tmp_dir, compressor):
    """
    Compress infile with compressor using tmp_dir as working directory
    to create temporary files in. Return the size of the resulting
    compressed file.
    """

    # create a new temporary file to copy the data to and close it so
    # that it can be used
    (tmp_file, tmp_path) = tempfile.mkstemp(dir=tmp_dir)
    os.fdopen(tmp_file).close()
    # copy infile to tmp_dir
    shutil.copy(infile, tmp_path)
    # compress the new file using the specified compressor
    func_call = "_compress_%s(tmp_path, compressor)"
    compressed_file = eval(func_call % compressor.lower())
    if compressed_file is not None:
        # get the size of the compressed file
        size = os.stat(compressed_file).st_size
        # remove the compressed file
        os.remove(compressed_file)
        # depending on the compressor, the temporary tmp_file may or
        # may not have been destroyed replaced by the compressed
        # version, so we try to remove it
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        # return the size of the compressed file
        return size
    # something very wrong happend while trying to use the compressor;
    # cleanup and don't return anything
    os.remove(tmp_path)
    return None

def _compressed_values(input_x, input_y, tmp_dir, compressor):
    """Compute the compressed size of each component used to calculate
    the NCD (files and respective concatenation). Return a tuple with
    the files' sizes."""
    c_x = _compress(input_x, tmp_dir, compressor)
    c_y = _compress(input_y, tmp_dir, compressor)
    # concatenate both files and compute the compressed size
    input_xy = _concat(input_x, input_y, tmp_dir)
    c_xy = _compress(input_xy, tmp_dir, compressor)
    input_yx = _concat(input_y, input_x, tmp_dir)
    c_yx = _compress(input_yx, tmp_dir, compressor)
    # delete the temporary file that resulted from the concatenation
    os.remove(input_xy)
    os.remove(input_yx)
    # apply the formula and return the value iff all values were
    # successfully computed
    if None not in [c_x, c_y, c_xy, c_yx]:
        return (c_x, c_y, c_xy, c_yx)
    return (None, None, None)

def compute_ncd(input_x, input_y, compressor=LZMA,
                tmp_dir="/tmp", verbose=False):
    """
    Compute the NCD of two files using some compressor.

    input_x and input_y are the input files whose NCD will be
    calculated. compressor is the name of the compressor (algorithm
    family) to use, as returned by available_compressors(). It
    defaults to LZMA because it was the algorithm which produced the
    best results on a series of experiments in "An experimental study
    on normal compressors" by Almeida and Antunes.

    If verbose is True a description of each step of the algorithm is
    sent to the console output.

    Returns either the NCD value or, if verbose is True, a tuple
    (C(input_x),
     C(input_y),
     C(input_x+input_y),
     C(input_y+input_x),
     NCD(input_x, input_y))
    where a+b means concatenation of a and b.

    """
    # enable/disable verbose output
    _enable_verbose(verbose)
    # compress the files and get the necessary values to calculate the
    # NCD
    (c_x, c_y, c_xy, c_yx) = _compressed_values(input_x, input_y,
                                                tmp_dir, compressor)
    # we use Steven de Rooij's approximation of NID: min{ C(xy),
    # C(yx)} - min{ C(x), C(y) } on the numerator
    ncd = (float(min(c_xy, c_yx))-float(min(c_x, c_y)))/max(c_x, c_y)
    if verbose:
        return (c_x, c_y, c_xy, c_yx, ncd)
    return ncd
