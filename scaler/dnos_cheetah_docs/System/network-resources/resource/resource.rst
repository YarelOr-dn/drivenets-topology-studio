system network-resources resource
---------------------------------

**Minimum user role:** operator

Command to create a new resource that can be consumed by the network-service on NCS

**Command syntax: resource [resource-name]**

**Command mode:** config

**Hierarchies**

- system network-resources

**Note**

- Legal string length is 1-255 characters.

- Illegal characters include any whitespace, non-ascii, and the following special characters (separated by commas): #,!,',”,\

**Parameter table**

+---------------+------------------------------------------------------------------------------+-----------------+---------+
| Parameter     | Description                                                                  | Range           | Default |
+===============+==============================================================================+=================+=========+
| resource-name | Reference to the configured name of the network function (resource) instance | | string        | \-      |
|               |                                                                              | | length 1-32   |         |
+---------------+------------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# network-resources
    dnRouter(cfg-system-netres)# resource nat-resource-1
    dnRouter(cfg-system-netres-res)#


**Removing Configuration**

To remove a specific network-resource
::

    dnRouter(cfg-system-netres)# no resource nat-resource-1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
