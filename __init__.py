import os
import subprocess
from distutils.spawn import find_executable
from os.path import join, dirname

from ovos_plugin_common_play import PlaybackType, MediaType
from ovos_utils.log import LOG
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media, ocp_play, ocp_pause, ocp_resume

from threading import Thread


class UVC:
    def __init__(self, device="video0", player="auto"):
        self.device = device
        self.stream = None
        self.running = False
        self._player = player

    @property
    def player(self):
        if self._player == "auto":
            if find_executable("mpv"):
                self._player = "mpv"
            elif find_executable("vlc"):
                self._player = "vlc"
            elif find_executable("mplayer"):
                self._player = "mplayer"

        player = find_executable(self._player) or self._player
        if self._player == "vlc" or self._player == "cvlc":
            return f'{player} v4l2://:v4l-vdev="/dev/{self.device}" --fullscreen --video-on-top'
        elif self._player == "mpv":
            return f'{player} av://v4l2:/dev/{self.device} --profile=low-latency --untimed --fs'
        elif self._player == "mplayer":
            return f'{player} tv:// -tv driver=v4l2:width=640:height=480:device=/dev/{self.device} -fps 30'
        return player

    def start(self):
        self.stop()
        if not self.player:
            raise RuntimeError("Can not display video")
        LOG.debug(f"Opening UVC Video: {self.player}")
        self.running = True
        self.stream = subprocess.Popen(self.player, shell=True)
        self.running = False

    def stop(self):
        if self.stream:
            try:
                self.stream.terminate()
                self.stream.communicate()
            except Exception as e:
                if self.stream:
                    self.stream.kill()
            finally:
                self.stream = None
        self.running = False


class UVCAudio:
    def __init__(self, card="CAMERA"):
        self.card = card
        self.stream = None
        self.audio_player = None
        self.running = False

    def start(self):
        self.stop()
        self.running = True

        arecord = find_executable("arecord")
        if arecord:
            player = f"{arecord} -D plughw:CARD={self.card}"
            LOG.debug(f"Opening audio stream: {player}")
            self.stream = subprocess.Popen(player, shell=True,
                                           stdout=subprocess.PIPE)
            self.start_audio_playback()
        else:
            LOG.exception("Could not open audio input, arecord not found")
        self.running = False

    def start_audio_playback(self):
        if self.stream:
            play_cmd = find_executable("aplay")
            if not play_cmd:
                LOG.exception("Can not playback audio, aplay not found")
            else:
                self.audio_player = subprocess.Popen(play_cmd, stdin=self.stream.stdout, shell=True)

    def stop_audio_playback(self):
        if self.audio_player:
            try:
                self.audio_player.terminate()
                self.audio_player.communicate()
            except Exception as e:
                self.audio_player.kill()
            finally:
                self.audio_player = None

    def stop(self):
        self.stop_audio_playback()
        if self.stream:
            try:
                self.stream.terminate()
                self.stream.communicate()
            except Exception as e:
                if self.stream:
                    self.stream.kill()
            finally:
                self.stream = None
        self.running = False


class UVCMediaSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(UVCMediaSkill, self).__init__("UVCMedia")
        self.supported_media = [MediaType.GENERIC, MediaType.GAME, MediaType.VIDEO]
        self.video = None
        self.audio = None
        self.skill_icon = join(dirname(__file__), "ui", "easycap.png")
        self.skill_logo = join(dirname(__file__), "ui", "easycap.jpg")

    def initialize(self):
        self.add_event("gui.clear.namespace", self.handle_gui_release)
        # TODO multiple devices with user defined aliases
        if "device" not in self.settings:
            self.settings["device"] = "video0"
        if "card" not in self.settings:
            self.settings["card"] = "CAMERA"
        if "player" not in self.settings:
            self.settings["player"] = "auto"
        self.settings["device"] = "video0"
        self.video = None
        self.audio = None

    def handle_gui_release(self, message):
        # TODO move this to base class  OVOSCommonPlaybackSkill
        skill_id = message.data.get("__from")
        if skill_id == self.skill_id or skill_id == "ovos.common_play":
            self.stop()

    def stop(self):
        if self.video:
            self.video.stop()
        if self.audio:
            self.audio.stop()
        self.video = None
        self.audio = None

    @ocp_play()
    def open_uvc(self, message=None):
        self.video = UVC(device=self.settings["device"],
                         player=self.settings["player"])
        self.audio = UVCAudio(card=self.settings["card"])
        self.video.start()
        self.audio.start()

    @ocp_pause()
    def pause_uvc_audio(self, message=None):
        if self.audio:
            self.audio.stop()
            self.audio = None

    @ocp_resume()
    def resume_uvc_audio(self, message=None):
        if self.video and not self.audio:
            self.audio = UVCAudio(card=self.settings["card"])
            self.audio.start()

    @ocp_featured_media()
    def featured_media(self):
        # TODO match individual vocabs according to user aliases
        # change icon per device
        if os.path.exists(f'/dev/{self.settings["device"]}'):
            return [
                {
                    "match_confidence": 90,
                    "media_type": MediaType.VIDEO,
                    "uri": f'/dev/{self.settings["device"]}',
                    "playback": PlaybackType.SKILL,
                    "skill_icon": self.skill_icon,
                    "image": self.skill_logo,
                    "bg_image": self.skill_logo,
                    "title": f'Capture Device /dev/{self.settings["device"]}'
                }
            ]
        return []

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
                "image": self.skill_logo,
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
