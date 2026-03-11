services mpls-oam profile admin-state
-------------------------------------

**Minimum user role:** operator


Setting the administrative state of the MPLS-OAM profile determines whether or not periodic LSP ping packets will be sent along the LSP.

To enable or disable the periodic LSP ping probe:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services mpls-oam profile

**Parameter table**

+-------------+------------------------------+--------------+----------+
| Parameter   | Description                  | Range        | Default  |
+=============+==============================+==============+==========+
| admin-state | profile administrative state | | enabled    | disabled |
|             |                              | | disabled   |          |
+-------------+------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# admin-state active

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# mpls-oam
    dnRouter(cfg-srv-mpls-oam)# profile P_1
    dnRouter(cfg-mpls-oam-profile)# admin-state passive


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-mpls-oam-profile)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
