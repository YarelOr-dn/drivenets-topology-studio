system aaa-server
-----------------

**Minimum user role:** admin

**Command mode:** config

You can configure all AAA functions (authentication, authorization, and accounting) in a single AAA TACACS+ server  with all its parameters, configure any function or any two functions on separate TACACS+ servers, or use a RADIUS server for authentication, and TACACS+ for authorization and accounting. 
The steps required for setting up a AAA server are:

1. Define users:
   * For local authentication, define users locally. See system login user.
   * For remote authentication, define users in the TACACS+/RADIUS server.

   **Note** - Authentication uses the PAP protocol.

2. Assign users with roles:
   * For local authentication, define roles locally. See system login user role.
   * For remote authentication, assign roles in the TACACS+ server (assign a viewer, operator, or administrator role (lowercase)).
      
   **Note** - If you already have roles defined in the TACACS+ server, please make sure that the roles are in lowercase. Make sure you have a user with techsupport role assigned to it. This user will have access directly to the NCR OS and have sudo permissions. **This user is for DriveNets use only, to provide technical support.**

   An authenticated user is granted access according to the user's assigned role (see system login user role). 
   You can expand the users' profiles by assigning users to groups and setting exceptions and limitations to the permissions granted by the role. 
   You can also set these exceptions and limitations on a user level, but group profiles are easier to manage.
   
   To create such profiles:

   -. Create groups in the TACACS+ server. Refer to the TACACS+ server documentation. 

     The following is an example of a group definition named "MyGroupA".
      ::

	group = MyGroupA {
        login = PAM
        service = TTY {
        default attribute = permit

   -. Add the following code to the group definition:
      ::

	dnRouter# configure
         role = 
         cmd_deny = 
         cmd_allow = 
         cmd_limit =	

   **role** - specify the role for all members of the group. 
      The available roles are:
      * Tech-support - has full control.
      * Admin - has full control except request system recovery commands.
      * Operator - has full control, except request system restart commands.
      * Viewer - can execute show commands only.

   The minimum user role required for each command is specified for every command in this manual, as follows:
      The minimum user role required for this command:
      * Support - Only Tech-support can execute the command.
      * Administrator - Administrators and Tech-support can execute the command.
      * Operator - Operators, Administrators, and Tech-support can execute the command.
      * Viewer - Viewers, Operators, and Administrators can execute the command.


   **cmd_deny** - enables to set exceptions to the commands permitted by the role. For example, say that you assign MyGroupA with the "Operator" role. This grants members of this group permission to execute a specific list of commands (see CLI-TACACS Command Mapping reference guide). If, for example, you don't want members of MyGroupA to make change the configured TACACS+ servers (contrary to the default permissions of the role), you must specify all the commands relating to the TACACS+ servers in the cmd_deny row. 

   **cmd_allow** - enables to set exceptions to the commands denied by the role. For example, say that you want members of MyGroupA to perform system restart, contrary to what is allowed by the role. You can add the system restart command in the cmd_allow row. 
   Commands must be entered in the form as described in the CLI-TACACS Command Mapping reference guide in the TACACS+ column. The commands are separated by a semicolon (;) (e.g. system.tacacs; no.system.tacacs). 

   **cmd_limit** - enables to set limitations on the value that group members can set to permitted commands. The value you want to limit can be greater than, less than, equals, or is not (>, <, =, !=), or it can be an "if... then... statement. 
   For example, say that members of MyGroupA are allowed to configure MTU for interfaces. You can set limitations on the value that they can set. 
   Here are some examples:

   * interface.mtu > 2500: this statement will not allow group members to set a value lower than 2500 for an interface MTU.
   * interface.mtu = 3000: this statement only allows group members to set a value of 3000 for interface MTU.
   * if interface.mtu > 2000 then interface.mtu > 2500: this statement allows group members to set the interface MTU to a value higher than 2500 only if it is already higher than 2000.


   -. Assign users to groups. Refer to the TACACS+ documentation.

**Example** 
   Using the examples above, the code for MyGroupA in the TACACS+ server is:
      ::

	group = MyGroupA {
   
      login = PAM
      
      service = TTY
      default attribute = permit
      role = Operator
      cmd_deny = system.tacacs; no.system.tacacs
      cmd_allow = request.system.restart
      cmd_limit = "if interface.mtu > 2000 then interface.mtu > 2500"


To enter AAA configuration mode:

::
   dnRouter(cfg-system)# aaa-server
   dnRouter(cfg-system-aaa)



**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 6.0     | Command introduced                           |
+---------+----------------------------------------------+
| 13.0    | Added support for RADIUS                     |
+---------+----------------------------------------------+

