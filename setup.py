#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-uvc-player.jarbasai=skill_uvc_player:UVCMediaSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-uvc-player',
    version='0.0.1',
    description='ovos uvc skill plugin',
    url='https://github.com/JarbasSkills/skill-uvc-player',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_uvc_player": ""},
    package_data={'skill_uvc_player': ['locale/*', 'ui/*']},
    packages=['skill_uvc_player'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a1"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
