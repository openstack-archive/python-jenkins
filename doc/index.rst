Welcome to Python Jenkins's documentation!
==========================================

Python Jenkins is a library for the remote API of the `Jenkins
<http://jenkins-ci.org/>`_ continuous integration server. It is useful
for creating and managing jobs as well as build nodes.

Example usage::

    j = jenkins.Jenkins('http://your_url_here', 'username', 'password')
    j.get_jobs()
    j.create_job('empty', jenkins.EMPTY_CONFIG_XML)
    j.disable_job('empty')
    j.copy_job('empty', 'empty_copy')
    j.enable_job('empty_copy')
    j.reconfig_job('empty_copy', jenkins.RECONFIG_XML)

    j.delete_job('empty')
    j.delete_job('empty_copy')

    # build a parameterized job
    j.build_job('api-test', {'param1': 'test value 1', 'param2': 'test value 2'})
    build_info = j.get_build_info('build_name', next_build_number)
    print(build_info)

Python Jenkins development is hosted on Launchpad: https://launchpad.net/python-jenkins

Installing
==========

``pip``::

    pip install python-jenkins
    
``easy_install``::

    easy_install python-jenkins

Ubuntu Oneiric or later::

    apt-get install python-jenkins


API documentation
=================

.. class:: JenkinsException

    General exception type for jenkins-API-related failures.

.. class:: Jenkins(url, [username=None, [password=None]])
    
    Create handle to Jenkins instance.

    All methods will raise :class:`JenkinsException` on failure.

    :param username: Server username, ``str``
    :param password: Server password, ``str``
    :param url: URL of Jenkins server, ``str``


    .. method:: get_jobs(self)

        Get list of jobs running.  Each job is a dictionary with
        'name', 'url', and 'color' keys.

        :returns: list of jobs, ``[ { str: str} ]``

    .. method:: job_exists(name)

        :param name: Name of Jenkins job, ``str``
        :returns: ``True`` if Jenkins job exists

    .. method:: build_job(name, [parameters=None, [token=None]])

        Trigger build job.
        
        :param parameters: parameters for job, or ``None``, ``dict``
  
    .. method:: build_job_url(name, [parameters=None, [token=None]])

        Get URL to trigger build job.  Authenticated setups may require configuring a token on the server side.
        
        :param parameters: parameters for job, or None., ``dict``
        :param token: (optional) token for building job, ``str``
        :returns: URL for building job

    .. method:: create_job(name, config_xml)

        Create a new Jenkins job

        :param name: Name of Jenkins job, ``str``
        :param config_xml: config file text, ``str``
    
    .. method:: copy_job(from_name, to_name)

        Copy a Jenkins job

        :param from_name: Name of Jenkins job to copy from, ``str``
        :param to_name: Name of Jenkins job to copy to, ``str``

    .. method:: rename_job(name, new_name)

        Rename an existing Jenkins job

        :param name: Name of Jenkins job to rename, ``str``
        :param new_name: New Jenkins job name, ``str``

    .. method:: delete_job(name)

        Delete Jenkins job permanently.
        
        :param name: Name of Jenkins job, ``str``
    
    .. method:: enable_job(name)

        Enable Jenkins job.

        :param name: Name of Jenkins job, ``str``

    .. method:: disable_job(name)

        Disable Jenkins job. To re-enable, call :meth:`Jenkins.enable_job`.

        :param name: Name of Jenkins job, ``str``

    .. method:: get_build_info(name, number)

        Get build information dictionary.

        :param name: Job name, ``str``
        :param name: Build number, ``int``
        :returns: dictionary of build information

    .. method:: get_job_config(name) -> str

        Get configuration XML of existing Jenkins job.  

        :param name: Name of Jenkins job, ``str``
        :returns: Job configuration XML

    .. method:: get_job_info(name)

        Get job information dictionary.

        :param name: Job name, ``str``
        :returns: dictionary of job information

    .. method:: debug_job_info(job_name)

        Print out job info in more readable format

    .. method:: reconfig_job(name, config_xml)

        Change configuration of existing Jenkins job.  To create a new job, see :meth:`Jenkins.create_job`.

        :param name: Name of Jenkins job, ``str``
        :param config_xml: New XML configuration, ``str``

    .. method:: get_node_info(name) -> dict

        Get node information dictionary

        :param name: Node name, ``str``
        :returns: Dictionary of node info, ``dict``
 
    .. method:: node_exists(name) -> bool

        :param name: Name of Jenkins node, ``str``
        :returns: ``True`` if Jenkins node exists
            
    .. method:: create_node(name, [numExecutors=2, [nodeDescription=None, [remoteFS='/var/lib/jenkins', [labels=None, [exclusive=False]]]]])

        :param name: name of node to create, ``str``
        :param numExecutors: number of executors for node, ``int``
        :param nodeDescription: Description of node, ``str``
        :param remoteFS: Remote filesystem location to use, ``str``
        :param labels: Labels to associate with node, ``str``
        :param exclusive: Use this node for tied jobs only, ``bool``

    .. method:: delete_node(name)

        Delete Jenkins node permanently.
        
        :param name: Name of Jenkins node, ``str``
    
    .. method:: get_queue_info(self)

        :returns: list of job dictionaries, ``[dict]``

        Example::

            >>> queue_info = j.get_queue_info()
            >>> print(queue_info[0])
            {u'task': {u'url': u'http://your_url/job/my_job/', u'color': u'aborted_anime', u'name': u'my_job'}, u'stuck': False, u'actions': [{u'causes': [{u'shortDescription': u'Started by timer'}]}], u'buildable': False, u'params': u'', u'buildableStartMilliseconds': 1315087293316, u'why': u'Build #2,532 is already in progress (ETA:10 min)', u'blocked': True}

    .. method:: get_info(self)

        Get information on this Master.  This information
        includes job list and view information.

        :returns: dictionary of information about Master, ``dict``

        Example::

            >>> info = j.get_info()
            >>> jobs = info['jobs']
            >>> print(jobs[0])
            {u'url': u'http://your_url_here/job/my_job/', u'color': u'blue', u'name': u'my_job'}


    .. method:: jenkins_open(req)

        Utility routine for opening an HTTP request to a Jenkins server.   This should only be used
        to extends the :class:`Jenkins` API.
    

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

