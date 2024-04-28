Feature: block with BGP
  Users can block routes via BGP

  Scenario Outline: We can block an IP
    When we add <route> with <asn> and <community> to the block list
    Then <route> is blocked
    And <unblock_ip> is unblocked

    Examples: data
    | route           |  asn       | community | unblock_ip   |
    | 192.0.2.4/32    | 64500      | 666       | 192.0.2.5    |
    | 192.0.2.10/32   | 4200000000 | 321       | 192.0.2.11   |
    | 2001:DB8:A::/64 | 64500      | 666       | baba::       |
    | 2001:DB8:B::/64 | 4200000000 | 321       | 2001:DB8::4  |

  Scenario Outline: We can block an IP
    When we add <route> with <asn> and <community> to the block list
    And we delete <route> from the block list
    Then <unblock_ip> is unblocked

    Examples: data
    | route           |  asn       | community | unblock_ip   |
    | 192.0.2.4/32    | 64500      | 666       | 192.0.2.4    |
    | 192.0.2.10/32   | 4200000000 | 321       | 192.0.2.11   |
    | 2001:DB8:A::/64 | 64500      | 666       | 2001:DB8::1 |
    | 2001:DB8:B::/64 | 4200000000 | 321       | 2001:DB8::4  |
