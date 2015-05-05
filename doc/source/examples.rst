Using Python-Jenkins API
========================

The APIs allows management of a Jenkins server thru the Jenkins REST endpoints.
These are examples to just get you started using the APIs.  If you need further
help take a look at the :doc:`api` docs for more details.


Example 1: Get version of Jenkins
---------------------------------
::

    import jenkins

    server = jenkins.Jenkins('localhost:8080', username='myuser', password='mypassword')
    version = server.get_version()
    print version

The above code prints the version of the Jenkins master running on 'localhost:8080'

From Jenkins vesion 1.426 onward one can specify an API token instead of your
real password while authenticating the user against Jenkins instance. Refer to
the the Jenkis Authentication_ wiki page for details about how a user can
generate an API token. Once you have an API token you can pass the API token
instead of real password while creating an Jenkins server instance using Jenkins
API.

.. _Authentication: https://wiki.jenkins-ci.org/display/JENKINS/Authenticating+scripted+clients


Example 2: Working with Jenkins Jobs
------------------------------------
::

    server.create_job('empty', jenkins.EMPTY_CONFIG_XML)
    jobs = server.get_jobs()
    print jobs
    server.build_job('empty')
    server.disable_job('empty')
    server.copy_job('empty', 'empty_copy')
    server.enable_job('empty_copy')
    server.reconfig_job('empty_copy', jenkins.RECONFIG_XML)

    server.delete_job('empty')
    server.delete_job('empty_copy')

    # build a parameterized job
    # requires creating and configuring the api-test job to accept 'param1' & 'param2'
    server.build_job('api-test', {'param1': 'test value 1', 'param2': 'test value 2'})
    last_build_number = server.get_job_info('api-test')['lastCompletedBuild']['number']
    build_info = server.get_job_info('api-test', last_build_number)
    print build_info


Example 3: Working with Jenkins Views
-------------------------------------

::

    server.create_view('EMPTY', jenkins.EMPTY_VIEW_CONFIG_XML)
    view_config = server.get_view_config('EMPTY')
    views = server.get_views()
    server.delete_view('EMPTY')
    print views


Example 4: Working with Jenkins Folder
--------------------------------------

::

    # create empty folder
    server.create_job('folder', jenkins.EMPTY_FOLDER_XML)

    # create subfolder
    server.create_job('folder/empty', jenkins.EMPTY_FOLDER_XML)

    # copy folder to new name
    server.copy_job('folder/empty', 'folder/empty_copy')

    # delete folder
    server.delete_job('folder/empty_copy')
    server.delete_job('folder')


Example 5: Working with Jenkins Plugins
---------------------------------------

::

    plugins = server.get_plugins_info()
    print plugins


Example 6: Working with Jenkins Nodes
-------------------------------------

::

    server.create_node('slave1')
    nodes = get_nodes()
    print nodes
    node_config = server.get_node_info('slave1')
    print node_config
    server.disable_node('slave1')
    server.enable_node('slave1')


Example 7: Working with Jenkins Build Queue
-------------------------------------------

::

    server.build_job('foo')
    queue_info = server.get_queue_info()
    id = queue_info[0].get('id')
    server.cancel_queue(id)


Example 8: Working with Jenkins Cloudbees Folders
-------------------------------------------------

::

    j.create_job('folder', jenkins.EMPTY_FOLDER_XML)
    j.create_job('folder/empty', jenkins.EMPTY_FOLDER_XML)
    j.copy_job('folder/empty', 'folder/empty_copy')
    j.delete_job('folder/empty_copy')
    j.delete_job('folder')
