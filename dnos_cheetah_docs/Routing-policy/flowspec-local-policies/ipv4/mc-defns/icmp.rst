routing-policy flowspec-local-policies ipv4 match-class icmp
------------------------------------------------------------

**Minimum user role:** operator

Configures the icmp as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: icmp [message-type]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv4 match-class

**Parameter table**

+--------------+--------------------+-----------------------------------------------+---------+
| Parameter    | Description        | Range                                         | Default |
+==============+====================+===============================================+=========+
| message-type | icmp message type. | | echo-reply                                  | \-      |
|              |                    | | destination-network-unreachable             |         |
|              |                    | | destination-host-unreachable                |         |
|              |                    | | destination-protocol-unreachable            |         |
|              |                    | | destination-port-unreachable                |         |
|              |                    | | fragmentation-required                      |         |
|              |                    | | source-route-failed                         |         |
|              |                    | | destination-network-unknown                 |         |
|              |                    | | destination-host-unknown                    |         |
|              |                    | | source-host-isolated                        |         |
|              |                    | | network-administratively-prohibited         |         |
|              |                    | | host-administratively-prohibited            |         |
|              |                    | | network-unreachable-for-tos                 |         |
|              |                    | | host-unreachable-for-tos                    |         |
|              |                    | | communication-administratively-prohibited   |         |
|              |                    | | host-precedence-violation                   |         |
|              |                    | | precedence-cutoff-in-effect                 |         |
|              |                    | | redirect-network                            |         |
|              |                    | | redirect-host                               |         |
|              |                    | | redirect-tos-network                        |         |
|              |                    | | redirect-tos-host                           |         |
|              |                    | | echo-request                                |         |
|              |                    | | router-advertisement                        |         |
|              |                    | | router-solicitation                         |         |
|              |                    | | ttl-expired-in-transit                      |         |
|              |                    | | fragment-reassembly                         |         |
|              |                    | | pointer-indicates-error                     |         |
|              |                    | | missing-required-option                     |         |
|              |                    | | bad-length                                  |         |
|              |                    | | timestamp                                   |         |
|              |                    | | timestamp-reply                             |         |
+--------------+--------------------+-----------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)# match-class mc-1
    dnRouter(cfg-flp-ipv4-mc)# icmp echo-reply
    dnRouter(cfg-flp-ipv4-mc)#


**Removing Configuration**

To remove the icmp from the match class:
::

    dnRouter(cfg-flp-ipv4-mc)# no icmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
