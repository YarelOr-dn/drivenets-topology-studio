policy set ipv4 next-hop
------------------------

**Minimum user role:** operator

To set the IPv4 next hop address:

**Command syntax: set ipv4 next-hop {[ipv4-address]|self|self-force|peer-address}**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+---------------+-----------------------------------------------------------+-----------+-------------+
|               |                                                           |           |             |
| Parameter     | Description                                               | Range     | Default     |
+===============+===========================================================+===========+=============+
|               |                                                           |           |             |
| ipv4-address  | The BGP neighbor IPv4 address to set as the next hop.     | A.B.C.D   | \-          |
+---------------+-----------------------------------------------------------+-----------+-------------+
| self          | Set next-hop to local speaker address for outbound policy |           | \-          |
+---------------+-----------------------------------------------------------+-----------+-------------+
| self-force    | Set next-hop to local speaker address for outbound policy |           | \-          |
|               | even when acting as route-reflector                       |           |             |
+---------------+-----------------------------------------------------------+-----------+-------------+
| peer-address  | Set next-hop to remote speaker address for inbound policy |           | \-          |
+---------------+-----------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set ipv4 next-hop 192.0.2.1

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_SELF
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set ipv4 next-hop self

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_SELF
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set ipv4 next-hop self-force

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_PEER_ADDRESS
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set ipv4 next-hop peer-address

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set ipv4 next-hop


.. **Help line:** Set the next hop to the BGP neighbor IPv4 address

**Command History**

+-------------+---------------------------+
|             |                           |
| Release     | Modification              |
+=============+===========================+
|             |                           |
| 6.0         | Command introduced        |
+-------------+---------------------------+
|             |                           |
| 17.1        | Added self option         |
+-------------+---------------------------+
|             |                           |
| 17.1        | Added peer-address option |
+-------------+---------------------------+