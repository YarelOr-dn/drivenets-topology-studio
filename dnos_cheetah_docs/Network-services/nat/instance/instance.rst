network-services nat instance
-----------------------------

**Minimum user role:** operator

To configure a NAT instance:

**Command syntax: instance [instance-name]**

**Command mode:** config

**Hierarchies**

- network-services nat

**Note**

- The legal string length is 1..255 characters.

- Illegal characters include any whitespace, non-ascii, and the following special characters (separated by commas): #,!,',”,\

**Parameter table**

+---------------+------------------------------------------------------+------------------+---------+
| Parameter     | Description                                          | Range            | Default |
+===============+======================================================+==================+=========+
| instance-name | Reference to the configured name of the nat instance | | string         | \-      |
|               |                                                      | | length 1-255   |         |
+---------------+------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# nat
    dnRouter(cfg-netsrv-nat)# instance tennant_customer_nat_1
    dnRouter(cfg-netsrv-nat-inst)#


**Removing Configuration**

To remove the specified NAT instance:
::

    dnRouter(cfg-netsrv-nat)# no instance tennant_customer_nat_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
