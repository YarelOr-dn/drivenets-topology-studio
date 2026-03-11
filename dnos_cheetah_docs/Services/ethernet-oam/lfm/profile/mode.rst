services ethernet-oam link-fault-management profile mode
--------------------------------------------------------

**Minimum user role:** operator

To set the OAM mode for the specified profile:

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management profile

**Parameter table**

+-----------+-------------+-------------+---------+
| Parameter | Description | Range       | Default |
+===========+=============+=============+=========+
| mode      | OAM mode    | | passive   | active  |
|           |             | | active    |         |
+-----------+-------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# mode active

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# mode passive


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-eoam-lfm-profile)# no mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
