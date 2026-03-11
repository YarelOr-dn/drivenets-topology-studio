system ntp server iburst
------------------------

**Minimum user role:** operator

When the iburst parameter is set, a series of NTP packets are sent instead of a single packet within the initial synchronization interval to a achieve faster initial synchronization. To configure NTP to start synchronisation in burst mode.

**Command syntax: iburst**

**Command mode:** configuration

**Hierarchies**

- system ntp


**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 200.24.34.1 vrf default
    dnRouter(cfg-system-ntp-server)# iburst

    dnRouter(cfg-system-ntp)# server 2001:ab12::1 vrf mgmt0
    dnRouter(cfg-system-ntp-server)# iburst

**Removing Configuration**

To remove iburst from the NTP configuration:
::

    dnRouter(cfg-system-ntp-server)# no iburst


.. **Help line:**


**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.2      | Command introduced    |
+-----------+-----------------------+
