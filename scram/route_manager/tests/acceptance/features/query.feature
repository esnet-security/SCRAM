Feature: we can query the list of entries for a specific entry
  The api should be able to return information about specific entries

  Scenario Outline: we can succesfully query our entry list
    Given a client with block authorization
    When we're logged in
    And the CIDR prefix limits are 8 and 32
    And we add the entry <ip>
    And we query for <ip>
    Then we get a 200 status code

    Examples: IPs
      | ip                 |
      | 192.0.2.168        |
      | 192.0.2.176/29     |
      | 2001:DB8:9508::1   |
      | 2001:DB8:9508::/48 |

  Scenario Outline: we can add a host and then query based on other parts of the CIDR
    Given a client with block authorization
    When we're logged in
    And the CIDR prefix limits are 8 and 32
    And we add the entry <ip>
    And we query for <cidr>
    Then we get a 200 status code

    Examples: v4
      | ip              | cidr             |
      | 192.0.2.3/32     | 192.0.2.0/28    |
      | 192.0.2.32/28    | 192.0.2.35/32   |
      | 192.0.2.128/28   | 192.0.2.137/29  |

    Examples: v6
      | ip                   | cidr                 |
      | 2001:DB8:950A::/128  | 2001:DB8:950A::/48   |
      | 2001:DB8:950B::/48   | 2001:DB8:950B::1     |
      | 2001:DB8:950C::/48   | 2001:DB8:950C::1/128 |
      | 2001:DB8:950D::/48   | 2001:DB8:950D::1/64  |


  Scenario Outline: we cant query for malformed IPs and get redirected back to the home page
    Given a client with block authorization
    When we're logged in
    And  we add the entry <ip>
    And  we query for <ip>
    Then we get a 200 status code

    Examples: IPs
      | ip              |
      | 1.2.3.256       |
      | 193.168.0.0/33  |
      | 2001:::::       |
      | 201::0/129      |
      | gibberish_ip    |
