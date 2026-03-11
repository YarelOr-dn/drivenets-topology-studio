show system snmp qos
--------------------

**Minimum user role:** viewer

To show the system snmp qos information:

**Command syntax: show system snmp qos** interface [interface-name]

**Command mode:** operational

**Note**

- The list can be filtered to show the configuration and provision indexes, relevant for a particular interface.

- If a Traffic Class is configured but not assigned to a rule, it will not be listed.


**Parameter table**

+----------------+------------------------------+----------------------------------------------+---------------+
|    Parameter   | Description                  | Range                                        | Default       |
+================+==============================+==============================================+===============+
| Interface-name | Filters the displayed        | ge<interface speed>-<A>/<B>/<C>,             | \-            |
|                | information by interface     | ge<interface speed>-<A>/<B>/<C>.<sub-if-id>, |               |
|                |                              | bundle-<bundle id>                           |               |
+----------------+------------------------------+----------------------------------------------+---------------+


**Example**
::

    dnRouter# show system snmp qos

    Policies

    +-------------------+-------------------+-------------------+------------------+
    | Policy            | Rule              | Traffic Class     | dnQoSConfigIndex |
    +-------------------+-------------------+-------------------+------------------+
    | My-Ingress-Policy |                   |                   |              442 |
    |                   | 1                 |                   |           123211 |
    |                   |                   | My-Qu-1           |           333211 |
    |                   | 2                 |                   |           123212 |
    |                   |                   | My-Qu-2           |           333212 |
    |                   | default           |                   |           123223 |
    | My-Egress-Policy  |                   |                   |              443 |
    |                   | 1                 |                   |           126211 |
    |                   |                   | My-Qt-1           |           333212 |
    |                   | 2                 |                   |           126213 |
    |                   |                   | My-Qt-2           |           333212 |
    |                   | default           |                   |           126223 |
    | My-Ingress-Def    |                   |                   |              444 |
    |                   | default           |                   |           123227 |

    Attached Interfaces

    +-------------------+-------------------+------------------+
    | Interface         | Direction         | dnQoSPolicyIndex |
    +-------------------+-------------------+------------------+
    | bundle-1          | in                |        656354344 |
    | bundle-1          | out               |        265635444 |
    | bundle-2          | in                |        656354345 |
    | bundle-2          | out               |        265635445 |
    | bundle-3          | in                |        656354346 |
    | bundle-3          | out               |        265635446 |


    dnRouter# show system snmp qos interface bundle-2

    Policies

    +-------------------+-------------------+-------------------+------------------+
    | Policy            | Rule              | Traffic Class     | dnQoSConfigIndex |
    +-------------------+-------------------+-------------------+------------------+
    | My-Ingress-Policy |                   |                   |              442 |
    |                   | 1                 |                   |           123211 |
    |                   |                   | My-Qu-1           |           333211 |
    |                   | 2                 |                   |           123212 |
    |                   |                   | My-Qu-2           |           333212 |
    |                   | default           |                   |           123223 |
    | My-Egress-Policy  |                   |                   |              443 |
    |                   | 1                 |                   |           126211 |
    |                   |                   | My-Qt-1           |           333212 |
    |                   | 2                 |                   |           126213 |
    |                   |                   | My-Qt-2           |           333212 |
    |                   | default           |                   |           126223 |

    Attached Interfaces

    +-------------------+-------------------+------------------+
    | Interface         | Direction         | dnQoSPolicyIndex |
    +-------------------+-------------------+------------------+
    | bundle-2          | in                |        656354344 |
    | bundle-2          | out               |        265635444 |


.. **Help line:** show system snmp qos

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+---------+----------------------------------+
| 15.0    | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for sub-interfaces |
+---------+----------------------------------+
