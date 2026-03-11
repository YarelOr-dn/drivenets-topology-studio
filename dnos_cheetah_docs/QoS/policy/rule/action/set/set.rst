qos policy rule action set
--------------------------

**Minimum user role:** operator

To configure a set action for the matched traffic class. The actions you can configure are:

Ingress policy actions:
- set qos-tag
- set drop-tag
- set mpls-exp

Egress policy actions:
- set pcp
- set pcp-dei
- set dscp (untrusted interfaces only)
- set ipp (untrusted interfaces only)
- set dscp and set ipp can only be set on egress policies attached to ip-marking untrusted (peering) interfaces. The IP DSCP field is remarked on ingress and egress according to the global qos remarking-map and the qos-tag and drop-tag assigned to the packet. set dscp and set ipp overrides the remarking table on egress. Either set dscp or set ipp actions can be used within the same rule.

Each ingress policy rule must include a set qos-tag action. Rule default sets qos-tag to 0 by default. If set drop-tag is not specified, set drop-tag green is implicitly assumed. Each rule within the policy must specify a different (qos-tag, drop-tag) tuple. This implies that the maximum number of rules configurable in any ingress policy, including rule default, is 16.

The command set mpls-exp modifies the EXP bits of incoming topmost swapped MPLS header. Set mpls-exp action can only be set if mpls-swap-exp-edit-mode parameter is set to copy. The MPLS EXP bits are set on the outgoing swapped MPLS header, as well as any additional pushed MPLS headers added at egress.

**Command syntax: set**

**Command mode:** config

**Hierarchies**

- qos policy rule action

**Note**

- no set removes whole selected action set. For dscp or ipp action, it is possible to remove a set command for a particular dscp (ipp) only, or to a particular dscp (ipp) and color only.

- set pcp is applied on all sub-interfaces of the interface the policy is attached to.

- set actions must be unambiguous and not dependent on order of actions. In particular, you cannot define both an action with all qualifier, e.g. **set dscp all all 5** and another similar set action with specific qos-tag or drop-tag qualifiers, e.g. also dscp 33 all 6, within the same rule.

- You can define multiple set actions per rule.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# set
    dnRouter(cfg-myPolicy1-rule-1-action-set)#


**Removing Configuration**

To remove the set configuration:
::

    dnRouter(cfg-myPolicy1-rule-1-action)# no set

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 5.1.0   | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 6.0     | When moving into different modes, higher mode names are removed |
+---------+-----------------------------------------------------------------+
| 9.0     | QoS not supported                                               |
+---------+-----------------------------------------------------------------+
| 11.2    | Command re-introduced                                           |
+---------+-----------------------------------------------------------------+
| 13.0    | Added support for egress and ingress DSCP marking               |
+---------+-----------------------------------------------------------------+
| 16.1    | Split from the generic QoS Policy Action Set command            |
+---------+-----------------------------------------------------------------+
