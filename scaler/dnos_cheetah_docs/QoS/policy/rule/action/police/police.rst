qos policy rule action police
-----------------------------

**Minimum user role:** operator

Traffic policing limits the rate of traffic that enters a network device according to the traffic classification. Matching traffic is metered against rate specification.

The following policing meters are supported:

- sr2cm - single-rate two color meter

- sr3cm - single-rate three color meter

- tr3ccm - two rates three color coupled meter

- tr3cm - two rates three color meter.

The policer enforces a confirm, exceed or violate action according to the marker's output.

The in color represents the color of the traffic class matched by the rule, and is determined by the explicit or implicit set drop-tag action. Traffic is matched against a meter, either ignoring in-color (color-blind meter) or taking color into account (color-aware meter), and the meter assigns a marker color to the packet. The in color and marker color are combined according to the table below to form the final color that is used for queue admission decisions, e.g. to select whether to use the wred green or yellow curves for wred admission.

+--------------------------+--------------------------+--------------------------+
| In color (set drop-tag)  | Marker color (police)    | Final-color (admission)  |
+--------------------------+--------------------------+--------------------------+
| green                    | green                    | green                    |
+--------------------------+--------------------------+--------------------------+
| green                    | yellow                   | yellow                   |
+--------------------------+--------------------------+--------------------------+
| green                    | red                      | red (drop)               |
+--------------------------+--------------------------+--------------------------+
| yellow                   | green                    | yellow                   |
+--------------------------+--------------------------+--------------------------+
| yellow                   | yellow                   | yellow                   |
+--------------------------+--------------------------+--------------------------+
| yellow                   | red                      | red (drop)               |
+--------------------------+--------------------------+--------------------------+

To configure a police action:

**Command syntax: police**

**Command mode:** config

**Hierarchies**

- qos policy rule action

**Note**

- You can view the policer rate and bucket size parameters in the 'show qos interface' command.

- The policer bucket size that can be set in the hardware is 50 KB, even if the relative settings calculation arrives at a smaller value. The policer's largest size is set to 255 MB, even if the relative calculation is a larger value. The actual settable values are displayed in the 'show qos interfaces' command.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# police
    dnRouter(cfg-myPolicy1-rule-1-action-police)#


**Removing Configuration**

To remove the policing action:
::

    dnRouter(cfg-myPolicy1-rule-1-action)# no police

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 13.1    | Command introduced                                           |
+---------+--------------------------------------------------------------+
| 16.1    | Split from the generic qos-policy-action-police-rate command |
+---------+--------------------------------------------------------------+
