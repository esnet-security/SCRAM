Feature: The ignorelist keeps us from blocking a cidr we have ignorelisted

  Scenario Outline: we can add an ignore entry
    When we're logged in
    And  we add the ignore entry <ip>
    And  we list the ignoreentrys

    Then the number of ignoreentrys is 1
    And  <ip> is contained in our list of ignoreentrys

    Examples: v4 IPs
      | ip          |
      | 1.2.3.4     |
      | 193.168.0.0 |

    Examples: v6 IPs
      | ip     |
      | 2000:: |
      | ::1    |

  Scenario Outline: we can't block an entry from the ignore list
    Given a client with block authorization
    When we're logged in
    And  we add the ignore entry <ignore>
    And  we add the entry <entry>
    Then we get a 400 status code

    Examples: v4 IPs
      | entry          | ignore       |
      | 2.2.2.2        | 2.2.2.2/32   |
      | 1.2.3.4        | 1.2.3.0/24   |
      | 193.168.0.0/24 | 193.168.0.2  |

    Examples: v6 IPs
      | entry      |  ignore   |
      | ::1        | ::1/128   |
      | 2000::1    | 2000::/64 |
      | 193::/64   | 193::2    |
