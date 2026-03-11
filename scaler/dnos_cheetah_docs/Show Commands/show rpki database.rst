show rpki database 
------------------

**Minimum user role:** viewer

This command displays the BGP RPKI validation database.

To display the database:

**Command syntax: show rpki database** {[server-address] [address-family] | as-number [as-number] | prefix [prefix]}

**Command mode:** operational

**Parameter table**

+----------------+-----------------------------------------------+----------------+---------+
| Parameter      | Description                                   | Range          | Default |
+================+===============================================+================+=========+
| server-address | RPKI cache server IP address or hostname      | A.B.C.D        | \-      |
|                |                                               | xx:xx::xx:xx/x |         |
+----------------+-----------------------------------------------+----------------+---------+
| address-family | Use to filter the results by address-family   | IPv4           | \-      |
|                |                                               | IPv6           |         |
+----------------+-----------------------------------------------+----------------+---------+
| as-number      | Lookup by AS number in the database           | 0..4294967295  | \-      |
|                |                                               |                |         |
+----------------+-----------------------------------------------+----------------+---------+
| prefix         | Lookup for a maching prefix in the database   | A.B.C.D/M      | \-      |
|                |                                               | xx:xx::xx:xx/x |         |
+----------------+-----------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# show rpki database

    486 BGP RPKI records

    | Network          | Max Length | Origin-AS | Advertising Server |
    +------------------+------------+-----------+--------------------+
    | 24.232.0.0/16    | 32         | 400071    | 10.0.0.1:8282      |
    | 31.3.8.0/21      | 21         | 400072    | 10.0.0.2:343       |
    ...

    
    dnRouter# show rpki database ipv6

    12 BGP RPKI records

    | Network          | Max Length | Origin-AS | Advertising Server |
    +------------------+------------+-----------+--------------------+
    | 2001:608::/32    | 32         | 400071    | 10.0.0.1:8282      |
    | 2001:610::/32    | 48         | 68931     | 10.0.0.1:8282      |
    ...


    dnRouter# show rpki database as-number 33145

    | Network          | Max Length | Origin-AS | Advertising Server |
    +------------------+------------+-----------+--------------------+
    | 11.0.0.0/16      | 24         | 33145     | 10.0.0.1:8282      |
    | 11.1.0.0/16      | 24         | 33145     | 10.0.0.1:8282      |
    ...


    dnRouter# show rpki database prefix 11.0.0.0/24

    | Network          | Max Length | Origin-AS | Advertising Server |
    +------------------+------------+-----------+--------------------+
    | 0.0.0.0/1        | 32         | 123456    | 100.64.7.222:8282  |
    | 0.0.0.0/1        | 32         | 654321    | 100.64.7.222:8282  |
    | 10.0.0.0/7       | 24         | 123456    | 100.64.7.222:8282  |
    | 11.0.0.0/16      | 24         | 33145     | 100.64.7.222:8282  |


    dnRouter# show rpki database 10.0.0.1

    63 BGP RPKI records

    | Network          | Max Length | Origin-AS | Advertising Server |
    +------------------+------------+-----------+--------------------+
    | 11.0.0.0/16      | 24         | 33145     | 10.0.0.1:8282      |
    | 11.1.0.0/16      | 24         | 33145     | 10.0.0.1:8282      |
    | 24.232.0.0/16    | 32         | 400071    | 10.0.0.1:8282      |
    | 2001:608::/32    | 32         | 400071    | 10.0.0.1:8282      |
    | 2001:610::/32    | 48         | 68931     | 10.0.0.1:8282      |
    ...


    dnRouter# show rpki database 10.0.0.1 ipv4

    19 BGP RPKI records

    | Network          | Max Length | Origin-AS | Advertising Server |
    +------------------+------------+-----------+--------------------+
    | 11.0.0.0/16      | 24         | 33145     | 10.0.0.1:8282      |
    | 11.1.0.0/16      | 24         | 33145     | 10.0.0.1:8282      |
    | 24.232.0.0/16    | 32         | 400071    | 10.0.0.1:8282      |
    ...

.. **Help line:** show BGP RPKI validation database.

**Command History**

+---------+--------------------------------------------------------+
| Release | Modification                                           |
+=========+========================================================+
| 15.1    | Command introduced                                     |
+---------+--------------------------------------------------------+
| 15.2    | Added new server-address, as-number and prefix filters |
+---------+--------------------------------------------------------+

