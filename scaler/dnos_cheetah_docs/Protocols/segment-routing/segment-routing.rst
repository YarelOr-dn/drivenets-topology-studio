protocols segment-routing
-------------------------

**Minimum user role:** operator

To enter the segment-routing configuration hierarchy:

**Command syntax: segment-routing**

**Command mode:** config

**Hierarchies**

- protocols

**Note**
- no command remove all segment-routing configurations

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)#


**Removing Configuration**

To remove the segment-routing configuration:
::

    dnRouter(cfg-protocols)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
