Contributing
============

If you would like to contribute to the development of OpenStack,
you must follow the steps in this page:

   http://docs.openstack.org/infra/manual/developers.html

If you already have a good understanding of how the system works and your
OpenStack accounts are set up, you can skip to the development workflow section
of this documentation to learn how changes to OpenStack should be submitted for
review via the Gerrit tool:

   http://docs.openstack.org/infra/manual/developers.html#development-workflow

Pull requests submitted through GitHub will be ignored.

Bugs should be filed on StoryBoard, not GitHub:

   https://storyboard.openstack.org/#!/project/718

To browse the latest code:

   https://git.openstack.org/cgit/openstack-infra/gerritlib/tree/

To clone the latest code:

   git clone git://git.openstack.org/openstack-infra/gerritlib

Code reviews are handled by gerrit:
   http://review.openstack.org

Use `git review` to submit patches (after creating a gerrit
account that links to your launchpad account). Example::

    # Do your commits
    $ git review
    # Enter your username if prompted
