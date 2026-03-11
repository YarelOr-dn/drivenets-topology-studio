interfaces admin-state
----------------------

**Minimum user role:** operator

Sets the administrative state of the interface. When a physical or bundle interface is disabled, the interface's laser signal is shut down. When a sub-interface is disabled, the interface IPv4/IPv6 address is unreachable and traffic cannot be forwarded via this interface (in either direction). When a bundle interface is disabled, the admin-state of the bundle members remains "enabled" and their operational state changes to "down".

To enable/disable an interface, set the admin-state parameter using the following command:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan
  - Loopback
  - mgmt0
  - Control
  - Fabric
  - Console
  - IPMI
  - Physical smartNIC (SGE)
  - L2-NAT
  - IPSEC
  - IRB
  - ICE

- All NNI/UNI physical interfaces are initialized with admin-state Disabled.

- Mgmt and control interfaces are initialized with admin-state Enabled.

- All logical interfaces (Loopback, sub-physical, bundle, sub-bundle, l2-nat, ipsec) are initialized with admin-state Enabled.

**Parameter table**

+-------------+-------------------------------------------------+--------------+-----------------------------------------+
| Parameter   | Description                                     | Range        | Default                                 |
+=============+=================================================+==============+=========================================+
| admin-state | Sets the administrative state of the interface. | | enabled    | | -Enabled for logical/ctrl/mgmt/ice    |
|             |                                                 | | disabled   | | -Disabled for physical                |
+-------------+-------------------------------------------------+--------------+-----------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# admin-state disabled

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# admin-state enabled

    dnRouter(cfg-if)# bundle-1.4
    dnRouter(cfg-if-bundle-1.4)# admin-state enabled

    dnRouter(cfg-if)# ctrl-ncp-0/0
    dnRouter(cfg-if-ctrl-ncp-0/0)# admin-state enabled

    dnRouter(cfg-if)# ice0
    dnRouter(cfg-if-ice0)# admin-state disabled
    Notice: Continuing with the commit will cause the following:
    The following commit will disable the Intra Cluster Exchange interface. Proceeding with this commit will disable the communication channel between NCPs and may cause loss of synchronization and traffic.
    Enter yes to continue with commit, no to abort commit (yes/no) [no]


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-bundle-1.4)# no admin-state

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces; applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 10.0    | Changed the default admin-state for physical interfaces            |
+---------+--------------------------------------------------------------------+
| 17.0    | Added support for NCM control ports                                |
+---------+--------------------------------------------------------------------+
| 19.10   | Added support for ICE interface                                    |
+---------+--------------------------------------------------------------------+
