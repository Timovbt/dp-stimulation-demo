from fire import Fire

from stimulation.stimulation import start_stimulation_VEP
from stimulation.utils.logging import logger

from dareplane_utils.default_server.server import DefaultServer


def main(port: int = 8081, ip: str = "127.0.0.1", loglevel: int = 10):
    logger.setLevel(loglevel)

    pcommand_map = {
        "VEP": start_stimulation_VEP,
        # "ODDBALL":
    }

    server = DefaultServer(
        port, ip=ip, pcommand_map=pcommand_map, name="stimulation_control_server"
    )

    # initialize to start the socket
    server.init_server()
    
    logger.info(
        f"Server intialized, starting to listen for connections on: {ip=}, {port=}"
    )

    # start processing of the server
    server.start_listening()

    return 0


if __name__ == "__main__":
    Fire(main)
