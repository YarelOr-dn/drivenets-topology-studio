interfaces bundle
------------------

**Minimum user role:** operator

The bundle interfaces in DNOS provide datapath connectivity between NCPs. The bundle interfaces are the customer/core interfaces that the user is provisioning. Each bundle will include a member of each of the NCPs, so that all the NCPs are able to send traffic from any ingress interface to any egress interface. Up to 128 enabled bundle interfaces with up to 64 members per bundle can be created. To create a LAG (bundle):

#. Create a bundle interface, using this command.
#. Bind an interface to the bundle using the "interfaces bundle-id" command.

The parameters that you can optionally configure on the bundle interface are the same parameters that you can configure on any interface. If you do not set these parameters, the default values will be assumed. If you configure a parameter on an existing bundle-id, the value of that parameter will be changed. If the bundle-id does not exist, it will be created. The parameters set on the bundle override the parameters of the interface members.

**Command syntax: bundle-<bundle-id>**

**Command mode:** config

**Hierarchies**

- interfaces

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+------------+
|               |                                                                                                                                                                                                                            |             |            |
| Parameter     | Description                                                                                                                                                                                                                | Range       | Bundle     |
+===============+============================================================================================================================================================================================================================+=============+============+
|               |                                                                                                                                                                                                                            |             |            |
| bundle-id     | The bundle (LAG) identifier. If the ID does not exist, this will create a new bundle interface with the specific identifier. If the ID exists, you will enter the existing bundle interface's configuration mode.          | 1..65535    | \-         |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# bundle-1
	dnRouter(cfg-if-bundle-1)#


**Removing Configuration**

To delete a bundle interface:
::

	dnRouter(cfg-if)# no bundle-1


.. **Help line:** Configures bundle interface

**Command History**

+-------------+-------------------------------------------------------+
|             |                                                       |
| Release     | Modification                                          |
+=============+=======================================================+
|             |                                                       |
| 5.1.0       | Command introduced                                    |
+-------------+-------------------------------------------------------+
|             |                                                       |
| 6.0         | Changed syntax from interface to interfaces           |
|             |                                                       |
|             | Applied new hierarchy                                 |
+-------------+-------------------------------------------------------+
|             |                                                       |
| 7.0         | Removed the keyword "interface" from   the syntax.    |
+-------------+-------------------------------------------------------+