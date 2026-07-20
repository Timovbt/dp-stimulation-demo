import json
import os
import random
import sys
import threading
import time
from pathlib import Path
from fire import Fire
import psychopy
from psychopy import core, event, misc, monitors, visual
# The modules logger is used everywhere necessary. Note this logger will usually only have a NetworkHandler.
# If you want to log to the console, you need to add a StreamHandler to it.
from stimulation.utils.logging import logger
from pylsl import StreamInfo, StreamOutlet
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
import toml


class Stimulation(object):
    def __init__(
        self,
        screen_resolution: tuple[int, int],
        refresh_rate: int,
        cfg: dict,
        screen_id: int = 0,
        background_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
        marker_stream_name: str = "marker-stream",
        quit_controls: list[str] = None,
        full_screen: bool = True,
    ) -> None:
        self.screen_resolution = screen_resolution
        self.full_screen = full_screen
        self.refresh_rate = refresh_rate
        self.quit_controls = quit_controls
        self.cfg = cfg
        # Setup monitor
        self.monitor = monitors.Monitor(
            name="Monitor"
        )
        self.monitor.setSizePix(screen_resolution)

        # Setup window
        self.window = visual.Window(
            monitor=self.monitor,
            screen=screen_id,
            units="pix",
            size=screen_resolution,
            color=background_color,
            fullscr=full_screen,
            waitBlanking=False,
            allowGUI=False,
        )
        self.window.setMouseVisible(False)

        # Setup LSL stream
        info = StreamInfo(
            name=marker_stream_name,
            type="Markers",
            channel_count=1,
            nominal_srate=0,
            channel_format="string",
            source_id=marker_stream_name,
        )
        self.outlet = StreamOutlet(info)

        self.stim_duration = self.refresh_rate / 60 * 3 #duration of 50ms
        self.rectangle = visual.rect.Rect(self.window,
                                          size = [500,500],
                                          name = 'rectangle',
                                        )

 
    def connect_to_decoder_lsl_stream(self) -> None:
        name = self.cfg["streams"]["decoder_stream_name"]
        logger.info(f'Connecting to decoder stream "{name}".')
        self.decoder_sw = StreamWatcher(name=name)
        self.decoder_sw.connect_to_stream()
    
    def run(
        self, 
    ) -> None:
        
        while True:
            stimulus_onset = random.randint(33,47) #random duration between 500ms and 750ms

            for i in range(self.refresh_rate):
                # Check quiting
                if i % 60 == 0:
                    if len(event.getKeys(keyList=self.quit_controls)) > 0:
                        self.quit()
                        break

                #draw for 50 ms
                if 0 < i < self.stim_duration:
                    self.rectangle.draw()
                    self.log(marker="stimulation_presented")

                if stimulus_onset < i < stimulus_onset + self.stim_duration:
                    self.rectangle.draw()
                    self.log(marker="stimulation_presented")

                self.window.flip()

            

    def quit(
        self,
    ) -> None:
        """
        Quit the stimulation, close the window.
        """
        if self.window is not None:
            self.window.flip()
            self.window.setMouseVisible(True)
            self.window.close()
       
    def log(
        self,
        marker: str,
    ) -> None:
        """
        Log a marker to the marker stream.

        Parameters
        ----------
        marker: str
            The marker to log.
        """
        self.outlet.push_sample([marker])


def start_stimulation_VEP(
    config_path: Path = Path("./configs/stimulation.toml"),  # relative to the project root
    ) -> int:

    cfg = toml.load(config_path)
    stimulation = Stimulation( 
        screen_resolution=cfg["stimulation"]["screen"]["resolution"],
        refresh_rate=cfg["stimulation"]["screen"]["refresh_rate_hz"],
        screen_id=cfg["stimulation"]["screen"]["id"],
        full_screen=cfg["stimulation"]["screen"]["full_screen"],
        background_color=cfg["stimulation"]["screen"]["background_color"],
        marker_stream_name=cfg["streams"]["marker_stream_name"],
        quit_controls=cfg["stimulation"]["controls"]["quit"],
        cfg=cfg,
        ) 
    

    # Wait to start run
    logger.info("Waiting for button press to start")
    event.waitKeys(keyList=cfg["stimulation"]["controls"]["continue"])

    # Log info
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    stimulation.log(
        marker=f"version;python={python_version};psychopy={psychopy.__version__}"
    )

    # Start run
    logger.info("Starting")
    stimulation.log(marker="start_run")
    # stimulation.set_text_field(name="messages", text="Starting...")
    stimulation.run()


    # Wait to stop
    logger.info("Waiting for button press to stop")
    # stimulation.set_text_field(name="messages", text="Press button to stop.")
    event.waitKeys(keyList=cfg["stimulation"]["controls"]["continue"])

    # Stop run
    logger.info("Stopping")
    stimulation.log(marker="stop_run")
    # stimulation.set_text_field(name="messages", text="Stopping...")
    stimulation.run()
    stimulation.quit()

    return 0

if __name__ == "__main__":
    Fire(start_stimulation_VEP)
