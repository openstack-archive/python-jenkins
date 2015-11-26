This plugin allows to monitor the Gerrit server.

This plugin integrates [JavaMelody](https://code.google.com/p/javamelody) in
Gerrit in order to retrieve live instrumentation data from Gerrit.

To access the monitoring URL a user must be a member of a group that is
granted the 'Javamelody Monitoring' capability (provided by this plugin)
or the 'Administrate Server' capability.

It adds top menu item "Monitoring" to access java melody page.
