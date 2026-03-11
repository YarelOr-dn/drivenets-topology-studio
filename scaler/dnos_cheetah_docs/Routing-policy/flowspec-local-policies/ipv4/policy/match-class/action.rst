routing-policy flowspec-local-policies ipv4 policy match-class action-type
--------------------------------------------------------------------------

**Minimum user role:** operator

Configure the packet-length as a match criteria of this match class. All criteria must match, for the match to be made.

**Command syntax: action-type [action-type]** vrf [vrf] max-rate [rate-limit]

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 policy match-class

**Parameter table**

+-------------+----------------------------------------------------------------------------------+----------------------------------+---------+
| Parameter   | Description                                                                      | Range                            | Default |
+=============+==================================================================================+==================================+=========+
| action-type | The action to be performed on match of the traffic class.                        | no-action                        | \-      |
|             |                                                                                  | rate-limit                       |         |
|             |                                                                                  | redirect-to-vrf                  |         |
|             |                                                                                  | redirect-to-vrf-and-rate-limit   |         |
+-------------+----------------------------------------------------------------------------------+----------------------------------+---------+
| vrf         | redirect-to target is a reference to another vrf - the next hop should be taken  | string                           | \-      |
|             | from that vrf.                                                                   | length 1..255                    |         |
+-------------+----------------------------------------------------------------------------------+----------------------------------+---------+
| rate-limit  | The rate in kbits per second to limit the traffic to.                            | 0..4294967295                    | \-      |
+-------------+----------------------------------------------------------------------------------+----------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# policy policy-1
    dnRouter(cfg-flp-ipv4-pl)# match-class mc-1
    dnRouter(cfg-ipv4-pl-mc)#  action-type rate-limit max-rate 0
    dnRouter(cfg-ipv4-pl-mc)# exit
    dnRouter(cfg-flp-ipv4-pl)


**Removing Configuration**

To remove the action from the policy
::

    dnRouter(cfg-ipv4-pl-mc)# no action-type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
