Example usage
=============

Example usage::

    import jenkins
    j = jenkins.Jenkins('http://your_url_here', 'username', 'password')
    j.get_jobs()
    j.create_job('empty', jenkins.EMPTY_CONFIG_XML)
    j.disable_job('empty')
    j.copy_job('empty', 'empty_copy')
    j.enable_job('empty_copy')
    j.reconfig_job('empty_copy', jenkins.RECONFIG_XML)

    j.delete_job('empty')
    j.delete_job('empty_copy')

    j.get_views()
    j.create_view('EMPTY', jenkins.EMPTY_VIEW_CONFIG_XML)
    j.view_exists('EMPTY')
    j.delete_view('EMPTY') 

    # build a parameterized job
    # requires setting up api-test job to accept 'param1' & 'param2'
    j.build_job('api-test', {'param1': 'test value 1', 'param2': 'test value 2'})
    last_build_number = j.get_job_info('api-test')['lastCompletedBuild']['number']
    build_info = j.get_job_info('api-test', last_build_number)
    print(build_info)

Look at the :doc:`api` for more details.
