Feature: block with BGP
  Users can block routes via BGP

  Scenario Outline: We can block an IP
    When we add <route> with <asn>, <vrf>, and <community> to the block list
    Then <route> in <vrf> is blocked
    Then we delete <route> with <asn>, <vrf>, and <community> from the block list
    And <unblock_ip> in <vrf> is unblocked

    Examples: data
      | route            | vrf      | asn        | community  | unblock_ip  |
      | 192.0.2.4/32     | base     | 54321      | 444        | 192.0.2.5   |
      | 192.0.2.10/32    | base     | 4200000000 | 321        | 192.0.2.11  |
      | 2001:DB8:A::/64  | base     | 54321      | 444        | baba::      |
      | 2001:DB8:B::/64  | base     | 4200000000 | 321        | 2001:DB8::4 |
      | 192.0.2.20/32    | base     | 4200000000 | 4200000000 | 192.0.2.11  |
      | 2001:DB8:C::/64  | base     | 4200000000 | 4200000000 | 2001:DB8::4 |
      | 2001:DB8:C::1/64 | base     | 4200000000 | 4200000000 | 2001:DB8::5 |
      # | 192.0.2.4/32     | test-vrf | 54321      | 444        | 192.0.2.5   |
      # | 192.0.2.10/32    | test-vrf | 4200000000 | 321        | 192.0.2.11  |
      # | 2001:DB8:A::/64  | test-vrf | 54321      | 444        | baba::      |
      # | 2001:DB8:B::/64  | test-vrf | 4200000000 | 321        | 2001:DB8::4 |
      # | 192.0.2.20/32    | test-vrf | 4200000000 | 4200000000 | 192.0.2.11  |
      # | 2001:DB8:C::/64  | test-vrf | 4200000000 | 4200000000 | 2001:DB8::4 |
      # | 2001:DB8:C::1/64 | test-vrf | 4200000000 | 4200000000 | 2001:DB8::5 |

  Scenario Outline: Invalid ASNs fail
    When <route>, <vrf>, and <community> with invalid <asn> is sent

    Examples: data
      | route            | vrf      | asn                    | community |
      | 2001:DB8:C::2/64 | base     | 4242424242424242424242 | 100       |
      | 2001:DB8:C::2/64 | base     | -1                     | 100       |
      | 2001:DB8:C::2/64 | base     | 0                      | 100       |
      | 2001:DB8:C::2/64 | test-vrf | 4242424242424242424242 | 100       |
      | 2001:DB8:C::2/64 | test-vrf | -1                     | 100       |
      | 2001:DB8:C::2/64 | test-vrf | 0                      | 100       |
