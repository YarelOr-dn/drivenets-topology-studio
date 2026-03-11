show dnos-internal remote-sync qos status
-----------------------------------------

**Minimum user role:** viewer

To display qos sync status between local ncp and remote ncp's:

**Command syntax: show dnos-internal remote-sync qos status**

**Command mode:** operation

**Example**
::

    dnRouter# show dnos-internal remote-sync qos status

    Remote ncps status:

    | NCP id   | Status           |
    |----------+------------------|
    | 1        | waiting-for-sync |
    | 2        | config-applied   |
    | 3        | waiting-for-sync |

.. **Help line:** Display information about qos sync for all remote ncps

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 19.10       | Command introduced    |
+-------------+-----------------------+
