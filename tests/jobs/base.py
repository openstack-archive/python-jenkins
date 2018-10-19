from tests.base import JenkinsTestBase


class JenkinsJobsTestBase(JenkinsTestBase):

    config_xml = """
        <matrix-project>
            <actions/>
            <description>Foo</description>
        </matrix-project>"""


class JenkinsGetJobsTestBase(JenkinsJobsTestBase):

    jobs_in_folder = [
        {'jobs': [
            {'name': 'my_job1', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_folder1', 'url': 'http://...', 'jobs': [{}, {}]},
            {'name': 'my_job2', 'color': 'blue', 'url': 'http://...'}
        ]},
        # my_folder1 jobs
        {'jobs': [
            {'name': 'my_job3', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_job4', 'color': 'blue', 'url': 'http://...'}
        ]}
    ]

    jobs_in_multiple_folders = [
        {'jobs': [
            {'name': 'my_job1', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_folder1', 'url': 'http://...', 'jobs': [{}, {}, {}]},
            {'name': 'my_job2', 'color': 'blue', 'url': 'http://...'}
        ]},
        # my_folder1 jobs
        {'jobs': [
            {'name': 'my_folder2', 'url': 'http://...', 'jobs': [{}, {}]},
            {'name': 'my_job3', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_job4', 'color': 'blue', 'url': 'http://...'}
        ]},
        # my_folder1/my_folder2 jobs
        {'jobs': [
            {'name': 'my_job1', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_job2', 'color': 'blue', 'url': 'http://...'}
        ]}
    ]

    jobs_in_unsafe_name_folders = [
        {'jobs': [
            {'name': 'my_job1', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_folder1', 'url': 'http://...', 'jobs': [{}, {}]},
            {'name': 'my_job2', 'color': 'blue', 'url': 'http://...'}
        ]},
        # my_folder1 jobs
        {'jobs': [
            {'name': 'my spaced folder', 'url': 'http://...', 'jobs': [{}]},
            {'name': 'my_job3', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_job4', 'color': 'blue', 'url': 'http://...'}
        ]},
        # my_folder1/my\ spaced\ folder jobs
        {'jobs': [
            {'name': 'my job 5', 'color': 'blue', 'url': 'http://...'}
        ]}
    ]

    jobs_in_folder_named_job = [
        # actually a folder :-)
        {'jobs': [
            {'name': 'job', 'url': 'http://...', 'jobs': [{}]}
        ]},
        # "job" folder jobs
        {'jobs': [
            {'name': 'my_job', 'color': 'blue', 'url': 'http://...'}
        ]}
    ]

    jobs_in_folder_deep_query = [
        {'jobs': [
            {'name': 'top_folder', 'url': 'http://...', 'jobs': [
                {'name': 'middle_folder', 'url': 'http://...', 'jobs': [
                    {'name': 'bottom_folder', 'url': 'http://...',
                     'jobs': [{}, {}]}
                ]}
            ]}
        ]},
        # top_folder/middle_folder/bottom_folder jobs
        {'jobs': [
            {'name': 'my_job1', 'color': 'blue', 'url': 'http://...'},
            {'name': 'my_job2', 'color': 'blue', 'url': 'http://...'}
        ]}
    ]
