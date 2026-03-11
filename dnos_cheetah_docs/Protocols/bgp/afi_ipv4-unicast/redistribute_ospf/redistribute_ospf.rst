protocols bgp address-family ipv4-unicast redistribute ospf instance
--------------------------------------------------------------------

**Minimum user role:** operator

You can set the router to advertise the OSPF routes. 

**Command syntax: redistribute ospf instance [ospf-instance-name]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast

**Note**

- This command is only applicable to unicast sub-address-families.

- Can set multiple policies. If multiple policies are set the policies are evaluated one after the other according to the user input order.

- You can specify the OSPFv2 instance you want to configure.

**Parameter table**

+--------------------+--------------------+------------------+---------+
| Parameter          | Description        | Range            | Default |
+====================+====================+==================+=========+
| ospf-instance-name | ospf instance name | | string         | \-      |
|                    |                    | | length 1-255   |         |
+--------------------+--------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute ospf instance MY_OSPF_INSTANCE
    dnRouter(cfg-bgp-afi-rdst-ospf)#


**Removing Configuration**

To stop redistribution of all route types:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute

To stop redistribution of OSPFv2 instance routes:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute ospf INSTANCE_NAME

**Command History**

+---------+----------------------------------------------------------------+
| Release | Modification                                                   |
+=========+================================================================+
| 6.0     | Command introduced                                             |
+---------+----------------------------------------------------------------+
| 18.1    | Added support for multiple policies attachments                |
+---------+----------------------------------------------------------------+
| 18.1    | Command modified to support per OSPFv2 instance redistribution |
+---------+----------------------------------------------------------------+
