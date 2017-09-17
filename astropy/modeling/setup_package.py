# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os
from os.path import join

from distutils.core import Extension
from distutils import log

from astropy_helpers import setup_helpers, utils
from astropy_helpers.version_helpers import get_pkg_version_module

wcs_setup_package = utils.import_file(join('astropy', 'wcs', 'setup_package.py'))


MODELING_ROOT = os.path.relpath(os.path.dirname(__file__))
MODELING_SRC = join(MODELING_ROOT, 'src')
SRC_FILES = [join(MODELING_SRC, 'projections.c.templ'),
             __file__]
GEN_FILES = [join(MODELING_SRC, 'projections.c')]


# This defines the set of projection functions that we want to wrap.
# The key is the projection name, and the value is the number of
# parameters.

# (These are in the order that the appear in the WCS coordinate
# systems paper).
projections = {
    'azp': 2,
    'szp': 3,
    'tan': 0,
    'stg': 0,
    'sin': 2,
    'arc': 0,
    'zea': 0,
    'air': 1,
    'cyp': 2,
    'cea': 1,
    'mer': 0,
    'sfl': 0,
    'par': 0,
    'mol': 0,
    'ait': 0,
    'cop': 2,
    'coe': 2,
    'cod': 2,
    'coo': 2,
    'bon': 1,
    'pco': 0,
    'tsc': 0,
    'csc': 0,
    'qsc': 0,
    'hpx': 2,
    'xph': 0,
}


def pre_build_py_hook(cmd_obj):
    preprocess_source()


def pre_build_ext_hook(cmd_obj):
    preprocess_source()


def pre_sdist_hook(cmd_obj):
    preprocess_source()


def preprocess_source():
    # TODO: Move this to setup_helpers

    # Generating the wcslib wrappers should only be done if needed. This also
    # ensures that it is not done for any release tarball since those will
    # include core.py and core.c.
    if all(os.path.exists(filename) for filename in GEN_FILES):
        # Determine modification times
        src_mtime = max(os.path.getmtime(filename) for filename in SRC_FILES)
        gen_mtime = min(os.path.getmtime(filename) for filename in GEN_FILES)

        version = get_pkg_version_module('astropy')

        if gen_mtime > src_mtime:
            # If generated source is recent enough, don't update
            return
        elif version.release:
            # or, if we're on a release, issue a warning, but go ahead and use
            # the wrappers anyway
            log.warn('WARNING: The autogenerated wrappers in '
                     'astropy.modeling._projections seem to be older '
                     'than the source templates used to create '
                     'them. Because this is a release version we will '
                     'use them anyway, but this might be a sign of '
                     'some sort of version mismatch or other '
                     'tampering. Or it might just mean you moved '
                     'some files around or otherwise accidentally '
                     'changed timestamps.')
            return
        # otherwise rebuild the autogenerated files

        # If jinja2 isn't present, then print a warning and use existing files
        try:
            import jinja2  # pylint: disable=W0611
        except ImportError:
            log.warn("WARNING: jinja2 could not be imported, so the existing "
                     "modeling _projections.c file will be used")
            return

    from jinja2 import Environment, FileSystemLoader

    # Prepare the jinja2 templating environment
    env = Environment(loader=FileSystemLoader(MODELING_SRC))

    c_in = env.get_template('projections.c.templ')
    c_out = c_in.render(projections=projections)

    with open(join(MODELING_SRC, 'projections.c'), 'w') as fd:
        fd.write(c_out)


def get_package_data():
    return {
        'astropy.modeling.tests': ['data/*.fits', 'data/*.hdr',
                                   '../../wcs/tests/maps/*.hdr']
    }


def requires_2to3():
    return False


def get_extensions():
    wcslib_files = [  # List of wcslib files to compile
        'prj.c',
        'wcserr.c',
        'wcsprintf.c',
        'wcsutil.c'
    ]

    wcslib_config_paths = [
        join(MODELING_SRC, 'wcsconfig.h')
    ]

    cfg = setup_helpers.DistutilsExtensionArgs()

    wcs_setup_package.get_wcslib_cfg(cfg, wcslib_files, wcslib_config_paths)

    cfg['include_dirs'].append(MODELING_SRC)

    astropy_files = [  # List of astropy.modeling files to compile
        'projections.c'
    ]
    cfg['sources'].extend(join(MODELING_SRC, x) for x in astropy_files)

    cfg['sources'] = [str(x) for x in cfg['sources']]
    cfg = dict((str(key), val) for key, val in six.iteritems(cfg))

    return [Extension(str('astropy.modeling._projections'), **cfg)]
