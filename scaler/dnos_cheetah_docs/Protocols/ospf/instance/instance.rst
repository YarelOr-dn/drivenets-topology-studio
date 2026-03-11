protocols ospf instance
-----------------------

**Minimum user role:** operator

OSPF instances allow you to set different OSPF configuration per instance, using the same router-id and loopback interfaces.
However, each instance must be configured with a different administrative-distance, and non-loopback interfaces. Each instance operates as  a separate IGP domain. 
However, connectivity between instances can only be achieved using MPLS with BGP-LU, as native IP leaking between instances is impossible.
You can configure up to 5 OSPF instances, each with a unique name.

To configure an OSPF instance:

**Command syntax: instance [ospf-instance-name]**

**Command mode:** config

**Hierarchies**

- protocols ospf

**Note**

- The OSPF router-id is identical in all ospf instances.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter          | Description                                                                      | Range            | Default |
+====================+==================================================================================+==================+=========+
| ospf-instance-name | The OSPFv2 instance name identifies the specific OSPF protocol instance. The     | | string         | \-      |
|                    | name cannot be changed. If you need to change it, you must delete the OSPF       | | length 1-255   |         |
|                    | protocol instance using the no instance [ospf-instance-name] command and         |                  |         |
|                    | reconfigure with a different name.                                               |                  |         |
+--------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_2
    dnRouter(cfg-protocols-ospf-inst)#


**Removing Configuration**

To remove all OSPF protocol instances:
::

    dnRouter(cfg-protocols-ospf)# no instance

To remove a specific OSPF protocol instance:
::

    dnRouter(cfg-protocols-ospf)# no instance INSTANCE_1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
