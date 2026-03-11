routing-policy qppb-policy rule action redirect-vrf
---------------------------------------------------

**Minimum user role:** operator

When the rule is matched, the redirect-vrf action will direct the matching traffic to be handled under the specified VRF. 

To set the redirect action:

**Command syntax: redirect-vrf [redirect-to-vrf]**

**Command mode:** config

**Hierarchies**

- routing-policy qppb-policy rule action

**Note**

- You can define multiple set actions per rule.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter       | Description                                                                      | Range            | Default |
+=================+==================================================================================+==================+=========+
| redirect-to-vrf | redirect-to-vrf target is a reference to another vrf (not the defined            | | string         | \-      |
|                 | applicable-vrf) - the next hop should be taken from that vrf                     | | length 1-255   |         |
+-----------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# qppb-policy PL-1
    dnRouter(cfg-rpl-qppb-policy-PL-1)# rule 10
    dnRouter(cfg-rpl-qppb-policy-PL-1-rule-10)# action
    dnRouter(cfg-qppb-policy-PL-1-rule-10-action) redirect-vrf Customer-1-VRF


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qppb-policy-PL-1-rule-10-action)# no redirect-vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
