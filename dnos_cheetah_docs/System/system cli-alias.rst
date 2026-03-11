system cli-alias
----------------

**Minimum user role:** operator

Entering the same commands repeatedly is sometimes a redundant task. The DNOS CLI allows you to define command shortcuts that can be used for the most common commands. You can configure up to 1024 aliases.

After setting up the various shortcuts, you can integrate them in the CLI.

To configure aliases for commands:

**Command syntax: cli-alias [cli-alias] [cli-alias-command]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- When introducing alias keys with two or more words separated by a space, only the first word will be saved.

- When upgrading to version 17.2, any alias key with two or more words separated by a space, will be deleted.

- when executing the alias it will be replaced with the configured value (including all spaces)

- alias value maximum length of 255 chars, alias name max length of 255 chars

- up to 1024 configurable aliases shall be supported

- alias will be supported at under any CLI level (main, config, interfaces, protocols, system, etc.)

- There will no validation for the value of the alias, thus is it can contain an unknown command, running the alias will return the relevant error

System will prevent recursive aliasing, for example, the following configuration will fail:

- cli-alias a b

- cli-alias b a

aliases work in exact match - when executing it, the CLI process will look for the exact alias.

- aliases are case sensitive

- security - user using the alias will not be able to run commands not in the permission level (the checks will be done on the alias value)

- alias will support concatenation of one alias to another aliases or to regular CLI commands

- no command without alias-key removes all alias configuration.

- no command with specific alias-key removes specific alias configuration.

Not supported:

- auto complete (tab) of alias commands

- present optional completion when using ?

- short commands for alias-value like "sh bg sum"

- single alias running two commands (separated with ; )

**Parameter table**

+-------------------+---------------------------------------------------+------------------+---------+
| Parameter         | Description                                       | Range            | Default |
+===================+===================================================+==================+=========+
| cli-alias         | Configured name of the cli alias command          | | string         | \-      |
|                   |                                                   | | length 1-255   |         |
+-------------------+---------------------------------------------------+------------------+---------+
| cli-alias-command | Configured command line (string) of the cli alias | | string         | \-      |
|                   |                                                   | | length 1-255   |         |
+-------------------+---------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cli-alias sbs "show bgp summary"
    dnRouter(cfg-system)# cli-alias sr0 "show route 0.0.0.0"
    dnRouter(cfg-system)# cli-alias sint "show interfaces"
    dnRouter(cfg-system)# cli-alias incbun "| include bundle"
    dnRouter(cfg-system)# cli-alias confip "interfaces lo0 ipv4-address 1.2.3.4/32"

    dnRouter# sbs
    dnRouter# sint incbun
    dnRouter# show interfaces counters incbun
    dnRouter(cfg)# confip


**Removing Configuration**

To delete cli-alias configuration:
::

    dnRouter(cfg-system)# no cli-alias

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 13.1    | Command introduced                     |
+---------+----------------------------------------+
| 17.2    | Added note about spaces in alias names |
+---------+----------------------------------------+
