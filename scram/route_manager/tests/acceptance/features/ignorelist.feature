Feature: The ignorelist keeps us from blocking a cidr we have ignorelisted

  Scenario Outline: we can add an ignore entry
    When we're logged in
    And  we add the ignore entry <ip>
    And  we list the ignoreentrys

    Then the number of ignoreentrys is 1
    And  <ip> is contained in our list of ignoreentrys

    Examples: v4 IPs
      | ip             |
      | 192.0.2.4      |
      | 198.51.100.255 |

    Examples: v6 IPs
      | ip          |
      | 2001:DB8::  |
      | 2001:DB8::1 |

  Scenario Outline: we can't block an entry from the ignore list
    Given a block actiontype is defined
    And a client with block authorization
    When we're logged in
    And the CIDR prefix limits are 16 and 48
    And  we add the ignore entry <ignore>
    And  we add the entry <entry>
    Then we get a 400 status code

    Examples: v4 IPs
      | entry           | ignore         |
      | 192.0.2.2       | 192.0.2.2/32   |
      | 192.0.2.129     | 192.0.2.128/25 |
      | 198.51.100.0/24 | 198.51.100.1   |

    Examples: v6 IPs
      | entry              | ignore             |
      | 2001:DB8::1        | 2001:DB8::1/128    |
      | 2001:DB8:ABCD::1   | 2001:DB8:ABCD::/64 |
      | 2001:DB8:DEAD::/64 | 2001:DB8:DEAD::2   |
