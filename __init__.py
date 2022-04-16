from os.path import join, dirname

from ovos_plugin_common_play import PlaybackType, MediaType
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media, ocp_play, ocp_pause, ocp_resume
from ovos_PHAL_plugin_analog_media_devices.analog import get_device_json, AnalogAudio, AnalogVideo, AnalogVideoAudio


class AnalogMediaSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(AnalogMediaSkill, self).__init__("Analog Media Devices")
        self.supported_media = [MediaType.GENERIC, MediaType.GAME, MediaType.VIDEO, MediaType.AUDIO]
        self.skill_icon = self.skill_logo = join(dirname(__file__), "ui", "easycap.jpg")

    def initialize(self):
        self.add_event("gui.clear.namespace", self.handle_gui_release)

    def handle_gui_release(self, message):
        # TODO move this to base class  OVOSCommonPlaybackSkill
        skill_id = message.data.get("__from")
        if skill_id == self.skill_id or skill_id == "ovos.common_play":
            self.bus.emit(message.forward("ovos.common_play.analog.stop"))

    @ocp_play()
    def open_uvc(self, message=None):
        self.bus.emit(message.forward("ovos.common_play.analog.play"))

    @ocp_pause()
    def pause_uvc_audio(self, message=None):
        self.bus.emit(message.forward("ovos.common_play.analog.pause"))

    @ocp_resume()
    def resume_uvc_audio(self, message=None):
        self.bus.emit(message.forward("ovos.common_play.analog.resume"))

    @ocp_featured_media()
    def featured_media(self):
        devices = []
        for device, data in get_device_json().items():
            audio = data.get("audior")
            video = data.get("video")
            icon = data.get("icon") or self.skill_icon
            devices.append(
                {
                    "match_confidence": 90,
                    "media_type": MediaType.VIDEO if video else MediaType.AUDIO,
                    "uri": f"analog://{device}",
                    "playback": PlaybackType.SKILL,
                    "skill_icon": self.skill_icon,
                    "image": icon,
                    "bg_image": self.skill_logo,
                    "title": device
                }
            )
        return devices


def create_skill():
    return AnalogMediaSkill()
