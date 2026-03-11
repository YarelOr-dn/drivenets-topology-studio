services ipsec tunnel vrf lifetime rekey-margin
-----------------------------------------------

**Minimum user role:** operator

the period of time before key/auth expires which the system initiates rekey/reauth.

**Command syntax: rekey-margin [rekey-margin]**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf lifetime

**Parameter table**

+--------------+-------------------------------------------------------------------------------+-------------------+---------+
| Parameter    | Description                                                                   | Range             | Default |
+==============+===============================================================================+===================+=========+
| rekey-margin | the period of time before key/auth expires which stronglahav initiates rekey. | 0, 300-4294967295 | \-      |
+--------------+-------------------------------------------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# lifetime
    dnRouter(cfg-srv-ipsec-tun-life)# rekey-margin 540


**Removing Configuration**

To remove the configuration of the rekey-margin:
::

    dnRouter(cfg-srv-ipsec-tun-life)# no rekey-margin

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
