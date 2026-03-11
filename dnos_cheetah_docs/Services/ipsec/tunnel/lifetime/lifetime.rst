services ipsec tunnel vrf lifetime
----------------------------------

**Minimum user role:** operator

DNOS supports IPSec tunnels configurable lifetime parameters.

**Command syntax: lifetime**

**Command mode:** config

**Hierarchies**

- services ipsec tunnel vrf

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ipsec
    dnRouter(cfg-srv-ipsec)# tunnel 1 vrf MyVrf
    dnRouter(cfg-srv-ipsec-tun)# lifetime
    dnRouter(cfg-srv-ipsec-tun-life)#


**Removing Configuration**

To remove the IPSec lifetime parameters:
::

    dnRouter(cfg-srv-ipsec-tun)# no lifetime

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.10   | Command introduced |
+---------+--------------------+
