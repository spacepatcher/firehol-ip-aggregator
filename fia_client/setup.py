from setuptools import setup
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='fia-client',
    version='1.1.1.dev',
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
        'Documentation': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/blob/develop/fia_client/README.md',
        'Source': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/tree/develop/fia_client',
        'Tracker': 'https://github.com/spacepatcher/FireHOL-IP-Aggregator/issues',
    },
    install_requires=['requests'],
    python_requires='>=3',
)
