interfaces mixed-type
---------------------

**Minimum user role:** operator

You can use the following command to configure either a mixed bundle type or none if all members in the bundles are required to be of the same speed. If the bundles allows members of different speeds, the member with the lowest speed allowed in the bundle is determined by the mixed-type. Members of this speed will have weight 1 in the bundle hash resolution, while members of the higher speed will be assigned a weight relative of their speed vs. the speed of the lowest allowed bundle member. Only members with a speed equal to or lower than x10 of the lowest speed member can be added to a 10G-100G mixed-typed bundle, yet 400G members cannot. The total weight of a mixed-type bundle must be less or equal to 64.

+----------------+-------------------+---------------+-------------------------------+---------------------------------+
| Mixed Type     | Possible Members  | Maximal Speed | Maximal Speed Configuration   | Comments                        |
+================+===================+===============+===============================+=================================+
| none           | 10G               | 640Gps        | 64x10G                        |                                 |
+----------------+-------------------+---------------+-------------------------------+---------------------------------+
| none           | 100G              | 6.4Tps        | 64x100G                       |                                 |
+----------------+-------------------+---------------+-------------------------------+---------------------------------+
| none           | 400G              | 6.4Tps        | 16x400G                       | maximum bundle speed limitation |
+----------------+-------------------+---------------+-------------------------------+---------------------------------+
| 10G-100G       | 10G, 100G         | 640Gps        | 64x10G, 54x10G+1x100G, ...    |                                 |
+----------------+-------------------+---------------+-------------------------------+---------------------------------+
| 100G-400G      | 100G, 400G        | 6.4Tps        | 64x100G, 60x100G+1x400G, ...  |                                 |
+----------------+-------------------+---------------+-------------------------------+---------------------------------+

**Command syntax: mixed-type [mixed-type]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to bundle interfaces.

**Parameter table**

+------------+--------------------------------------------------------------+---------------+---------+
| Parameter  | Description                                                  | Range         | Default |
+============+==============================================================+===============+=========+
| mixed-type | Configure which member interfaces are allowed in the bundle. | | none        | none    |
|            |                                                              | | 10G-100G    |         |
|            |                                                              | | 100G-400G   |         |
|            |                                                              | | 1G-10G      |         |
+------------+--------------------------------------------------------------+---------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# mixed-bundle 100G-400G


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1)# no mixed-bundle

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
