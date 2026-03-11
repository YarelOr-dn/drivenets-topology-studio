protocols segment-routing mpls policy path
------------------------------------------

**Minimum user role:** operator

Configure path


**Command syntax: path [path]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-----------+---------------------------+------------------+---------+
| Parameter | Description               | Range            | Default |
+===========+===========================+==================+=========+
| path      | segment-routing path name | | string         | \-      |
|           |                           | | length 1-255   |         |
+-----------+---------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# path PATH_1
    dnRouter(cfg-mpls-policy-path)#


**Removing Configuration**

To remove the path setting:
::

    dnRouter(cfg-sr-mpls-policy)# no path PATH_1

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 17.0    | Command introduced            |
+---------+-------------------------------+
| 18.3    | Moved priority to new command |
+---------+-------------------------------+
