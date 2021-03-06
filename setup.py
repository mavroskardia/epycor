'setuptools setup script for epycor'

# import sys
# import os
# import glob
from setuptools import setup, find_packages

# ALL_FILES = [f for f in glob.glob('app/*/**', recursive=True) if not os.path.isdir(f)]

setup(
    name='epycor',
    version='0.0.2',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'epycor = epycor.epycor:run_epycor'
        ]
    },
    install_requires=[
        'appdirs==1.4.3',
        'asn1crypto==0.22.0',
        'astroid==1.5.3',
        'cached-property==1.3.0',
        'cefpython3==57.0',
        'certifi==2017.4.17',
        'cffi==1.10.0',
        'chardet==3.0.4',
        'cryptography==1.9',
        'dbus-python==1.2.4;platform_system=="Linux"',
        'defusedxml==0.5.0',
        'idna==2.5',
        'isodate==0.5.4',
        'isort==4.2.15',
        'keyring==10.3.3',
        'lazy-object-proxy==1.3.1',
        'lxml==3.8.0',
        'mccabe==0.6.1',
        'ntlm-auth==1.0.4',
        'ordereddict==1.1',
        'pycparser==2.17',
        'pylint==1.7.2',
        'python-dateutil==2.6.0',
        'pytz==2017.2',
        'requests==2.18.1',
        'requests-ntlm==1.0.0',
        'requests-toolbelt==0.8.0',
        'SecretStorage==2.3.1;platform_system=="Linux"',
        'six==1.10.0',
        'urllib3==1.21.1',
        'wrapt==1.10.10',
        'zeep==2.1.1',
    ]
)
