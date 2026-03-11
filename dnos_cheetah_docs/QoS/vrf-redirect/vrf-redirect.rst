qos vrf-redirect
----------------

**Minimum user role:** operator

DNOS supports three types of VRF redirect schemes: static routes redirecting to another VRF, flowspec redirection and ABF redirection to another VRF.
VRF QoS adds two shapers, the vrf-redirect-0 shaper and the vrf-redirect-1 shaper.
vrf-redirect-0 ensures that the maximum rate of static-route redirected traffic is limited to the specified shaper rate.
vrf-redirect-1 ensures that the maximum rate of flowpsec redirect and ABF redirect traffic sent is limited to the specified shaper rate.

**Command syntax: vrf-redirect**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# vrf-redirect
    dnRouter(cfg-qos-vrfr)#


**Removing Configuration**

To revert the vrf-redirect parameters to the default value:
::

    dnRouter(cfg-qos)# no vrf-redirect

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
