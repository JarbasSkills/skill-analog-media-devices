#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-analog-media-devices.jarbasai=skill_analog_media_devices:AnalogMediaSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-analog-media-devices',
    version='0.0.1',
    description='ovos uvc skill plugin',
    url='https://github.com/JarbasSkills/skill-analog-media-devices',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_analog_media_devices": ""},
    package_data={'skill_analog_media_devices': ['locale/*', 'ui/*']},
    packages=['skill_analog_media_devices'],
    include_package_data=True,
    install_requires=["ovos-PHAL-plugin-analog-media-devices",
                      "ovos_plugin_common_play"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
