protocols pim address-family mofrr use-bgp-lfa
----------------------------------------------

**Minimum user role:** operator

To consider BGP in the MoFRR standby selection:

**Command syntax: use-bgp-lfa [use-bgp-lfa]**

**Command mode:** config

**Hierarchies**

- protocols pim address-family mofrr

**Note**
This command is applicable for non-ecmp UMH selection mode

**Parameter table**

+-------------+----------------------------------------+--------------+----------+
| Parameter   | Description                            | Range        | Default  |
+=============+========================================+==============+==========+
| use-bgp-lfa | Use BGP LFA in MoFRR standby selection | | enabled    | disabled |
|             |                                        | | disabled   |          |
+-------------+----------------------------------------+--------------+----------+

**Example**
::

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-address-family)# mofrr
    dnRouter(cfg-pim-address-family-mofrr)# use-bgp-lfa enabled

    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# address-family ipv4
    dnRouter(cfg-protocols-pim-address-family)# mofrr
    dnRouter(cfg-pim-address-family-mofrr)# use-bgp-lfa disabled


**Removing Configuration**

To revert use-bgp-lfa to its default value:
::

    dnRouter(cfg-pim-address-family-mofrr)# no use-bgp-lfa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
