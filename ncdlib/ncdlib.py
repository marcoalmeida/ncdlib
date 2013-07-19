#!/usr/bin/env python3

import sys
import os
import shutil
import subprocess
import tempfile
from optparse import OptionParser


# known compressors mapping: name->bin; a list with more than one
# binary means that there is more than one known compressor
# implementing the same algorithm; they are ordered by preference;
# names are always in upper-case
KNOWN_COMPRESSORS = {"LZMA":["plzip", "lzip"], "BZIP2": "bzip2", "LZ77":"gzip",
                     "LZW":"compress", "PPMZ":["ppmz", "static-ppmz"],
                     "PPMD":"ppmd", "PAQ": "paq8l"}

# function for verbose output; by default, it doesn't do anything; it
# is redefined when _enable_verbose()
_verbose = lambda *a, **k: None

# return True iff the command cmd is available and can be executed
def _cmd_exists(cmd):
    try:
        subprocess.check_output("which %s" % cmd, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

# redefine the _verbose function
def _enable_verbose(enable=True):
    global _verbose
    if enable:
        _verbose = print
    else:
        _verbose = lambda *a, **k: None

# search the system for available (usable) compressors
def available_compressors():
    """Search the system for usable compressors. Return a dictionary
    similar to KNOWN_COMPRESSORS: each key is an algorithm's name, and
    its value is the command line tool that implements it."""
    compressors = {}
    for (name, binary) in KNOWN_COMPRESSORS.items():
        # try to find the binary by order of preference
        if type(binary) is list:
            for b in binary:
                if _cmd_exists(b):
                    compressors[name] = b
                    break
        else:
            if _cmd_exists(binary):
                compressors[name] = binary
    return compressors

# apply a given compressor with cmd; return the full path to the
# resulting compressed file or None if something fails
def _compress_any(cmd, result):
    try:
        _verbose("Trying '%s'" % cmd)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _verbose("Failed '%s': %s\n\t%s" % (cmd, e, e.output))
        # try to cleanup
        try:
            _verbose("Trying to remove '%s'" % result)
            os.remove(result)
        except OSError as e:
            _verbose("Failed to remove '%s': %s" % (result, e))
            # doesn't really matter
            pass
        return None
    # return the full path to the compressed file
    return result

def _compress_LZMA(fl, binary, verbose=False):
    cmd = "%s -f --best %s" % (binary, fl)
    result = "%s.lz" % fl
    return _compress_any(cmd, result)

def _compress_BZIP2(fl, binary, verbose=False):
    cmd = "%s -z -f --best %s" % (binary, fl)
    result = "%s.bz2" % fl
    return _compress_any(cmd, result)

def _compress_LZ77(fl, binary, verbose=False):
    cmd = "%s -f --best %s" % (binary, fl)
    result = "%s.gz" % fl
    return _compress_any(cmd, result)

def _compress_LZW(fl, binary, verbose=False):
    cmd = "%s -f %s" % (binary, fl)
    result = "%s.Z" % fl
    return _compress_any(cmd, result)

def _compress_PPMZ(fl, binary, verbose=False):
    cmd = "%s -b %s %s.ppmz" % (binary, fl, fl)
    result = "%s.ppmz" % fl
    return _compress_any(cmd, result)

def _compress_PPMD(fl, binary, verbose=False):
    cmd = "%s e -d -m256 -o16 -r1 -f%s.ppmd %s" % (binary, fl, fl)
    result = "%s.ppmd" % fl
    return _compress_any(cmd, result)

def _compress_PAQ(fl, binary, verbose=False):
    cmd = "%s -8 %s" % (binary, fl)
    result = "%s.paq8l" % fl
    return _compress_any(cmd, result)

# concatenate file1 and file2 into a new (temporary) file created in
# working directory wd; return the full path to the new file
def _concat(file1, file2, wd, verbose=False):
    # create a new temporary file
    (tmp_file, tmp_path) = tempfile.mkstemp(dir=wd)
    # concatenate file1 and file2 into tmpfl
    os.system("cat %s %s > %s" % (file1, file2, tmp_path))
    # close the file
    os.fdopen(tmp_file).close()
    # return the full path to tmpfl (it's the caller function's
    # responsability to delete it)
    return tmp_path

# ;
def _compress(fl, wd, compressor_name, compressor_binary, verbose=False):
    """
    Compress a file with some compressor.

    fl: file to compress
    compressor_name: name of the compressor to use - as returned by
    available_compressors()
    compressor_binary: command line tool for 'compressor_name' - as
    returned by available_compressors()
    verbose: enable/disable verbose output (to the console)

    returns: the size of the resulting compressed file

    """

    # create a new temporary file to copy the data to and close it so
    # that it can be used
    (tmp_file, tmp_path) = tempfile.mkstemp(dir=wd)
    os.fdopen(tmp_file).close()
    # copy fl to wd
    shutil.copy(fl, tmp_path)
    # compress the new file using the specified compressor
    compressed_file = eval("_compress_%s(tmp_path, compressor_binary, verbose)" % compressor_name)
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

# compute the compressed size of each component used to calculate the
# NCD (files and respective concatenation)
def _compressed_values(input_x, input_y, wd, compressor_name, compressor_binary, verbose=False):
    cx = _compress(input_x, wd, compressor_name, compressor_binary, verbose)
    cy = _compress(input_y, wd, compressor_name, compressor_binary, verbose)
    # concatenate both files and compute the compressed size
    input_xy = _concat(input_x, input_y, wd, verbose)
    cxy = _compress(input_xy, wd, compressor_name, compressor_binary, verbose)
    input_yx = _concat(input_y, input_x, wd, verbose)
    cyx = _compress(input_yx, wd, compressor_name, compressor_binary, verbose)
    # delete the temporary file that resulted from the concatenation
    os.remove(input_xy)
    os.remove(input_yx)
    # apply the formula and return the value iff all values were
    # successfully computed
    if None not in [cx, cy, cxy, cyx]:
        return (cx, cy, cxy, cyx)
    return (None, None, None)

def compute_ncd(input_x, input_y, compressor_name=None, wd="/tmp", verbose=False):
    """
    Compute the NCD of two files using some compressor.

    input_x and input_y are the input files whose NCD will be
    calculated. compressor_name is the name of the compressor
    (algorithm family) to use, as returned by
    available_compressors(). If compressor_name is None, all available
    compressors are used and the best (smallest) result is used.

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
    compressor_binary = available_compressors()
    if compressor_name is not None:
        (cx, cy, cxy, cyx) = _compressed_values(input_x, input_y, wd, compressor_name, compressor_binary[compressor_name], verbose)
    else:
        # worst possible values
        cx = 10*os.stat(input_x).st_size
        cy = 10*os.stat(input_y).st_size
        cxy = cx+cy
        cyx = cx+cy
        # loop through all available compressors and choose the best
        # possible compression value for each component
        for c in compressor_binary:
            (ncx, ncy, ncxy, ncyx) = _compressed_values(input_x, input_y, wd, c, compressor_binary[c], verbose)
            cx = min(cx, ncx)
            cy = min(cy, ncy)
            cxy = min(cxy, ncxy)
            cyx = min(cyx, ncyx)
    # the distance; we use Steven de Rooij's approximation of NID:
    # min{ C(xy), C(yx)} - min{ C(x), C(y) } on the numerator
    d = (min(cxy, cyx)-min(cx, cy))/max(cx, cy)
    if verbose:
        return (cx, cy, cxy, cyx, d)
    return d
