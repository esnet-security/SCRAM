Feature: an automated source adds a block entry
  Automated clients (eg zeek) can add v4/v6 block entries

  Scenario: unauthenticated users get a 403
    When we add the entry 192.0.2.132
    Then we get a 403 status code

  Scenario Outline: add a block entry
    Given a block actiontype is defined
    And a client with block authorization
    When we're logged in
    And  we add the entry <ip>
    And  we list the entrys

    Then the number of entrys is 1
    And <cidr> is one of our list of entrys
    And <ip> is contained in our list of entrys
#    And <cidr> is announced by block translators

    Examples: v4 IPs
      | ip          | cidr           |
      | 192.0.2.128 | 192.0.2.128/32 |
      | 192.0.2.129 | 192.0.2.129/32 |

    Examples: v6 IPs
      | ip     | cidr                         |
      | 2001:DB8:94BB::94BC  | 2001:DB8:94BB::94BC/128  |
      | 2001:DB8:94BC:: | 2001:DB8:94BC::/128 |

  @history
  Scenario: add a block entry with a comment
    Given a client with block authorization
    When we're logged in
    And  we add the entry 192.0.2.133 with comment it's coming from inside the house
    Then we get a 201 status code
    And  the change entry for 192.0.2.133 is it's coming from inside the house

  Scenario Outline: add a block entry multiple times and it's accepted
    Given a client with block authorization
    When we're logged in
    And  we add the entry <ip>
    And  we add the entry <ip>

    Then we get a 201 status code
    And the number of entrys is 1

    Examples: IPs
      | ip              |
      | 192.0.2.130     |
      | 198.51.100.130  |
      | 2001:DB8:94BD::94BD  |
      | 2001:DB8:94BE:: |

  Scenario Outline: invalid block entries can't be added
    Given a client with block authorization
    When we're logged in
    And  we add the entry <ip>

    Then we get a 400 status code
    And the number of entrys is 0

    Examples: invalid IPs
      | ip          |
      | 1.2.3.4/128 |
      | 256.0.0.0   |
      | 1.2         |
      | gg::        |
      | 1:          |
      | 2000::1::1  |
      | 2000::/129  |

  Scenario Outline: add a block entry as a cidr address
    Given a block actiontype is defined
    And a client with block authorization
    When we're logged in
    And the CIDR prefix limits are 8 and 32
    And we add the entry <ip>
    And we list the entrys

    Then the number of entrys is 1
#    And <ip> is announced by block translators

    Examples:
      | ip                 |
      | 192.0.2.131/32     |
      | 198.51.100.160/29  |
      | 2001:DB8:94BA::94BD/128 |
      | 2001:DB8:94BE::/64 |
