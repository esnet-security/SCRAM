Feature: we can query the list of entries for a specific entry
  The api should be able to return information about specific entries

  Scenario Outline: we can succesfully query our entry list
    When we're logged in
    And the CIDR prefix limits are 8 and 32
    And we add the entry <ip>
    And we query for <ip>
    Then we get a 200 status code

    Examples: IPs
      | ip            |
      | 1.2.3.4       |
      | 2.0.0.0/8     |
      | 2001::1       |
      | 201::0/32     |

  Scenario Outline: we can add a host and then query based on other parts of the CIDR
    When we're logged in
    And the CIDR prefix limits are 8 and 32
    And we add the entry <ip>
    And we query for <cidr>
    Then we get a 200 status code

    Examples: v4
      | ip          | cidr        |
      | 1.2.3.4/32  | 1.0.0.0/8   |
      | 2.0.0.0/8   | 2.1.1.1     |
      | 2.0.0.0/8   | 2.1.1.1/32  |
      | 2.0.0.0/8   | 2.1.1.1/15  |

    Examples: v6
      | ip          | cidr        |
      | 2001::1/128 | 2001::/32   |
      | 2001::/32   | 2001::1     |
      | 2001::/32   | 2001::1/128 |
      | 2001::/32   | 2001::1/64  |

  Scenario Outline: we cant query larger than our prefixmin
    When we're logged in
    And the CIDR prefix limits are 1 and 1
    And we add the entry <ip>
    And the CIDR prefix limits are 8 and 32
    And we query for <ip>
    Then we get a 400 status code


    Examples: IPs
      | ip            |
      | 2.0.0.0/7     |
      | 201::0/31     |

  Scenario Outline: we cant enter malformed IPs
    When we're logged in
    And  we add the entry <ip>
    And  we query for <ip>
    Then we get a ValueError


    Examples: IPs
      | ip              |
      | 1.2.3.256       |
      | 193.168.0.0/33  |
      | 2001:::::       |
      | 201::0/129      |
