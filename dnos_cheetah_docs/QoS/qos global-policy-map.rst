qos global-policy-map
---------------------

**Minimum user role:** operator

Global policy maps control the traffic's mapping of QoS attributes to per-hop behavior (PHB), i.e. to qos-tag and drop-tag for IP, MPLS and layer-2 traffic not controlled by an interface ingress QoS policy.

You can configure the following global policy maps:

• Default-IP global map: 

  The qos-tag and drop-tag assigned to IP traffic originated and sent from the system to the network ("from-me" traffic) is controlled globally by this map. The mapping is also used as the ingress policy on all interfaces which are not assigned any user policy.

  For example, BGP traffic sent from the NCC will use the assigned BGP DSCP value (configured using the  "protocols bgp class-of-service" command), and will be mapped to qos-tag and drop-tag specified by this map.

  The following table describes the default mapping of DSCP to qos-tag, with drop-tag set to yellow for qos-tags 1 and 3:

  ::

    +-------------+----------+----------+           +-------------+----------+----------+
    | dscp        | qos-tag  | drop-tag |           | dscp        | qos-tag  | drop-tag |
    +-------------+----------+----------+           +-------------+----------+----------+
    | default     | 0        | green    |           | cs4         | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 1           | 0        | green    |           | 33          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 2           | 0        | green    |           | af41        | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 3           | 0        | green    |           | 35          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 4           | 0        | green    |           | af42        | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 5           | 0        | green    |           | 37          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 6           | 0        | green    |           | af43        | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 7           | 0        | green    |           | 39          | 4        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | cs1         | 1        | yellow   |           | cs5         | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 9           | 1        | yellow   |           | 41          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af11        | 1        | yellow   |           | 42          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 11          | 1        | yellow   |           | 43          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af12        | 1        | yellow   |           | voice-admit | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 13          | 1        | yellow   |           | 45          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af13        | 1        | yellow   |           | ef          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 15          | 1        | yellow   |           | 47          | 5        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | cs2         | 2        | green    |           | cs6         | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 17          | 2        | green    |           | 49          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af21        | 2        | green    |           | 50          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 19          | 2        | green    |           | 51          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af22        | 2        | green    |           | 52          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 21          | 2        | green    |           | 53          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af23        | 2        | green    |           | 54          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 23          | 2        | green    |           | 55          | 6        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | cs3         | 3        | yellow   |           | cs7         | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 25          | 3        | yellow   |           | 57          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af31        | 3        | yellow   |           | 58          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 27          | 3        | yellow   |           | 59          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af32        | 3        | yellow   |           | 60          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 29          | 3        | yellow   |           | 61          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | af33        | 3        | yellow   |           | 62          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    | 31          | 3        | yellow   |           | 63          | 7        | green    |
    +-------------+----------+----------+           +-------------+----------+----------+
    
• Default-MPLS global map:

  The qos-tag and drop-tag assigned to MPLS traffic originated and sent from the system to the network ("from-me" traffic) is controlled globally by this map. The mapping is also used as the ingress policy on all interfaces which are not assigned any user policy.

  For example, MPLS Ping packets sent from the NCC will use the assigned BGP exp value (e.g. using the  "run ping" mpls bgp-lu 1.2.3.4/32 count 10 exp 4 command), and will be mapped to qos-tag and drop-tag specified by this map.

  The qos-tag and drop-tag assigned to incoming MPLS packets at tunnel termination, when termination with explicit-null label is used, is also controlled globally by this map. Mapping of all other MPLS traffic, either mid tunnel (swap) or at the penultimate-hop-popping (PHP) tunnel edge are controlled per QoS policy attached to the ingress interface.

  The pipe model requires that the PHB will be selected according to the mpls-exp value of the top-most label, and in particular, when the tunnel is terminated using the explicit-null label (reserved labels 0 or 3 for Ipv6), the PHB is determined from the mpls-exp carried by the explicit null label.

  The following table describes the default mapping of the MPLS exp value to qos-tag, with drop-tag set to yellow for qos-tags 1 and 3:
  ::

    +----------+----------+----------+
    | mpls-exp | qos-tag  | drop-tag |
    +----------+----------+----------+
    | 0        | 0        | green    |
    +----------+----------+----------+
    | 1        | 1        | yellow   |
    +----------+----------+----------+
    | 2        | 2        | green    |
    +----------+----------+----------+
    | 3        | 3        | yellow   |
    +----------+----------+----------+
    | 4        | 4        | green    |
    +----------+----------+----------+
    | 5        | 5        | green    |
    +----------+----------+----------+
    | 6        | 6        | green    |
    +----------+----------+----------+
    | 7        | 7        | green    |
    +----------+----------+----------+

• Default-L2 global map:
  
  The qos-tag and drop-tag assigned to layer 2 traffic originated and sent from the system to the network ("from-me" traffic) is controlled globally by this map. For example, ARP, IS-IS, LLDP, etc.
  
  By default, L2 traffic is assigned qos-tag 6 and drop-tag green.

To configure a QoS global policy map, enter the policy's configuration mode:

**Command syntax: qos global-policy-map [global-policy-map-name]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+---------------------------+---------------------------------------------------+------------------------------------------------------------------------------------+-------------+
|                           |                                                   |                                                                                    |             |
| Parameter                 | Description                                       | Range                                                                              | Default     |
+===========================+===================================================+====================================================================================+=============+
|                           |                                                   |                                                                                    |             |
| global-policy-map-name    | The name of the global policy map to configure    | default-ip: default mapping applicable to from-me   IP traffic                     | \-          |
|                           |                                                   |                                                                                    |             |
|                           |                                                   | default-mpls: default mapping applicable to   from-me / Explicit NULL MPLS traffic |             |
|                           |                                                   |                                                                                    |             |
|                           |                                                   | default-l2: Default mapping. Applicable to   from-me L2 traffic                    |             |
+---------------------------+---------------------------------------------------+------------------------------------------------------------------------------------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-ip
  dnRouter(cfg-qos-default-ip)#

  dnRouter(cfg-qos)# global-policy-map default-mpls
  dnRouter(cfg-qos-default-mpls)#

  dnRouter(cfg-qos)# global-policy-map default-l2
  dnRouter(cfg-qos-default-l2)#


**Removing Configuration**

To remove the global-policy-map configuration:
::

  dnRouter(cfg-qos)# no global-policy-map default-ip
  dnRouter(cfg-qos)# no global-policy-map

.. **Help line:** configure qos global-policy-map

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+