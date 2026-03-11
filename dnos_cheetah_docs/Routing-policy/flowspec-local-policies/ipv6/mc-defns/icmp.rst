routing-policy flowspec-local-policies ipv6 match-class icmp
------------------------------------------------------------

**Minimum user role:** operator

Configures the icmp as a match criteria of this match class. For the match to be made, all criteria must match.

**Command syntax: icmp [message-type]**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies ipv6 match-class

**Parameter table**

+--------------+-------------------------+-------------------------------------------------+---------+
| Parameter    | Description             | Range                                           | Default |
+==============+=========================+=================================================+=========+
| message-type | ipv6-icmp message type. | | no-route-to-destination                       | \-      |
|              |                         | | administratively-prohibited                   |         |
|              |                         | | beyond-scope-of-source-address                |         |
|              |                         | | address-unreachable                           |         |
|              |                         | | port-unreachable                              |         |
|              |                         | | source-address-failed-ingress/egress-policy   |         |
|              |                         | | reject-route-to-destination                   |         |
|              |                         | | error-in-source-routing-header                |         |
|              |                         | | packet-too-big                                |         |
|              |                         | | hop-limit-exceeded-in-transit                 |         |
|              |                         | | fragment-reassembly-time-exceeded             |         |
|              |                         | | erroneous-header-field-encountered            |         |
|              |                         | | unrecognized-next-header-type-encountered     |         |
|              |                         | | unrecognized-ipv6-option-encountered          |         |
|              |                         | | echo-request                                  |         |
|              |                         | | echo-reply                                    |         |
|              |                         | | multicast-listener-query                      |         |
|              |                         | | multicast-listener-report                     |         |
|              |                         | | multicast-listener-done                       |         |
|              |                         | | router-solicitation                           |         |
|              |                         | | router-advertisement                          |         |
|              |                         | | neighbor-solicitation                         |         |
|              |                         | | neighbor-advertisement                        |         |
|              |                         | | redirect-message                              |         |
|              |                         | | renumbering-command                           |         |
|              |                         | | renumbering-result                            |         |
|              |                         | | renumbering-sequence-number-reset             |         |
|              |                         | | query-ipv6-address                            |         |
|              |                         | | query-name                                    |         |
|              |                         | | query-ipv4-address                            |         |
|              |                         | | response-successful                           |         |
|              |                         | | response-refuse                               |         |
|              |                         | | response-unknown                              |         |
|              |                         | | solicitation-message                          |         |
|              |                         | | advertisement-message                         |         |
|              |                         | | mldv2-reports                                 |         |
|              |                         | | discovery-request-message                     |         |
|              |                         | | discovery-reply-message                       |         |
|              |                         | | mobile-prefix-solicitation                    |         |
|              |                         | | mobile-prefix-advertisement                   |         |
|              |                         | | certification-path-solicitation               |         |
|              |                         | | certification-path-advertisement              |         |
|              |                         | | mrd-advertisement                             |         |
|              |                         | | mrd-solicitation                              |         |
|              |                         | | mrd-termination                               |         |
|              |                         | | rpl-control-message                           |         |
+--------------+-------------------------+-------------------------------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)# match-class mc-1
    dnRouter(cfg-flp-ipv6-mc)# icmp echo-reply
    dnRouter(cfg-flp-ipv6-mc)#


**Removing Configuration**

To remove the icmp from the match class:
::

    dnRouter(cfg-flp-ipv6-mc)# no icmp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
