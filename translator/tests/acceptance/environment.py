import gobgp_pb2_grpc
import grpc
import walrus


def before_all(context):
    context.db = walrus.Database(host="redis")
    channel = grpc.insecure_channel("gobgp:50051")
    context.stub = gobgp_pb2_grpc.GobgpApiStub(channel)
