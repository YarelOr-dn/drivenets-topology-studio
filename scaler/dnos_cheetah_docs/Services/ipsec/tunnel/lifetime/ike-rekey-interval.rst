services ipsec tunnel vrf lifetime ike-rekey-interval
-----------------------------------------------------

**Minimum user role:** operator

Set the ike-rekey-interval in seconds for the configured tunnel. when rekey-interval=0, no rekey will be performed

**Command syntax: ike-rekey-interval [ike-rekey-interval]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf lifetime

**Parameter table**

+--------------------+-----------------------------------------------------------------------+-------------------+---------+
| Parameter          | Description                                                           | Range             | Default |
+====================+=======================================================================+===================+=========+
| ike-rekey-interval | Time in seconds between each IKE SA rekey.The value 0 means infinite. | 0, 300-4294967295 | \-      |
+--------------------+-----------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# lifetime
    dnRouter(cfg-srv-ipsec-tun-life)# ike-rekey-interval 14400


**Removing Configuration**

To remove the configuration of the ike-rekey-interval:
::

    dnRouter(cfg-srv-ipsec-tun-life)# no ike-rekey-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
