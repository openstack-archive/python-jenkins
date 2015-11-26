Build
=====

This plugin is built with Buck.

Two build modes are supported: Standalone and in Gerrit tree. Standalone
build mode is recommended, as this mode doesn't require local Gerrit
tree to exist.

Build standalone
----------------

Clone bucklets library:

```
  git clone https://gerrit.googlesource.com/bucklets

```
and link to bucklets directory:

```
  cd javamelody && ln -s ../bucklets .
```

Add link to the .buckversion file:

```
  cd javamelody && ln -s bucklets/buckversion .buckversion
```

Add link to the .watchmanconfig file:

```
  cd javamelody && ln -s bucklets/watchmanconfig .watchmanconfig
```

To build the plugin, issue the following commands:

```
  buck build all
```

The output of the target is:

```
  buck-out/gen/javamelody.jar
```

If [database interception](database-monitoring.html) should be activated,
then the following artifacts must be used instead:

```
  buck-out/gen/javamelody-nodep.jar
  buck-out/gen/javamelody-deps.jar
  buck-out/gen/javamelody-datasource-interceptor.jar
```

Build in Gerrit tree
--------------------

Clone or link this plugin to the plugins directory of the Gerrit tree
and issue the command:

```
  buck build plugins/javamelody:javamelody
```

If [database interception](database-monitoring.html) should be activated,
then the following targets must be used instead:

```
  buck build plugins/javamelody:javamelody-nodep
  buck build plugins/javamelody:javamelody-deps
  buck build plugins/javamelody:javamelody-datasource-interceptor
```

The output from the former target is:

```
  buck-out/gen/plugins/javamelody/javamelody.jar
```

The output from the latter targets are:

```
  buck-out/gen/plugins/javamelody/javamelody-nodep.jar
  buck-out/gen/plugins/javamelody/javamelody-deps.jar
  buck-out/gen/plugins/javamelody/javamelody-datasource-interceptor.jar
```

This project can be imported into the Eclipse IDE:

```
  ./tools/eclipse/project.py
```

More information about Buck can be found in the [Gerrit
documentation](../../../Documentation/dev-buck.html).
