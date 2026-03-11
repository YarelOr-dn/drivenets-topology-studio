routing-policy flowspec-local-policies ipv4 policy match-class action redirect-to-vrf
-------------------------------------------------------------------------------------

**Minimum user role:** operator

Configures the action of a redirect to another vrf when matching to this match-class.

**Command syntax: action redirect-to-vrf [redirected-to-vrf]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 policy match-class

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter         | Description                                                                      | Range            | Default |
+===================+==================================================================================+==================+=========+
| redirected-to-vrf | redirect-to-vrf target is a reference to another vrf - the next hop should be    | | string         | \-      |
|                   | taken from that vrf                                                              | | length 1-255   |         |
+-------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# policy policy-1
    dnRouter(cfg-flp-ipv4-pl)# match-class mc-1
    dnRouter(cfg-ipv4-pl-mc)#  action redirect-to-vrf vrf-1
    dnRouter(cfg-ipv4-pl-mc)# exit
    dnRouter(cfg-flp-ipv4-pl)


**Removing Configuration**

To remove the action from the policy:
::

    dnRouter(cfg-ipv4-pl-mc)# no action redirect-to-vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
