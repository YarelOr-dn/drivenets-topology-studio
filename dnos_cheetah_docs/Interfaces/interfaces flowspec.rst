interfaces flowspec
-------------------

**Minimum user role:** operator

Flowspec is a dynamic data path policy that is received from a remote neighbor through BGP in order to impose different behaviors on different traffic flows. Flowspec is typically used to block or rate-limit distributed denial-of-service (DDoS) attacks and protect against malicious flows.

Flowspec specifies rules for matching a specific flow with source and destination, L4 parameters, and other packet specifics (e.g. length, fragmented, etc.) and encodes them as BGP network layer reachability information (NLRI). It also enables to dynamically install an action at the border router to drop all traffic. The action is coded as an extended community in the NLRI.
The actions that can be taken with FlowSpec are:

- Allow - the traffic is unaffected
- Drop - the traffic-rate community with a rate value of 0 tells the receiving router to discard all the traffic
- Redirect - redirect control or datapath traffic to IPv4 and IPv6 next-hops. This allows to mitigate DDOS attacks by redirecting suspected flows towards a scrubbing center, where further actions will be executed, and the safe traffic will be sent back to the network. The redirect to IP action is supported for both IPv4 and IPv6 addresses.

	The redirect operation is supported within the default VRF. I.e., redirect to a different VRF is not supported.

	Rules that carry both a redirect to IP next-hop and traffic-rate that equals 0.0 bps (i.e., drop) as BGP extended communities, will not be installed and are displayed as unsupported NLRI and/or action.

To configure FlowSpec:

#.	Configure BGP neighbors from which BGP FlowSpec rules are received (see "bgp neighbor" and "bgp neighbor address-family"). This will cause the router to share NLRIs with its peers.
#.	(Optional) Limit the number of FlowSpec rules received from the peers (see "bgp neighbor address-family maximum-prefix" and "bgp neighbor address-family maximum-prefix exceed-action").
#.	Configure the interfaces that will be FlowSpec-enabled:

To enable FlowSpec filtering on an interface:

**Command syntax: flowspec [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

	- Physical
	- Physical vlan
	- Bundle
	- Bundle vlan
	- IRB

- BGP FlowSpec does not impact the normal processing of packets running through the network processing unit (NPU).

- When enabled, ingress flow filtering will be applied according to rules received by BGP FlowSpec.

- A physical interface assigned to a bundle inherits the FlowSpec definition of the bundle.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Set the administrative state of the FlowSpec feature on the interface. When      | | enabled    | disabled |
|             | enabled, ingress flow filtering will be applied according to the rules received  | | disabled   |          |
|             | by BGP FlowSpec.                                                                 |              |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# flowspec enabled

    dnRouter(cfg-if)# bundle-1.10
    dnRouter(cfg-if-bundle-1.10)# flowspec disabled

    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# flowspec enabled

    dnRouter(cfg-if)# ge100-1/1/1.20
    dnRouter(cfg-if-ge100-1/1/1.20)# flowspec disabled

    dnRouter(cfg-if)# bundle-2
    dnRouter(cfg-if-bundle-2)# flowspec enabled

    dnRouter(cfg-if)# bundle-2
    dnRouter(cfg-if-bundle-2)# flowspec disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/1/1)# no flowspec

::

    dnRouter(cfg-if-ge100-1.20)# no flowspec

::

    dnRouter(cfg-if-bundle-2)# no flowspec

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 13.0    | Command introduced                                    |
+---------+-------------------------------------------------------+
| 13.3    | Added support for redirect to IPv4 and IPv6 next-hops |
+---------+-------------------------------------------------------+
