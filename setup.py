try:
    from setuptools import setup, find_packages
    from imp import find_module, load_module
except ImportError:
    from distutils.core import setup


URL = "https://gitlab.com/seek-and-deploy/terraform-deployer"
doclink = "Please visit {}.".format(URL)

found = find_module('_version', ['deployer'])
_version = load_module('_version', *found)

setup(
    name='deployer',
    version=_version.__version__,
    description='Deployer',
    long_description=doclink,
    author='Paul Lussier',
    author_email='pllsaph+gitlab@gmail.com',
    url=URL,
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
        'termcolor',
        'workdir',
    ],
    license="VERACODE",
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
