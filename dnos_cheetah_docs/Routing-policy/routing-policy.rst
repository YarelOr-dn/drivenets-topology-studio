routing-policy
--------------

**Minimum user role:** operator

You can create policies that are used by the various routing protocols. The following types of policies are supported:

-	AS-path access-list

-	Community-list

-	extcommunity-list

-	large-community-list

-	Policy

-	Prefix-list

To enter routing policy configuration mode:

**Command syntax: routing-policy**

**Command mode:** config

**Note**

- You cannot remove a routing-policy that is being used.

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# 

**Removing Configuration**

To remove all policies configuration (all as-path-lists, community-lists, extcommunity-lists, large-community-lists , policies and prefix-lists):
::

	dnRouter(cfg)# no routing-policy

.. **Help line:** enters routing policy configuration mode

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 6.0         | Command introduced    |
+-------------+-----------------------+
