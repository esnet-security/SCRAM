import grpc
import gobgp_pb2_grpc


def before_all(context):
    channel = grpc.insecure_channel("gobgp:50051")
    context.stub = gobgp_pb2_grpc.GobgpApiStub(channel)
