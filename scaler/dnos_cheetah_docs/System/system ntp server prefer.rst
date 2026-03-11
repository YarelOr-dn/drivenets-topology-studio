system ntp server prefer
------------------------

**Minimum user role:** operator

To configure the remote NTP preferred server.

**Command syntax: prefer**

**Command mode:** configuration

**Hierarchies**

- system ntp

**Note**

- Only one server can be configured with the preferred configuration.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 200.24.34.1 vrf default
    dnRouter(cfg-system-ntp-server)# prefer

    dnRouter(cfg-system-ntp)# server 2001:ab12::1 vrf mgmt0
    dnRouter(cfg-system-ntp-server)#

**Removing Configuration**

To remove the prefer parameter from the NTP server:
::

    dnRouter(cfg-system-ntp-server)# no prefer


.. **Help line:**

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.2      | Command introduced    |
+-----------+-----------------------+
