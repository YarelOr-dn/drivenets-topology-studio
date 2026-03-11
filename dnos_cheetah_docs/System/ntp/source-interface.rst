system ntp source-interface
---------------------------

**Minimum user role:** admin

IP address of this interface is used as source IP address of all outingoing NTP messages

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- system ntp

**Parameter table**

+------------------+----------------------------------------------------------------+----------------------------------------------------------------------------------+--------------------------------------------+
| Parameter        | Description                                                    | Range                                                                            | Default                                    |
+==================+================================================================+==================================================================================+============================================+
| source-interface | The source interface whose IP address is used for NTP messages | Any interface in the default VRF with an IPv4/IPv6 address, except GRE tunnel    | system in-band-management source-interface |
|                  |                                                                | interfaces                                                                       |                                            |
+------------------+----------------------------------------------------------------+----------------------------------------------------------------------------------+--------------------------------------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# source-interface ge100-0/0/0


**Removing Configuration**

To revert source-interface to default:
::

    dnRouter(cfg-system-ntp)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
