try:
    from setuptools import setup, find_packages
    from imp import find_module, load_module
except ImportError:
    from distutils.core import setup


VC_URL = "https://stash.veracode.local/projects/VC"
doclink = "Please visit {}.".format(VC_URL)

found = find_module('_version', ['deployer'])
_version = load_module('_version', *found)

setup(
    name='deployer',
    version=_version.__version__,
    description='Deployer',
    long_description=doclink,
    author='Paul Lussier, Pat Day',
    author_email='plussier@veracode.com, pday@veracode.com',
    url=VC_URL,
    packages=find_packages(),
    scripts=['bin/deployer', 'bin/gen_config', 'bin/configure-aws.sh'],
    package_dir={'deployer': 'deployer'},
    package_data={'deployer': ['conf/logging.conf']},
    include_package_data=True,
    install_requires=[
        'argparse',
        'botocore',
        'boto3',
        'docopt',
        'flake8',
        'jinja2',
        'jsonschema',
        'termcolor==1.1.0',
        'workdir',
    ],
    license="VERACODE",
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
