from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='fiaclient',
    version='1.1.10',
    description='A simple client for FIA API (https://github.com/spacepatcher/FireHOL-IP-Aggregator)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/spacepatcher/FireHOL-IP-Aggregator',
    author='spacepatcher',
    author_email='mycardinalmail@gmail.com',
    license='MIT',
    classifiers=[],
    keywords='client threat_intelligence FireHOL-IP-Aggregator reputation',
    project_urls={
        'Documentation': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/blob/develop/fiaclient/README.md',
        'Source': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/tree/develop/fiaclient',
        'Tracker': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/issues',
    },
    packages=find_packages(),
    install_requires=['requests'],
    python_requires='>=3',
)
