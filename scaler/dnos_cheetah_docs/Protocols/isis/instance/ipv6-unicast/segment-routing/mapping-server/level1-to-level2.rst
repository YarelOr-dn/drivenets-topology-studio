protocols isis instance address-family ipv6-unicast segment-routing mapping-server propagate level1-to-level2 policy
--------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

You can control the propagation of binding SIDs between ISIS levels. Propagation can be done even if the router is not enabled as a mapping client.

Only "policy match ipv6 prefix" can be used in the propagation attachment points. Other match / set statements will be ignored.
Match is achieved when a binding-SID prefix is matches an allow rule in the attached prefix-list. When the binding-SID has a range, the match in the propagation policy is on the first prefix in the range. I.e., a binding-SID 9:9::9:1/128 with range 10 will be matched with ipv6-prefix 9:9::9:1/128 matching-len 128, but not with 9:9::9:4/128 matching-len 128.

To control the propagation of binding-SIDs between ISIS levels:

**Command syntax: propagate level1-to-level2 policy [policy-name]** s-flag-ignore

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast segment-routing mapping-server

**Note**

- Propagation can be done from level-1 to level-2 and from level-2 to level-1 at the same time, each using a separate policy.

- Reconfiguring the policy in any propagation direction maintains the existing s-flag-ignore settings.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter     | Description                                                                      | Range            | Default |
+===============+==================================================================================+==================+=========+
| policy-name   | The new preference value to be advertised                                        | | string         | \-      |
|               | A value of 0 indicates that advertisements from this node must not be used. The  | | length 1-255   |         |
|               | preference TLV will not be advertised.                                           |                  |         |
+---------------+----------------------------------------------------------------------------------+------------------+---------+
| s-flag-ignore | Allows the propagation even when the s-flag is not set on the binding-SID TLV.   | \-               | \-      |
|               | By default, when s-flag is not set, no propagation will be done for binding-SIDs |                  |         |
|               | in any direction. The s-flag configuration is per direction.                     |                  |         |
|               | Reconfiguring the policy in a given propagate direction will maintain the        |                  |         |
|               | existing s-flag-ignore settings.                                                 |                  |         |
+---------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)# propagate level1-to-level2 policy My_Pol_1_2 s-flag-ignore
    dnRouter(cfg-afi-sr-mapping)# propagate level2-to-level1 policy My_Pol_2_1


**Removing Configuration**

To remove the s-flag-ignore configuration:
::

    dnRouter(cfg-afi-sr-mapping)# no propagate level1-to-level2 policy My_Pol_1_2 s-flag-ignore

To stop level-1 into level-2 propagation and remove the s-flag-ignore configuration:
::

    dnRouter(cfg-afi-sr-mapping)# no propagate level1-to-level2 policy My_Pol_1_2

To revert to the default behavior where all binding-SID with s-flag configured will be propagated from level-2 to level-1, (i.e., also remove s-flag-ignore configuration):
::

    dnRouter(cfg-afi-sr-mapping)# no propagate level2-to-level1 policy My_Pol_2_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
