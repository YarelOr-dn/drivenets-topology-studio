protocols segment-routing mpls backup-path-install
--------------------------------------------------

**Minimum user role:** operator

When a backup-install-path is set for a given policy, DNOS picks the next (lower) preference valid candidate path as the backup for the active candidate path.
The backup path is installed to a FIB to provide a sub 50 msec failover upon active path failure.

To enable end to end protecition and support backup path installation:


**Command syntax: backup-path-install [backup-path-install]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls

**Note**
- For policy to have a backup path , at least two paths needs to be configured for policy (no commit validation required)
- Each path , both active and backup is fully defined by its path settings. There is no implicit disjoint constraint between them.


**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter           | Description                                                                      | Range        | Default  |
+=====================+==================================================================================+==============+==========+
| backup-path-install | Utilize lower preference candidate path as policy end to end back path installed | | enabled    | disabled |
|                     | to RIB and FIB                                                                   | | disabled   |          |
+---------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# backup-path-install enabled


**Removing Configuration**

To return the backup-path-install setting to its default value:
::

    dnRouter(cfg-protocols-igp-mpls)# no backup-path-install

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
