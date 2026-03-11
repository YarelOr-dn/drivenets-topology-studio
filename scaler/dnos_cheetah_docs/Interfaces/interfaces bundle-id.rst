interfaces bundle-id
--------------------

**Minimum user role:** operator

When binding a physical interface to a bundle interface, the physical interface functions as a member of the bundle. You can attach an interface only to an existing bundle.

Only physical interfaces (geX-<f>/<n>/<p>) are allowed.

A bundle can contain only members of the same type (i.e. all members are 10 GbE). Alternatively, a bundle can contain a mixture of physical interfaces of different types/speeds (using the "interfaces mixed-type" command, so that it can have both 100G physical interfaces and 400G physical interfaces simultaneously). The bundle's aggregated maximum speed is 6400Gbps. Traffic is load-balanced over the bundle based on links speeds.

The interface can only be bound to one bundle interface and the bundle interface must exist prior to binding. If you try to bind an interface to a non existing bundle interface, an error is displayed.

Once attached, the physical interface functions as a member in the bundle.

To attach a physical interface to a bundle interface:

**Command syntax: bundle-id [bundle-id]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to physical interfaces.

- Binding a port to a bundle removes all logical configurations (e.g. IP address, MTU) from the physical interface (including any sub-interfaces configured under it). The member interface inherits the configuration from the bundle interface. Only logical configurations related to the member hardware are retained (e.g. led-flash, admin-state). Therefore, unbinding an interface from a bundle, the interface is configured with default parameters only. Any parameters previously configured on the physical interface are not retained.

- The member interface inherits the configuration from the bundle interface.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| bundle-id | Enter the LAG identifier that you have created (see step 1 above) to bind the    | 1-65535 | \-      |
|           | specific physical interface to the bundle.                                       |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# bundle-id 2

    dnRouter(cfg-if)# ge100-1/5/1
    dnRouter(cfg-if-ge100-1/5/1)# bundle-id 4


**Removing Configuration**

This command does not delete the bundle interface.

To unbind an interface from a bundle interface:
::

    dnRouter(cfg-if-ge100-1/5/1)# no bundle-id

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces, applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 7.0     | Removed the keyword "interface" from the syntax                    |
+---------+--------------------------------------------------------------------+
