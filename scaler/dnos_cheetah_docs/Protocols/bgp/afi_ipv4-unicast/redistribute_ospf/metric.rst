protocols bgp address-family ipv4-unicast redistribute ospf instance metric
---------------------------------------------------------------------------

**Minimum user role:** operator

To modify the metric of redistributed routes:

**Command syntax: metric [metric]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast redistribute ospf instance

**Parameter table**

+-----------+---------------------+--------------+---------+
| Parameter | Description         | Range        | Default |
+===========+=====================+==============+=========+
| metric    | update route metric | 0-4294967295 | \-      |
+-----------+---------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute ospf instance MY_OSPF_INSTANCE
    dnRouter(cfg-bgp-afi-rdst-ospf)# metric 100


**Removing Configuration**

To revert metric to default value:
::

    dnRouter(cfg-bgp-afi-rdst-ospf)# no metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
