routing-policy policy rule match protocol
-----------------------------------------

**Minimum user role:** operator

Match a prefix by the protocol origin from which the prefix was learned.

**Command syntax: match protocol [match-protocol]**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**
Currently this option is only supported for policies applied to RIB-groups and VPN.

**Parameter table**

+----------------+-----------------------------------------------------------------+---------------+---------+
| Parameter      | Description                                                     | Range         | Default |
+================+=================================================================+===============+=========+
| match-protocol | Match a prefix by protocol origin from which prefix was learned | | connected   | \-      |
|                |                                                                 | | static      |         |
|                |                                                                 | | bgp         |         |
|                |                                                                 | | ospf        |         |
|                |                                                                 | | ospfv3      |         |
|                |                                                                 | | isis        |         |
|                |                                                                 | | pim         |         |
|                |                                                                 | | ldp         |         |
|                |                                                                 | | rsvp        |         |
|                |                                                                 | | isis-sr     |         |
|                |                                                                 | | ospf-sr     |         |
|                |                                                                 | | sr-te       |         |
+----------------+-----------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# match protocol connected


**Removing Configuration**

To remove match protocols criteria:
::

    dnRouter(cfg-rpl-policy-rule-10)# no match protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
