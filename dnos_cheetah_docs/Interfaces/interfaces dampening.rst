interfaces dampening
--------------------

**Minimum user role:** operator

In normal operation, the state of an interface is advertised whenever a change occurs. Dampening helps reduce the number of advertisements when the state of an interface changes frequently (flaps). Changing the interface dampening configuration clears the penalty value. The suppression state is also cleared for interfaces that are in a suppressed state. To configure dampening for an interface, enter the interface dampening configuration hierarchy:

**Command syntax: dampening**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to physical interfaces.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# dampening
    dnRouter(cfg-if-ge100-1/0/1-dampening)#


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-if-ge100-1/0/1)# no dampening

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
