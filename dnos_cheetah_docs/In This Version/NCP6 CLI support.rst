NCP6 CLI Command Support
------------------------

Due to limitations of the NCP6 platform, some features are unsupported (by commit validation for CLI & NETCONF).
To avoid the risk of NCP failure when features are not supported, the following CLI commands will not be supported:

**Note**

All validations will provide the following error:

Error: Command not supported by current system.

*Flowspec*

- interfaces flowspec - cannot be enabled
- forwarding-options flowspec-local ipv4 apply-policy-to-flowspec - cannot attach local flowspec policy
- forwarding-options flowspec-local ipv6 apply-policy-to-flowspec - cannot attach local flowspec policy
- protocols bgp neighbor address-family - does not support ipv4-flowspec and ipv6-flowspec  
- Same for 'protocols bgp neighbor-group address-family'  & 'bgp neighbor-group  neighbor address-family'

*QPPB*

- interfaces qppb admin-state - cannot be enabled
- forwarding-options install-qppb-policy - cannot attach qppb policy
- routing-policy policy rule allow set qppb dest-class
- routing-policy policy rule allow set qppb src-class

*uRPF*

- interfaces urpf admin-state - cannot be enabled 

*Egress ACL*

- interfaces access-list ipv4/6 direction out - cannot attach access list

*L3 Multicast*

- protocols pim
- protocols ldp multipoint p2mp admin-state - cannot be enabled

*Tx fragmentation*

- system ipv4-fragmentation-in-transit admin-state - cannot be enabled. 

*SR-TE/RSVP* 

- protocols rsvp tunnel - cannot configure a RSVP tunnel
- protocols segment-routing mpls policy - cannot configure an SR-TE policy

*SR/LDP FEC stat*

- FEC statistics will be disabled by default.
 
*VRF-Redirect*

- protocols static address-family ipv4/6 route next-table - cannot be configured
- protocols bgp address-family ipv4/6-unicast bgp-leak import-from - cannot be configured

*Ingress policer*

- qos policy rule action police - cannot be configured 

*Timing*

- system ncp clock synce admin-state - cannot be enabled
- system ncp clock ptp tod-mode - cannot be configured
- system ncp clock ptp g8275-1 admin-state - cannot be enabled

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 19.1    | Limitations introduced                                         |
+---------+----------------------------------------------------------------+


  