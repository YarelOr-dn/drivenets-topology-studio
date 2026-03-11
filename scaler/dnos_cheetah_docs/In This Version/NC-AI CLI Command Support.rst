NC-AI CLI Command Support
-------------------------

NC-AI is based on the same DNOS as Network Cloud. However, due to the different nature of this product, some features unsupported in Network Cloud are not supported in NC-AI. The commands for these features still appear in the CLI, however, you should refrain from configuring them. We've added validations to commands that must not be configured. However, as the CLI includes all DNOS commands, we did our utmost to remove the unsupported commands from the guide. Some unsupported commands may still exist in the guide.

**Note**

For unsupported commands with validation, the following error is displayed:

Error: Command not supported by current system.

The following Features/protocols are not supported:

- Interfaces/Interfaces/Clock
- MPLS
- Multicast
- NACM
- Network-services *
- Protocols/bfd
- Protocols/bgp
- Protocols/igmp
- Protocols/isis
- Protocols/lacp
- Protocols/ldp
- Protocols/mpls
- Protocols/msdp
- Protocols/ospf
- Protocols/ospfv3
- Protocols/pcep
- Protocols/pim
- Protocols/rsvp
- Protocols/segment-routing
- Protocols/vrrp
- QOS/vrf-redirect
- QOS/policy/rule/action/police
- Routing-options/bmp_server
- Routing-options/rpki_server
- Routing-options/table_mpls-nh-ipv6
- Routing-policy/flowspec
- Routing-policy/qppb-policy
- Segment-routing
- Services/ethernet-oam
- Services/ipsec
- Services/l2-cross-connect
- Services/mpls-oam
- Services/performance-monitoring
- Services/port-mirroring
- Services/simple-twamp
- Services/twamp
- System/cprl
- System/diagnostics
- System/high-availability
- VRFs

In addition, despite residing in supported hierarchies, the following commands are not supported.

**Note**
An asterisk indicates that whatever comes after is also not supported.

*Access-lists*
access-lists rule vrf

*Debug*
debug bgp dampening
debug isis
debug ldp
debug mpls-oam
debug msdp
debug ospf
debug ospfv3
debug pim
debug rsvp
debug segment-routing
debug vrrp
microloop avoidance

*Forwarding-options*
forwarding-options flowspec *
forwarding-options install qppb policy

*GI Mode Commands*
request system deploy (replaced by request system ai-deploy)


*Interfaces*
interfaces bundle
interfaces bundle-id
interfaces bundle min-bandwidth
interfaces bundle min-links
interfaces bundle mixed-type
interfaces carrier-delay on-startup interval
interfaces console-ncc admin-state
interfaces console-ncc
interfaces destination
interfaces flow-monitoring type ipv4-over-mpls *
interfaces flow-monitoring type ipv6-over-mpls *
interfaces flowspec
interfaces ipmi-ncc *
interfaces irb
interfaces l2-service
interfaces mtu-gre *
interfaces mtu-mpls
interfaces mpls
interfaces port *
interfaces qppb
interfaces source
interfaces speed
interfaces transceiver optical transport grid spacing
interfaces untagged
interfaces urpf *
interfaces vlan-id
interfaces vlan-manipulation egress-mapping *
interfaces vlan-manipulation ingress-mapping *
interfaces vlan-tags outer-tag inner-tag

*Policy*
policy match rpki
policy set aigp
policy set isis metric
policy set ospf metric
policy set rpki

*Protocols*
protocols bgp nsr

*QOS*
qos policy rule action set mpls-exp
qos traffic-class-map mpls-exp
mpls-swap-exp-edit-mode
qos global-policy-map default-mpls mpls-exp

*Request Commands*
request service ipsec session reset
request system ncc switchover

*Routing-options*
routing-options segment-routing mpls global-block
routing-options segment-routing mpls
routing-options table mpls-nh-ipv6

*Set Commands*
set evpn mac-suppression
set rsvp auto-bandwidth sample

*System*
system hardware model temperature-threshold


*Services*
Services performance-monitoring interfaces delay-measurement

*Run Commands*
run mtrace
run packet-capture ncc
run ping mpls *
run ping multicast
run traceroute mpls *

*Request Commands*
request mpls *
request rsvp *
request segment-routing *

*Show Commands and Clear Commands*
Show and clear commands for unsupported features have not been removed from the guide.


**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 19.10   | Limitations introduced                                         |
+---------+----------------------------------------------------------------+
