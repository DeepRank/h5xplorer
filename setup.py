#from distutils.core import setup
from setuptools import setup

setup(
    name='h5xplorer',
    description='A customizable HDF5 Browser',
    version='0.1',
    url='https://github.com/DeepRank/h5xplorer',
    packages=['h5xplorer'],


    install_requires=[,
        'h5py',
        'PyQt5',
        'matplotlib',
        'qtconsole',
        'IPython' ],

    extras_require= {
        'test': ['nose', 'coverage', 'pytest',
                 'pytest-cov','codacy-coverage','coveralls'],
    }
)