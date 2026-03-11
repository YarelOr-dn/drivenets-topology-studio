protocols bgp maximum-sessions threshold
----------------------------------------

**Minimum user role:** operator

You can control the maximum number of concurrent BGP sessions by setting thresholds to generate system event notifications. Only established sessions are counted. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary.

- This is a global setting where the thresholds apply to all BGP session types (iBGP and eBGP) and are for all BGP instances combined.

- The thresholds are for generating system-events only. There is no limitation for how many bgp neighbors/groups user can configure. A session will open for every configured peer.

To configure thresholds for BGP sessions:

**Command syntax: bgp maximum-sessions [maximum] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- When the number of sessions drops below a threshold, a system-event notification is generated.

- In the above example, the maximum number of sessions is set to 600 and the threshold is set to 70%. This means that when the number of sessions reaches 420 (600x70%), a system-event notification will be generated that the 70% threshold has been crossed. If you do nothing, you will not receive another notification until the number of sessions reaches 600.

**Parameter table**

+-----------+---------------------------------------------------------+--------+---------+
| Parameter | Description                                             | Range  | Default |
+===========+=========================================================+========+=========+
| maximum   | maximum session scale, covers all types of bgp sessions | 1-5000 | 500     |
+-----------+---------------------------------------------------------+--------+---------+
| threshold | threshold as a percentage of system maximum bgp session | 1-100  | 75      |
+-----------+---------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp maximum-sessions 600 threshold 70


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols)# no bgp maximum-sessions

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
