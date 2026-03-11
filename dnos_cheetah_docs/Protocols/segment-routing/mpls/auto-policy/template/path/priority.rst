protocols segment-routing mpls auto-policy template color path priority
-----------------------------------------------------------------------

**Minimum user role:** operator

To configure a path priority:

**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color path

**Parameter table**

+-----------+----------------------------+-------+---------+
| Parameter | Description                | Range | Default |
+===========+============================+=======+=========+
| priority  | SR-TE policy path priority | 1-255 | \-      |
+-----------+----------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# path PATH_1
    dnRouter(cfg-auto-policy-color-3-path)# priority 5
    dnRouter(cfg-auto-policy-color-3-path)#


**Removing Configuration**

To remove a priority:
::

    dnRouter(cfg-auto-policy-color-3-path)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
