protocols isis instance interface address-family conditional-adv level level-1 policy
-------------------------------------------------------------------------------------

**Minimum user role:** operator

Condition IP reachability advetisement (TLV 135/235/236/237) of interface prefix using a route policy. 
All related reachability infromation such as Segment-Routing SIDs will also be effected. 
Conditional route Adrvertismeant is used to alter ISIS advertisements based on network status, by identifying specific network scenarios using a routing policy, ISIS should stop advertising given prefixes.
This feature is useful for network edge scenarios like ASBR, Upon failure of uplink interface that is used as exist point to another AS, ISIS will stop advertising the lo0 that is used as the next hop. Commonly used when ASBRs advertise the anycast sid as the BGP next-hop.

**Command syntax: conditional-adv level level-1 policy [policy-name]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family

**Note**

- Level configuration is optional, if no level is set, impose for level-1-2. Any configuration for more specific level take presedence

- Metric manipulation by conditional-adv will override interface metric setting, except when max-metric is being set. - i.e when max-metric is required to be advertised to interface , in case prefix is allowed to be advertised, max-matric will be provided

- For non loopback interface, ISIS neighbor info are uneffected (TLV 22/23/222/223)

**Parameter table**

+-------------+--------------------+------------------+---------+
| Parameter   | Description        | Range            | Default |
+=============+====================+==================+=========+
| policy-name | Impose for level-1 | | string         | \-      |
|             |                    | | length 1-255   |         |
+-------------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface lo0
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# conditional-adv level level-1 policy MY_POLICY
    dnRouter(cfg-isis-inst-if)# address-family ipv6-unicast
    dnRouter(cfg-inst-if-afi)# conditional-adv level level-1 policy MY_POLICY


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-if-afi)# no conditional-adv level level-1 policy MY_POLICY

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
