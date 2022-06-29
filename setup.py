#!/usr/bin/env python

import os
from setuptools import (find_packages, setup)

here = os.path.abspath(os.path.dirname(__file__))

# To update the package version number, edit h5xplorer/__version__.py
version = {}
with open(os.path.join(here, 'h5xplorer', '__version__.py')) as f:
    exec(f.read(), version)

with open('README.md') as readme_file:
    readme = readme_file.read()


setup(
    name='h5xplorer',
    version=version['__version__'],
    description="A customizable HDF5 browser",
    long_description=readme + '\n\n',
    long_description_content_type='text/markdown',
    author=["Nicolas Renaud"],
    author_email='n.renaud@esciencecenter.nl',
    url='https://github.com/DeepRank/h5xplorer',
    packages=find_packages(),
    package_dir={'h5xplorer': 'h5xplorer'},
    include_package_data=True,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='h5xplorer',

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Visualization'
    ],
    test_suite='tests',


    install_requires=['h5py','PyQt5','matplotlib',
        'qtconsole','IPython' ],

    extras_require={
        'dev': ['prospector[with_pyroma]', 'yapf', 'isort'],
        'doc': ['recommonmark', 'sphinx', 'sphinx_rtd_theme'],
        'test': ['nose','coverage', 'pycodestyle', 'pytest', 'pytest-cov', 'pytest-runner','coveralls'],
        'publishing': ['build', 'twine', 'wheel']
    }
)
