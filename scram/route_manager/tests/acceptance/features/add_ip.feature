Feature: add and remove IP addresses
  Users can add and remove v4 and v6 IP addresses

  Scenario: unauthenticated users get a 403
    When we add the IP 127.0.0.1
    Then we get a 403 status code

  Scenario Outline: add an IP address
     When we're logged in
     And  we add the IP <ip>
     And  we list the IPs

     Then the number of IPs is 1
     And  <cidr> is one of our IPs
     And  <ip> is contained in our IPs


  Examples: v4 IPs
   | ip          | cidr           |
   | 1.2.3.4     | 1.2.3.4/32     |
   | 193.168.0.0 | 193.168.0.0/32 |

  Examples: v6 IPs
   | ip      | cidr       |
   | 2000::  | 2000::/128 |
   | ::1     | ::1/128    |

  Scenario Outline: add an IP address multiple times
     When we're logged in
     And  we add the IP <ip>
     And  we add the IP <ip>

     Then we get a 400 status code
     And the number of IPs is 1

  Examples: IPs
   | ip          |
   | 1.2.3.4     |
   | 193.168.0.0 |
   | 2000::      |
   | ::1         |
