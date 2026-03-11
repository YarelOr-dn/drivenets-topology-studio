qos deep-buffering
------------------

**Minimum user role:** operator

To configure deep-buffering:

**Command syntax: deep-buffering [deep-buffering]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+----------------+----------------------------------+----------------+---------+
| Parameter      | Description                      | Range          | Default |
+================+==================================+================+=========+
| deep-buffering | Control deep buffering behavior. | | normal       | normal  |
|                |                                  | | hbm-bypass   |         |
+----------------+----------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# deep-buffering normal


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-qos)# no deep-buffering

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
