"""Test talking to GoBGP with new API."""

import attribute_pb2
import common_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
import nlri_pb2

_TIMEOUT_SECONDS = 1000


class GoBGP:
    """Session for a GoBGP instance."""

    def __init__(self):
        """Initializes the session."""
        self.stub = gobgp_pb2_grpc.GobgpApiStub(grpc.insecure_channel("gobgp:50051"))

    def create_table_entry(self, ip, vrf=None):
        """create_table_entry creates a table entry for the given IP.

        Args:
            ip (_type_): IP address to add
            vrf (_type_, optional): VRF to add it to. Defaults to None.
        """
        family = common_pb2.Family(
            afi=common_pb2.Family.AFI_IP,  # AFI_IP for IPv4
            safi=common_pb2.Family.SAFI_UNICAST,  # SAFI_UNICAST for unicast routes
        )

        nlri = nlri_pb2.NLRI(prefix=nlri_pb2.IPAddressPrefix(prefix=ip, prefix_len=32))

        next_hop = attribute_pb2.Attribute(next_hop=attribute_pb2.NextHopAttribute(next_hop="0.0.0.0"))  # noqa S104

        origin = attribute_pb2.Attribute(
            origin=attribute_pb2.OriginAttribute(
                origin=0  # Set the origin to IGP
            )
        )

        pattrs = [next_hop, origin]

        path_object = gobgp_pb2.Path(
            nlri=nlri,
            pattrs=pattrs,
            family=family,
        )

        if vrf:
            self.stub.AddPath(
                gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.TableType.VRF, vrf_id="ipt", path=path_object)
            )
            return
        self.stub.AddPath(gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.TableType.GLOBAL, path=path_object))

        return

    def get_table_entries(self, ip, vrf=None):
        """get_table_entries grabs all the entries from a table, filtered to a single IP.

        Args:
            ip (_type_): IP to filter to
            vrf (_type_, optional): VRF to look in. Defaults to None.

        Returns:
            _type_: _description_
        """
        prefixes = [gobgp_pb2.TableLookupPrefix(prefix=str(ip))]
        family_afi = common_pb2.Family.AFI_IP

        if vrf:
            result = self.stub.ListPath(
                gobgp_pb2.ListPathRequest(
                    table_type=gobgp_pb2.VRF,
                    name=vrf,
                    prefixes=prefixes,
                    family=common_pb2.Family(afi=family_afi, safi=common_pb2.Family.SAFI_UNICAST),
                ),
                _TIMEOUT_SECONDS,
            )
            return list(result)

        result = self.stub.ListPath(
            gobgp_pb2.ListPathRequest(
                table_type=gobgp_pb2.GLOBAL,
                prefixes=prefixes,
                family=common_pb2.Family(afi=family_afi, safi=common_pb2.Family.SAFI_UNICAST),
            ),
            _TIMEOUT_SECONDS,
        )

        return list(result)


def main():
    """Tests that vrfs and global rib filters work the same way."""
    g = GoBGP()
    g.create_table_entry("10.0.0.1")
    g.create_table_entry("10.0.0.2")
    g.create_table_entry("10.0.0.1", vrf="ipt")
    g.create_table_entry("10.0.0.2", vrf="ipt")

    global_entries = g.get_table_entries("10.0.0.1")
    vrf_entries = g.get_table_entries("10.0.0.1", vrf="ipt")
    print(f"Found {len(global_entries)} entry in base routing instance.")  # noqa T201
    print(f"Found {len(vrf_entries)} entry in IPT VRF")  # noqa T201
    if len(global_entries) != len(vrf_entries):
        print("Uh oh, these aren't the same size, that sucks, filtering is broken!")  # noqa T201
    else:
        print("Yay, these are the same size, that means, filtering is not broken!")  # noqa T201


main()
