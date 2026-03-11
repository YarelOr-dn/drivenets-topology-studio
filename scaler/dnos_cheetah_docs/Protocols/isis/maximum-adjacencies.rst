protocols isis maximum-adjacencies
----------------------------------

**Minimum user role:** operator

You can control the number of IS-IS adjacencies allowed. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. The thresholds are for generating system-events only. There is no strict limit on the number of IS-IS adjacencies that can be formed.

To limit the number of IS-IS adjacencies:

**Command syntax: maximum-adjacencies [max-adjacencies]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols isis

**Note**

- There is no strict limitation on the number of IS-IS adjacencies that can be formed.

- When a threshold is crossed (max-adjacencies or threshold), a single system-event notification is generated.

- When a threshold is cleared (max-adjacencies or threshold), a single system-event notification is generated.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| max-adjacencies | The maximum number of IS-IS adjacencies allowed. When this threshold is crossed, | 1-65535 | 50      |
|                 | a system-event notification is generated every 30 seconds until the number of    |         |         |
|                 | adjacencies drops below the maximum.                                             |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+
| threshold       | A percentage (%) of max-adjacencies to give you advance notice that the number   | 1-100   | 75      |
|                 | of adjacencies is reaching the maximum level. When this threshold is crossed, a  |         |         |
|                 | single system-event notification is generated.                                   |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# maximum-adjacencies 50 threshold 80

In the above example, the maximum number of IS-IS adjacencies is set to 50 and the threshold is set to 80%. This means that when the number of adjacencies reaches 40, a system-event notification will be generated that the 80% threshold has been crossed. If you do nothing, you will not receive another notification until the number of adjacencies reaches 50.


**Removing Configuration**

To revert to the default values:
::

    dnRouter(cfg-protocols-isis)# no maximum-adjacencies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
