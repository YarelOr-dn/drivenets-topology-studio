protocols bgp enforce-first-as
------------------------------

**Minimum user role:** operator

This command forces the BGP router to compare the first AS, in the AS path of eBGP routes received from neighbors, to the configured remote external neighbor AS number. Updates from eBGP neighbors that do not include that AS number as the first item in the AS_PATH attribute will be ignored.

**Command syntax: enforce-first-as**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# enforce-first-as


**Removing Configuration**

To disable the enforcement:
::

    dnRouter(cfg-protocols-bgp)# no enforce-first-as

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
