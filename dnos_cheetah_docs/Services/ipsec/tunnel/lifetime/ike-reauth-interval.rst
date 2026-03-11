services ipsec tunnel vrf lifetime ike-reauth-interval
------------------------------------------------------

**Minimum user role:** operator

Set the ike-reauth-interval in seconds for the configured tunnel. when reauth-interval=0, no reauth will be performed

**Command syntax: ike-reauth-interval [ike-reauth-interval]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf lifetime

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+-------------------+---------+
| Parameter           | Description                                                                      | Range             | Default |
+=====================+==================================================================================+===================+=========+
| ike-reauth-interval | Time in seconds between each IKE SA reauthentication. The value 0 means          | 0, 300-4294967295 | \-      |
|                     | infinite.                                                                        |                   |         |
+---------------------+----------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# lifetime
    dnRouter(cfg-srv-ipsec-tun-life)# ike-reauth-interval 14400


**Removing Configuration**

To remove the configuration of the ike-reauth-interval:
::

    dnRouter(cfg-srv-ipsec-tun-life)# no ike-reauth-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
