services twamp vrf client-list type
-----------------------------------

**Minimum user role:** operator

This command defines whether the configured client-list (see "services twamp client-list") is a white list or a black list.

To configure the client list type:

**Command syntax: client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- services twamp vrf

**Note**

- Client lists with type "allow" must contain at least one network-address.

**Parameter table**

+-----------+------------------------------------------------+-----------+---------+
| Parameter | Description                                    | Range     | Default |
+===========+================================================+===========+=========+
| list-type | Defines the type of the configured client list | | allow   | deny    |
|           |                                                | | deny    |         |
+-----------+------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp vrf default
    dnRouter(cfg-srv-twamp-vrf)# client-list type allow


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-twamp-vrf)# no client-list type

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 6.0     | Command introduced        |
+---------+---------------------------+
| 16.2    | Moved under VRF hierarchy |
+---------+---------------------------+
