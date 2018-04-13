from setuptools import setup
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fia-client',
    version='0.0.1',
    description='A simple client for FIA API (https://github.com/spacepatcher/FireHOL-IP-Aggregator)',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/spacepatcher/FireHOL-IP-Aggregator',
    author='spacepatcher',
    author_email='mycardinalmail@gmail.com',
    license='MIT',
    classifiers=[],
    keywords='client threat_intelligence FireHOL-IP-Aggregator',
    project_urls={
        'Documentation': '',
        'Source': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator',
        'Tracker': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/issues',
    },
    install_requires=['argparse', 'requests'],
    python_requires='>=3',
)
