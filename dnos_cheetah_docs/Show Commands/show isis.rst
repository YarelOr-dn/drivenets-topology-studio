show isis
----------

**Minimum user role:** viewer

The show isis command displays information on a variety of IS-IS information and configuration. You can filter the information by parameter and/or by interface name. When filtering by parameter only, the system displays the requested parameter for all interfaces. When filtering by interface name, the information is further filtered to display the parameter configuration for the requested interface only.



**Command syntax: show isis** instance [isis-instance-name]

**Command mode:** operational



.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when now specified, display information from all isis instances



**Example**
::

    dnRouter# show isis

    TE Router ID    : 100.117.117.117
    TE Ipv6 Router ID    : 1111::7777
    Graceful-Restart: enabled
      grace-interval: 120 secs
    Graceful-Restart helper-mode: enabled
    NSR: disabled
    Number of areas : 1
    ISIS routes max/threshold/current: 32000/75/11
    ISIS adjacencies max/threshold/current: 50/75/2
    Instance Devtest_AP:
      Admin state     : enabled
      System Id       : 0000.1717.1717
      Area-id(s)      : 47.0000
      level-1 TE Status         : disable
      level-2 TE Status         : enable
      Dynamic Hostname          : R17-Core
      Administrative Distance   : 102
      ISIS Levels: level-2
      Segment-Routing MPLS:
        Ipv4: enabled
        Ipv6: enabled
        SRLB: 8000 - 15999
        SRGB: 16000 - 23999
      Lsp-flood-reduction: enabled
      Ignore-attached-bit: enabled
      Topologies:
        IPv4 Unicast
        IPv6 Unicast
      Level-2:
        IPv4-Unicast topology computation:
          Last run elapsed  : 00:00:03 ago
          Last run duration : 180 usec
          Run count         : 73877
          Delay             : 0 msec
          Min holdtime      : 5 msec
          Max holdtime      : 5000 msec
          Next schedule     : N/A
        Shortcuts IPv4-Unitcast topology computation:
          Last run elapsed  : 00:00:03 ago
          Last run duration : 234 usec
          Run count         : 73882
          Delay             : 0 msec
          Min holdtime      : 5 msec
          Max holdtime      : 5000 msec
          Next schedule     : N/A
        IPv6-Unicast topology computation:
          Last run elapsed  : 00:00:03 ago
          Last run duration : 120 usec
          Run count         : 73880
          Delay             : 0 msec
          Min holdtime      : 5 msec
          Max holdtime      : 5000 msec
          Next schedule     : N/A
        Max-metric-value: 16777214
        Overload on-startup: enabled
          interval: 600
          wait-for-bgp bgp-delay: 60
          advertisement-type: overload-bit
        Overload-bit: off
        Max-metric: off
        LSP Throttle:
          Delay             : 50 msec
          Min holdtime      : 200 msec
          Max holdtime      : 5000 msec
          Next schedule     : 00:14:03.773
        LSP Lifetime                : 1200 sec
        LSP Refresh Interval        : 900 sec
        LSP Interval                : 0 msec
        Administrative Distance     : 115
        Log Adjacency Changes       : enabled
        LSP MTU                     : 1497
        Distribute BGP Link State   : disabled
        MPLS Traffic Engineering Level-1   : off
        MPLS Traffic Engineering Level-2   : on
        LFA:
          IPv4                : enabled, remote-lfa
          IPv6                : enabled
          IPv4-multicast      : disabled
        TI-LFA:
          IPv4                : disabled, link-protection, maximum-labels 3
          IPv6                : disabled, link-protection, maximum-labels 3

.. **Help line:**

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 9.0     | Command introduced                            |
+---------+-----------------------------------------------+
| 13.0    | Added support for overload-bit                |
+---------+-----------------------------------------------+
| 15.0    | Added support for the display of LSP interval |
+---------+-----------------------------------------------+
| 16.2    | Added support for IPv4-multicast              |
+---------+-----------------------------------------------+
| 17.0    | Added support for NSR                         |
+---------+-----------------------------------------------+
| 17.1    | Extended LFA mode display to remote-lfa       |
+---------+-----------------------------------------------+
