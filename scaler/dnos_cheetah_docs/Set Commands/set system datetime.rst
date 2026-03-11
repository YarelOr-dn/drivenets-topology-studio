set system datetime
-------------------

**Minimum user role:** viewer

To manually set the clock to the correct time, use the set system datetime command. You can set the current date and the time of day, as follows:

**Command syntax: set system datetime** [datetime]

**Command mode:** operational

**Note**

- Make sure that system timing mode is set to "manual" to disable the NTP functionality. See "system timing-mode".

..
	**Internal Note**

	- Validation:

	If system timing-mode is set to "ntp", set system datetime command is rejected and the following message is presented:

	"Timing mode is set to NTP, local time setting is unavailable".

**Parameter table**

+---------------+-------------------------------------------------------------------------------------+------------------------------+
|               |                                                                                     |                              |
| Parameter     | Description                                                                         | Range                        |
+===============+=====================================================================================+==============================+
|               |                                                                                     |                              |
| datetime      | Sets the system local time of day. You can optionally   set a millisecond value.    | dd-mm-yyyyThh:mm:ss[.sss]    |
+---------------+-------------------------------------------------------------------------------------+------------------------------+

**Example**
::

	dnRouter# set system datetime 2017-11-13T17:59:59

	dnRouter# set system datetime 2017-11-13T17:59:59.999
	Timing mode is set to NTP, manual time setting is unavailable.

.. **Help line:** Set manual system datetime

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
|             |                                              |
| 5.1.0       | Command introduced                           |
+-------------+----------------------------------------------+
|             |                                              |
| 6.0         | Changed   from run command to set command    |
+-------------+----------------------------------------------+