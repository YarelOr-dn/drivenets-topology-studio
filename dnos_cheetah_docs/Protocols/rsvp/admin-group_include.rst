protocols rsvp admin-group
--------------------------

**Minimum user role:** operator

After configuring the administrative group, you can either exclude, include, or ignore links of that color in the traffic engineering database:

- If you exclude a specific color, all segments with an administrative group of that color are excluded from CSPF path selection.

- If you include a specific color, only those segments with the appropriate color are selected.

- If you neither exclude nor include the color, the metrics associated with the administrative groups and applied on the specific segments determine the path cost for that segment.

The LSP with the lowest total path cost is selected into the traffic engineering database. By default, admin-group constraints are ignored in path calculation.
To define global link include admin-group attributes for all tunnels:

**Command syntax: admin-group [include-type] [admin-group-name]** [, admin-group-name, admin-group-name]

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Note**
- You cannot set the same admin-group-name in both an exclude and include constraint.

.. -  default system behavior is to ignore admin-groups constraints in path calculation

.. -  can either set include-all or include-any or include-strict admin-group list

.. -  cannot be set together with admin-group exclude

.. -  'no admin-group include-all [admin-group-name]', 'no admin-group include-strict [admin-group-name]' - remove the specified admin-group from the admin-groups list

.. -  'no admin-group include-any', 'no admin-group include-strict' - remove all admin-groups from the admin-groups list

**Parameter table**

+------------------+------------------------------------+--------------------+---------+
| Parameter        | Description                        | Range              | Default |
+==================+====================================+====================+=========+
| include-type     | rsvp global admin groups           | | include-all      | \-      |
|                  |                                    | | include-any      |         |
|                  |                                    | | include-strict   |         |
+------------------+------------------------------------+--------------------+---------+
| admin-group-name | Admin groups (separated by commas) | | string           | \-      |
|                  |                                    | | length 1-255     |         |
+------------------+------------------------------------+--------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group include-all RED, GREEN

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# admin-group include-strict BLUE


**Removing Configuration**

To remove a specific admin-group-name from the constraint:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group include-any RED

To remove all admin-groups from the admin group list:
::

    dnRouter(cfg-protocols-rsvp)# no admin-group include-all

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
