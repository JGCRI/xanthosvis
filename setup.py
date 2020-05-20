"""Setup file for xanthosvis

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()


setup(
    name='xanthosvis',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/crvernon/xanthosvis.git',
    license='BSD 2-Clause',
    author='Jason Evanoff; Chris R. Vernon',
    author_email='jason.evanoff@pnnl.gov; chris.vernon@pnnl.gov',
    description='An interactive dashboard for visualizing Xanthos data',
    python_requires='>=3.3.*, <4'
)
