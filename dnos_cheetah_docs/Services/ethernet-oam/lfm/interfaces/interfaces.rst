services ethernet-oam link-fault-management interface
-----------------------------------------------------

**Minimum user role:** operator

To configure the 802.3ah EFM OAM protocol on a specific interface:

**Command syntax: interface [interface]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management

**Note**

- support only physical interfaces <geX-X/X/X>

**Parameter table**

+-----------+--------------------------------------------------+------------------+---------+
| Parameter | Description                                      | Range            | Default |
+===========+==================================================+==================+=========+
| interface | 802.3ah EFM OAM protocol on a specific interface | | string         | \-      |
|           |                                                  | | length 1-255   |         |
+-----------+--------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-eoam-lfm)# interface ge100-0/0/0
    dnRouter(cfg-eoam-lfm-if)#


**Removing Configuration**

To remove 802.3ah EFM OAM configuration from a specific interface:
::

    dnRouter(cfg-eoam-lfm)# no interface ge100-0/0/0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
