interfaces ipv4-default-gateway
-------------------------------

**Minimum user role:** operator

This command assigns an IPv4 default gateway address for the interface being configured.

To configure the IPv4 default gateway address for an interface, use the following command:

**Command syntax: ipv4-default-gateway [default-gateway]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - ipmi

- ipmi can only be configured with default gateway IPv4 address in standalone systems.

**Parameter table**

+-----------------+----------------------------------------------------+---------+---------+
| Parameter       | Description                                        | Range   | Default |
+=================+====================================================+=========+=========+
| default-gateway | The IPv4 default gateway address on the interface. | A.B.C.D | 0.0.0.0 |
+-----------------+----------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ipmi-ncc-0/0
    dnRouter(cfg-if-ipmi-ncc-0/0)# ipv4-default-gateway 10.20.30.40
    dnRouter(cfg-if-ipmi-ncc-0/0)# no ipv4-address


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-if-ipmi-ncc-0/0)# no ipv4-default-gateway

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
