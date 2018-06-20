README
======

Python Jenkins is a python wrapper for the `Jenkins <http://jenkins-ci.org/>`_
REST API which aims to provide a more conventionally pythonic way of controlling
a Jenkins server.  It provides a higher-level API containing a number of
convenience functions.

We like to use python-jenkins to automate our Jenkins servers. Here are some of
the things you can use it for:

* Create new jobs
* Copy existing jobs
* Delete jobs
* Update jobs
* Get a job's build information
* Get Jenkins master version information
* Get Jenkins plugin information
* Start a build on a job
* Create nodes
* Enable/Disable nodes
* Get information on nodes
* Create/delete/reconfig views
* Put server in shutdown mode (quiet down)
* List running builds
* Delete builds
* Wipeout job workspace
* Create/delete/update folders [#f1]_
* Set the next build number [#f2]_
* Install plugins
* and many more..

To install::

    $ sudo python setup.py install

Online documentation:

* http://python-jenkins.readthedocs.org/en/latest/

Developers
----------
Bug report:

* https://bugs.launchpad.net/python-jenkins

Repository:

* https://git.openstack.org/cgit/openstack/python-jenkins

Cloning:

* git clone https://git.openstack.org/openstack/python-jenkins

Patches are submitted via Gerrit at:

* https://review.openstack.org/

Please do not submit GitHub pull requests, they will be automatically closed.

The python-jenkins developers communicate in the ``#openstack-jjb`` channel
on Freenode's IRC network.

More details on how you can contribute is available on our wiki at:

* http://docs.openstack.org/infra/manual/developers.html

Writing a patch
---------------

Be sure that you lint code before created an code review.
The easiest way to do this is to install git pre-commit_ hooks.

Installing without setup.py
---------------------------

Then install the required python packages using pip_::

    $ sudo pip install python-jenkins

.. _tox: https://testrun.org/tox
.. _pip: https://pypi.org/project/pip
.. _pre-commit: https://pre-commit.com/#install


.. rubric:: Footnotes

.. [#f1] The free `Cloudbees Folders Plugin
    <https://wiki.jenkins-ci.org/display/JENKINS/CloudBees+Folders+Plugin>`_
    provides support for a subset of the full folders functionality. For the
    complete capabilities you will need the paid for version of the plugin.

.. [#f2] The `Next Build Number Plugin
   <https://wiki.jenkins-ci.org/display/JENKINS/Next+Build+Number+Plugin>`_
   provides support for setting the next build number.
