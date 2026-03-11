services ethernet-oam link-fault-management profile pdu-interval
----------------------------------------------------------------

**Minimum user role:** operator

To set the 802.3ah EFM OAM protocol's hello interval time:

**Command syntax: pdu-interval [pdu-interval]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management profile

**Note**

- The valid range is 100-1000ms in skips of 100ms.

**Parameter table**

+--------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter    | Description                                                                      | Range    | Default |
+==============+==================================================================================+==========+=========+
| pdu-interval | Specifies the periodic OAMPDU sending interval in milliseconds. The interval     | 100-1000 | 1000    |
|              | should be specified in skips of 100 milliseconds.                                |          |         |
+--------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# pdu-interval 400


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-eoam-lfm-profile)# no pdu-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
