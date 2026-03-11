protocols ospf instance ti-fast-reroute protection-mode
-------------------------------------------------------

**Minimum user role:** operator

Sets the required ti-fast-reroute protection.
For link protection only link protection lfa will be calculated. If none found, no LFA will be provided.
For node protection, the node protecting LFA paths will be found first. If none found, a link protection LFA path will be calculated.

**Command syntax: protection-mode [protection-mode]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance ti-fast-reroute

**Note**

- Node protection calculation has higher calculation complexity and may risk that OSPF will find LFA path in the required time.

**Parameter table**

+-----------------+------------------------------------+----------+---------+
| Parameter       | Description                        | Range    | Default |
+=================+====================================+==========+=========+
| protection-mode | the desired ti-lfa protection type | | link   | link    |
|                 |                                    | | node   |         |
+-----------------+------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# ti-fast-reroute
    dnRouter(cfg-protocols-ospf-ti-frr)# protection-mode node


**Removing Configuration**

To revert protection-mode to the default value:
::

    dnRouter(cfg-protocols-ospf-ti-frr)# no protection-mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
