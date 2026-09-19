import json
import os
import random
import sys
import threading
import time
import pylsl
from pathlib import Path
from fire import Fire
import psychopy
from psychopy import core, event, misc, monitors, visual
from stimulation.utils.logging import logger
from pylsl import StreamInfo, StreamOutlet
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
import toml


class Stimulation(object):
    """
    Object to present a stimulation on the screen

    Parameters
    ----------
    screen_resolution: tuple[int, int]
        Resolution of display used for stimulation
    refresh_rate: int
        refresh rate of display
    cfg: dict
        dict of toml config file
    screen_id: int = 0,
    background_color: tuple[float, float, float] (default: 0.0, 0.0, 0.0),
    marker_stream_name: str = "marker-stream",
    start_eval_marker: str = "start"
    quit_controls: list[str] = None,
    full_screen: bool = True
        whether to use full screen
    stimulation_method: str (default: 'VEP')
        which way of stimulation to use
    Attributes
    ----------


    """
    def __init__(
        self,
        screen_resolution: tuple[int, int],
        refresh_rate: int,
        cfg: dict,
        screen_id: int = 0,
        background_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
        marker_stream_name: str = "marker-stream",
        start_eval_marker: int =  0,
        stim_marker: int = 1,
        quit_controls: list[str] = None,
        stim_size: list = [500,500],
        stim_color = "white",
        full_screen: bool = True,
        stimulation_method: str = "VEP",
        n_flashes: int = 200,
        flash_duration: int = 0,
        interval: list = [500,750]
    ) -> None:
        self.screen_resolution = screen_resolution
        self.full_screen = full_screen
        self.refresh_rate = refresh_rate
        self.quit_controls = quit_controls
        self.stim_size = stim_size
        self.stim_color = stim_color
        self.stimulation_method = stimulation_method
        self.n_flashes = n_flashes
        self.flash_duration= flash_duration
        self.start_eval_marker = start_eval_marker
        self.stim_marker = stim_marker
        self.interval_min,self.interval_max = interval
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
            nominal_srate=0.0,
            channel_format=pylsl.cf_int8,
            source_id=marker_stream_name,
        )
        self.outlet = StreamOutlet(info)

        self.stim_duration = self.refresh_rate / 60 * 3 #duration of 50ms
        
        if self.stimulation_method == "VEP":
                self.add_stimuli_VEP()
                self.add_fixation()



    def add_stimuli_VEP(self):
        """Add a single rectangle from psychopy for VEP stimulation"""
        self.stimuli = visual.rect.Rect(self.window,
                                          size = self.stim_size,
                                          units='pix',
                                          name = 'rectangle',
                                          color = self.stim_color
                                        )

    def add_fixation(self):
        self.fixation = visual.ShapeStim(win=self.window,
                                         vertices= "cross",
                                         size= (30,30),
                                         fillColor= "black",
                                         lineColor="black"
                                         )
        
    def run(
        self, 
    ) -> None:
        """Main loop for stimulation"""
        logger.info("Starting stimulation...")
        self.log(marker = self.start_eval_marker)
        # self.stimuli.setAutoDraw(False)
        # core.wait(5)
        self.fixation.setAutoDraw(True)
        for i in range(self.n_flashes):
            if len(event.getKeys(keyList=self.quit_controls)) > 0:
                self.quit()
                break
            random_time = random.uniform(self.interval_min,self.interval_max)
            self.stimuli.draw()
            self.window.callOnFlip(self.log,self.stim_marker)
            self.window.flip() #show stimuli
            core.wait(self.flash_duration)
            self.window.flip() #clear stimuli
            core.wait(random_time/1000) #ISI
            

    def quit(
        self,
    ) -> None:
        """
        Quit the stimulation, close the window.
        """
        if self.window is not None:
            logger.info("Closing window...")
            self.window.flip()
            self.window.setMouseVisible(True)
            self.window.close()
       
    def log(
        self,
        marker: int,
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
        stim_marker = cfg["streams"]["stim_marker"],
        start_eval_marker = cfg["streams"]["start_eval_marker"],
        quit_controls=cfg["stimulation"]["controls"]["quit"],
        stim_size=cfg['stimulation']['stimuli']['size'],
        stim_color=cfg['stimulation']['stimuli']['color'],
        stimulation_method = "VEP",
        n_flashes=cfg["stimulation"]["timing"]["n_flashes"],
        flash_duration=cfg["stimulation"]["timing"]["flash_duration"],
        interval =cfg["stimulation"]["timing"]["interval"],
        cfg=cfg,
        ) 
    
    
    # Wait to start run
    logger.info("Waiting for button press to start")
    event.waitKeys(keyList=cfg["stimulation"]["controls"]["continue"])

    # Log info
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    # stimulation.log(
    #     marker=f"version;python={python_version};psychopy={psychopy.__version__}"
    # )

    # Start run
    logger.info("Starting")
    # stimulation.log(marker="start_run")
    # stimulation.set_text_field(name="messages", text="Starting...")
    stimulation.run()

    # Stop run
    logger.info("Stopping")
    # stimulation.log(marker="stop_run")
    stimulation.quit()

    return 0

if __name__ == "__main__":
    Fire(start_stimulation_VEP)
