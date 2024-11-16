Feature: block with BGP
  Users can block routes via BGP

  Scenario Outline: We can block an IP
    When we add <route> with <asn> and <community> to the block list
    Then <route> is blocked
    Then we delete <route> with <asn> and <community> from the block list
    And <unblock_ip> is unblocked

    Examples: data
      | route            | asn        | community  | unblock_ip  |
      | 192.0.2.4/32     | 54321      | 444        | 192.0.2.5   |
      | 192.0.2.10/32    | 4200000000 | 321        | 192.0.2.11  |
      | 2001:DB8:A::/64  | 54321      | 444        | baba::      |
      | 2001:DB8:B::/64  | 4200000000 | 321        | 2001:DB8::4 |
      | 192.0.2.20/32    | 4200000000 | 4200000000 | 192.0.2.11  |
      | 2001:DB8:C::/64  | 4200000000 | 4200000000 | 2001:DB8::4 |
      | 2001:DB8:C::1/64 | 4200000000 | 4200000000 | 2001:DB8::5 |

  Scenario Outline: Invalid ASNs fail
    When <route> and <community> with invalid <asn> is sent

    Examples: data
      | route            | asn                    | community |
      | 2001:DB8:C::2/64 | 4242424242424242424242 | 100       |
      | 2001:DB8:C::2/64 | -1                     | 100       |
      | 2001:DB8:C::2/64 | 0                      | 100       |
