Example usage
=============

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

Look at the :doc:`api` for more details.
