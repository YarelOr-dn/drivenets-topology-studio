routing-options bmp server
--------------------------

**Minimum user role:** operator

To configure a BMP server to which the bgp monitoring information will be sent.

**Command syntax: bmp server [server-id]**

**Command mode:** config

**Hierarchies**

- routing-options

**Note**

- Up to 5 bmp servers can be configured per neighbor.

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| server-id | bmp server local id | 1-5   | \-      |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-routing-option)# no bmp server 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
