protocols rsvp auto-mesh tunnel-template primary admin-group
------------------------------------------------------------

**Minimum user role:** operator

After configuring the administrative group, you can either exclude, include, or ignore links of that color in the traffic engineering database:

- If you exclude a specific color, all segments with an administrative group of that color are excluded from CSPF path selection.

- If you include a specific color, only those segments with the appropriate color are selected.

- If you neither exclude nor include the color, the metrics associated with the administrative groups and applied on the specific segments determine the path cost for that segment.

The LSP with the lowest total path cost is selected into the traffic engineering database. To define global link exclude admin-group attributes for all tunnels:

**Command syntax: admin-group [exclude-type] [admin-group-name]** [, admin-group-name, admin-group-name]

**Command mode:** config

**Hierarchies**

- protocols rsvp auto-mesh tunnel-template primary
- protocols rsvp tunnel primary
- protocols rsvp tunnel bypass primary
- protocols rsvp auto-bypass primary

**Note**
- You cannot set the same admin-group-name in both an exclude and include constraint.

- The tunnel admin-group exclude configuration overrides the global setting.

.. -  default system behavior is to ignore admin-groups constraints in path calculation

.. -  can either set exclude or exclude-all

.. -  cannot be set together with admin-group include

.. -  'no admin-group exclude [admin-group-name]'' - remove the specified admin-group from the admin-groups list

.. -  'no admin-group exclude', 'no admin-group exclude-all' - remove all admin-groups from the admin-groups list

**Parameter table**

+------------------+------------------------------------+--------------------+---------+
| Parameter        | Description                        | Range              | Default |
+==================+====================================+====================+=========+
| exclude-type     | exclude options                    | | exclude-any      | \-      |
|                  |                                    | | exclude-strict   |         |
+------------------+------------------------------------+--------------------+---------+
| admin-group-name | Admin groups (separated by commas) | | string           | \-      |
|                  |                                    | | length 1-255     |         |
+------------------+------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group exclude-any RED, GREEN

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group exclude-all


**Removing Configuration**

To remove a specific admin-group-name from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group exclude RED

To remove all admin-groups from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group exclude-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
