"""
Services package - modularized structure.
"""
from .ppt_parser import PPTParser
from .script import ScriptGenerator
from .tts import TTSService

__all__ = ['PPTParser', 'ScriptGenerator', 'TTSService']
