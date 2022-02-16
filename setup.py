"""
    setup.py - Setup file to distribute the library
See Also:
    https://github.com/pypa/sampleproject
    https://packaging.python.org/en/latest/distributing.html
    https://pythonhosted.org/an_example_pypi_project/setuptools.html
"""
import os
import glob
from setuptools import setup, Extension, find_packages


def read(fname):
    """Read in a file"""
    with open(os.path.join(os.path.dirname(__file__), fname), 'r') as file:
        return file.read()


def get_meta(filename):
    """Return the metadata dictionary from the given filename."""
    with open(filename, 'r') as f:
        meta = {}
        exec(compile(f.read(), filename, 'exec'), meta)
        return meta


if __name__ == "__main__":
    # Variables
    meta = get_meta('continuous_threading/__meta__.py')
    name = meta['name']
    version = meta['version']
    description = meta['description']
    url = meta['url']
    author = meta['author']
    author_email = meta['author_email']
    keywords = 'threading continuous pausable'
    packages = find_packages(exclude=('tests', 'bin', 'dist', 'build'))

    # Extensions
    extensions = [
        # Extension('libname',
        #           # define_macros=[('MAJOR_VERSION', '1')],
        #           # extra_compile_args=['-std=c99'],
        #           sources=['file.c', 'dir/file.c'],
        #           include_dirs=['./dir'])
        ]

    setup(name=name,
          version=version,
          description=description,
          long_description=read('README.rst'),
          long_description_content_type='text/x-rst',
          keywords=keywords,
          url=url,
          download_url=''.join((url, '/archive/v', version, '.tar.gz')),

          author=author,
          author_email=author_email,

          license="MIT",
          platforms="any",
          classifiers=["Programming Language :: Python",
                       "Programming Language :: Python :: 3",
                       "Operating System :: OS Independent"],

          scripts=[file for file in glob.iglob('bin/*.py')],  # Run with python -m Scripts.module args

          ext_modules=extensions,  # C extensions
          packages=packages,
          include_package_data=True,
          # package_data={
          #     'package': ['slat_app/resources/resources/*']
          #     },

          # Data files outside of packages
          # data_files=[('my_data', ['data/my_data.dat'])],

          # options to install extra requirements
          install_requires=[
              'psutil>=5.4.0',
              ],
          # extras_require={
          #     '': [''],
          #     },

          # entry_points={
          #     'console_scripts': [
          #         'plot_csv=bin.plot_csv:plot_csv',
          #         ],
          #     'gui_scripts': [
          #         'baz = my_package_gui:start_func',
          #         ]
          #     }
          )
