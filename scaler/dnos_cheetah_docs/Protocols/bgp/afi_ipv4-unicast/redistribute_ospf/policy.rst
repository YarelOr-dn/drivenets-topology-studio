protocols bgp address-family ipv4-unicast redistribute ospf instance policy
---------------------------------------------------------------------------

**Minimum user role:** operator

Impose a routing policy or policies to filter or modify redistributed routes:

**Command syntax: policy [policy]** [, policy, policy]

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast redistribute ospf instance

**Note**

- Can set multiple policies. If multiple policies are set the policies are evaluated one after the other according to the user input order.

**Parameter table**

+-----------+------------------------------+------------------+---------+
| Parameter | Description                  | Range            | Default |
+===========+==============================+==================+=========+
| policy    | redistribute by policy rules | | string         | \-      |
|           |                              | | length 1-255   |         |
+-----------+------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute ospf instance MY_OSPF_INSTANCE
    dnRouter(cfg-bgp-afi-rdst-ospf)# policy My_Policy, My_Policy2


**Removing Configuration**

To remove policy:
::

    dnRouter(cfg-bgp-afi-rdst-ospf)# no policy My_Policy

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 18.1    | Added support for multiple policies attachments |
+---------+-------------------------------------------------+
