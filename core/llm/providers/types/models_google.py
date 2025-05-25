from enum import Enum


class GoogleModel(Enum):
    GEMINI_2_5_FLASH_PREVIEW: str = "gemini-2.5-flash-preview-04-17"
    GEMINI_2_5_PRO_PREVIEW: str = "gemini-2.5-pro-preview-05-06"
    GEMINI_2_0_FLASH: str = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE: str = "gemini-2.0-flash-lite"
    GEMINI_1_5_FLASH: str = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B: str = "gemini-1.5-flash-8b"
    GEMINI_1_5_PRO: str = "gemini-1.5-pro"
