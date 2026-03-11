services ipsec tunnel vrf lifetime ipsec-rekey-interval
-------------------------------------------------------

**Minimum user role:** operator

Set the ipsec-rekey-interval in seconds for the configured tunnel. when rekey-interval=0, no rekey will be performed

**Command syntax: ipsec-rekey-interval [ipsec-rekey-interval]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf lifetime

**Parameter table**

+----------------------+-------------------------------------------------------------------------+-------------------+---------+
| Parameter            | Description                                                             | Range             | Default |
+======================+=========================================================================+===================+=========+
| ipsec-rekey-interval | Time in seconds between each IPsec SA rekey.The value 0 means infinite. | 0, 300-4294967295 | \-      |
+----------------------+-------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# lifetime
    dnRouter(cfg-srv-ipsec-tun-life)# ipsec-rekey-interval 3600


**Removing Configuration**

To remove the configuration of the ipsec-rekey-interval:
::

    dnRouter(cfg-srv-ipsec-tun-life)# no ipsec-rekey-interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
