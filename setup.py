from setuptools import setup
import os

PROJECT_ROOT, _ = os.path.split(__file__)
PROJECT_AUTHORS = 'Ken Conley'
PROJECT_EMAILS= ['kwc@willowgarage.com']
REVISION = '0.4.13'
PROJECT_NAME = 'python-jenkins'
PROJECT_URL='https://github.com/openstack/python-jenkins'
SHORT_DESCRIPTION = (
  'Python Jenkins is a python wrapper for the Jenkins REST API which aims to provide a more conventionally pythonic way of '
  'controlling a Jenkins server. It provides a higher-level API containing a number of convenience functions.'
)

try:
    DESCRIPTION = open(os.path.join(PROJECT_ROOT, 'README.rst')).read()
except IOError:
    DESCRIPTION = SHORT_DESCRIPTION


setup(
    name=PROJECT_NAME.lower(),
    version=REVISION,
    author=PROJECT_AUTHORS,
    author_email=PROJECT_EMAILS,
    packages=[
        'jenkins'],
    zip_safe=True,
    include_package_data=False,
    install_requires = [line.strip()
                 for line in open('requirements.txt')
                 if line.strip()],
    url=PROJECT_URL,
    description=SHORT_DESCRIPTION,
    long_description=DESCRIPTION,
    license='BSD',
    classifiers=[
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)
