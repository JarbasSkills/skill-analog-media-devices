import os
import subprocess
from distutils.spawn import find_executable
from os.path import join, dirname

from ovos_plugin_common_play import PlaybackType, MediaType
from ovos_utils.log import LOG
from ovos_utils.sound import play_wav
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media, ocp_play


class UVC:
    def __init__(self, device="video0", card="CAMERA"):
        self.device = device
        self.card = card
        self.video = None
        self.audio_stream = None
        self.audio_player = None

    @property
    def audio_fifo(self):
        stream = f"/tmp/uvc_audio_{self.card}.stream"
        # (Re)create Fifo
        if os.path.exists(stream):
            os.remove(stream)
        os.mkfifo(stream)
        return stream

    def run(self):

        self.stop()

        player = find_executable("mpv")
        if player:
            player = f'{player} av://v4l2:/dev/{self.device} --profile=low-latency --untimed --fs'
        if not player:
            player = find_executable("vlc")
            if player:
                player = f'{player} v4l2://:v4l-vdev="/dev/{self.device}" --fullscreen'
        if not player:
            player = find_executable("mplayer")
            if player:
                player = f'{player} tv:// -tv driver=v4l2:width=640:height=480:device=/dev/{self.device} -fps 30'
        if not player:
            raise RuntimeError("Can not display video")

        LOG.debug(f"Opening UVC Video: {player}")
        self.video = subprocess.Popen(player, shell=True)

        LOG.debug(f"Opening audio stream: {player}")
        stream = self.audio_fifo
        self.audio_stream = subprocess.Popen(f"arecord -D plughw:CARD={self.card} {stream}", shell=True)
        self.audio_player = play_wav(stream)

    def stop_audio(self):
        if self.audio_stream:
            try:
                self.audio_stream.terminate()
                self.audio_stream.communicate()
            except Exception as e:
                self.audio_stream.kill()
            finally:
                self.audio_stream = None
        if self.audio_player:
            try:
                self.audio_player.terminate()
                self.audio_player.communicate()
            except Exception as e:
                self.audio_player.kill()
            finally:
                self.audio_player = None

    def stop_video(self):
        if self.video:
            try:
                self.video.terminate()
                self.video.communicate()
            except Exception as e:
                self.video.kill()
            finally:
                self.video = None

    def stop(self):
        self.stop_audio()
        self.stop_video()


class UVCMediaSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(UVCMediaSkill, self).__init__("UVCMedia")
        self.supported_media = [MediaType.GENERIC, MediaType.GAME, MediaType.VIDEO]
        self.uvc = None
        self.skill_icon = join(dirname(__file__), "ui", "easycap.png")
        self.skill_logo = join(dirname(__file__), "ui", "easycap.jpg")

    def initialize(self):
        self.add_event("gui.clear.namespace", self.handle_gui_release)
        # TODO multiple devices with user defined aliases
        if "device" not in self.settings:
            self.settings["device"] = "video0"
        if "card" not in self.settings:
            self.settings["card"] = "CAMERA"
        self.uvc = UVC(device=self.settings["device"], card=self.settings["card"])

    def handle_gui_release(self, message):
        # TODO move this to base class  OVOSCommonPlaybackSkill
        skill_id = message.data.get("__from")
        if skill_id == self.skill_id or skill_id == "ovos.common_play":
            self.stop()

    def stop(self):
        if self.uvc:
            self.uvc.stop()

    @ocp_play()
    def open_uvc(self, message=None):
        self.uvc.run()

    @ocp_featured_media()
    def featured_media(self):
        # TODO match individual vocabs according to user aliases
        # change icon per device
        return [
            {
                "match_confidence": 90,
                "media_type": MediaType.VIDEO,
                "uri": f'/dev/{self.settings["device"]}',
                "playback": PlaybackType.SKILL,
                "skill_icon": self.skill_icon,
                "image": self.skill_logo,
                "bg_image": self.skill_logo,
                "title": "Analog Input UVC ( /dev/video0 )"
            }
        ]

    @ocp_search()
    def ocp_uvc(self, phrase):
        if not os.path.exists(f'/dev/{self.settings["device"]}'):
            return
        if self.voc_match(phrase, "console_names"):
            score = 100
            icon = join(dirname(__file__), "ui", "console.png")
            # TODO match individual consoles according to user aliases
            # change icon per console, only match voc for consoles user flagged
            yield {
                "match_confidence": score,
                "media_type": MediaType.GAME,
                "uri": f'/dev/{self.settings["device"]}',
                "playback": PlaybackType.SKILL,
                "skill_icon": self.skill_icon,
                "image": icon,
                "bg_image": self.skill_logo,
                "title": "Game Console (Analog Input UVC)"
            }
        elif self.voc_match(phrase, "vhs", exact=True):
            yield {
                "match_confidence": 95,
                "media_type": MediaType.VIDEO,
                "uri": f'/dev/{self.settings["device"]}',
                "playback": PlaybackType.SKILL,
                "skill_icon": self.skill_icon,
                "image": join(dirname(__file__), "ui", "vhs.png"),
                "bg_image": self.skill_logo,
                "title": "VHS player (UVC Analog Input)"
            }


def create_skill():
    return UVCMediaSkill()
