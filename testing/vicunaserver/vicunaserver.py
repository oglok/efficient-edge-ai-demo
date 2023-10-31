from mlc_chat import ChatModule, ChatConfig, ConvConifg
from mlc_chat.callback import StreamIterator
from threading import Thread
import asyncio
import logging
import grpc
from vicunaserving_pb2 import VicunaReply
from vicunaserving_pb2 import VicunaRequest
from vicunaserving_pb2_grpc import MultiVicunaServicer
from vicunaserving_pb2_grpc import add_MultiVicunaServicer_to_server
import supervision as sv

class VicunaServing(MultiVicunaServicer):
    async def vicunaInference(self, request: VicunaRequest,
                       context: grpc.aio.ServicerContext) -> VicunaReply:
        logging.info("Serving the requested inferencing")

        conv_config = ConvConfig(system=request.context)

        cm = ChatModule(model="params", conv_config=conv_config)

        stream = StreamIterator(callback_interval=2)
        generation_thread = Thread(
            target=cm.generate,
            kwargs={"prompt": request.prompt, "progress_callback": stream},
        )
        generation_thread.start()
        
        infstr = ""
        for delta_message in stream:
            # Yield back our VicunaReply
            infstr += delta_message
            yield VicunaReply(reply=infstr)
       
        generation_thread.join()

# async serve function for the grpc server
async def serve() -> None:

    # Instantiate a server on 50051
    server = grpc.aio.server()
    add_MultiVicunaServicer_to_server(VicunaServing(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
