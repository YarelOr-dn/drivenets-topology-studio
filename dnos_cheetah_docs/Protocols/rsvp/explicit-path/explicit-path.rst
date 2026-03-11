protocols rsvp explicit-path
----------------------------

**Minimum user role:** operator

Explicit paths limit LSP routing to a specified list of LSRs. By default, RSVP messages follow a path that is dynamically determined by the network IGP's shortest path (i.e. by IS-IS), unless an explicit path is configured.
To create an explicit path:

**Command syntax: explicit-path [explicit-path]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
.. - no commands remove the explicit-path

- You cannot remove an explicit path that is in use by a tunnel.

**Parameter table**

+---------------+--------------------+------------------+---------+
| Parameter     | Description        | Range            | Default |
+===============+====================+==================+=========+
| explicit-path | explicit path name | | string         | \-      |
|               |                    | | length 1-255   |         |
+---------------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# explicit-path PATH_1
    dnRouter(cfg-protocols-rsvp-expl-path)#


**Removing Configuration**

To remove an explicit path:
::

    dnRouter(cfg-protocols-rsvp)# no explicit-path PATH_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
