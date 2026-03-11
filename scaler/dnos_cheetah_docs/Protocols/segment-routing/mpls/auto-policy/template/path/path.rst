protocols segment-routing mpls auto-policy template color path
--------------------------------------------------------------

**Minimum user role:** operator

To configure a path:

**Command syntax: path [path]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

**Note**
- A path is not a mandatory configuration for auto-policies. If no paths are configured, then algo0 SPF algorithm will be used to resolve the destination.

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# path PATH_1
    dnRouter(cfg-auto-policy-color-3-path)#


**Removing Configuration**

To remove a path:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no path PATH_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
