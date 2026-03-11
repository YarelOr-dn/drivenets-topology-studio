services mpls-oam profile size
------------------------------

**Minimum user role:** operator

To set the packet size using the Pad TLV to pad the echo messages

**Command syntax: size [size]**

**Command mode:** config

**Hierarchies**

- services mpls-oam profile

**Parameter table**

+-----------+-------------------------------+----------+---------+
| Parameter | Description                   | Range    | Default |
+===========+===============================+==========+=========+
| size      | mpls echo request packet size | 100-9300 | \-      |
+-----------+-------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# size 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-mpls-oam-profile)# no size

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
