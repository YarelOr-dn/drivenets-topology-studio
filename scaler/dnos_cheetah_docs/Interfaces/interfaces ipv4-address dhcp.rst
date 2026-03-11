interfaces ipv4-address dhcp
----------------------------

**Minimum user role:** operator

To dynamically allocate an IPv4 address for an logical management interface, use the following command:

**Command syntax: ipv4-address dhcp**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - mgmt0
  - ipmi

- ipmi can only be configured with default gateway IPv4 address in standalone systems.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# mgmt0
    dnRouter(cfg-if-mgmt0)# ipv4-address dhcp


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-if-mgmt0)# no ipv4-address

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 11.0    | Command introduced                     |
+---------+----------------------------------------+
| 16.2    | Management physical interfaces removed |
+---------+----------------------------------------+
| 19.2    | Add support for ipmi                   |
+---------+----------------------------------------+
