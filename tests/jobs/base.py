from tests.base import JenkinsTestBase


class JenkinsJobsTestBase(JenkinsTestBase):

    config_xml = """
        <matrix-project>
            <actions/>
            <description>Foo</description>
        </matrix-project>"""
