"""验证码处理模块，带开关（默认关闭）。

当 CAPTCHA_ENABLED=True 时，提供验证码识别占位接口，
可通过实现 _call_captcha_api 方法对接第三方打码平台。

默认关闭（CAPTCHA_ENABLED=False），仅提供占位接口。
API密钥从 .env 文件读取，禁止硬编码。
"""
from __future__ import annotations

from typing import Optional

from loguru import logger

from config.settings import get_settings


class CaptchaSolver:
    """验证码识别器，带开关控制。

    使用方式：
    1. 在 .env 中设置 CAPTCHA_ENABLED=true
    2. 配置 CAPTCHA_API_URL 和 CAPTCHA_API_KEY
    3. 实现 _call_captcha_api 方法对接具体打码平台
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        """验证码处理是否启用。"""
        return self._settings.CAPTCHA_ENABLED

    def solve(self, image_data: bytes) -> Optional[str]:
        """识别验证码图片。

        当验证码处理未启用时直接返回None；
        启用后调用打码API进行识别（需实现 _call_captcha_api）。

        Args:
            image_data: 验证码图片的二进制数据

        Returns:
            识别结果文本，识别失败或未启用时返回 None
        """
        if not self.enabled:
            logger.debug("验证码处理未启用，跳过")
            return None

        logger.info("验证码处理已启用，调用打码API...")

        # 检查API配置是否完整
        if not self._settings.CAPTCHA_API_URL or not self._settings.CAPTCHA_API_KEY:
            logger.warning("打码API配置不完整（CAPTCHA_API_URL / CAPTCHA_API_KEY），返回None")
            return None

        # 调用打码API
        try:
            return self._call_captcha_api(image_data)
        except NotImplementedError:
            logger.warning("打码API尚未实现，返回None")
            return None
        except Exception as e:
            logger.error("打码API调用异常: {}", e)
            return None

    def _call_captcha_api(self, image_data: bytes) -> Optional[str]:
        """调用第三方打码API（占位方法，需根据实际API文档实现）。

        Args:
            image_data: 验证码图片二进制数据

        Returns:
            识别结果文本

        Raises:
            NotImplementedError: 此方法为占位，需子类或使用者实现
        """
        # TODO: 根据实际打码平台API文档实现
        # 示例伪代码：
        #   import aiohttp
        #   async with aiohttp.ClientSession() as session:
        #       data = aiohttp.FormData()
        #       data.add_field("image", image_data, filename="captcha.png")
        #       data.add_field("key", self._settings.CAPTCHA_API_KEY)
        #       async with session.post(self._settings.CAPTCHA_API_URL, data=data) as resp:
        #           result = await resp.json()
        #           return result.get("result")
        raise NotImplementedError("打码API调用尚未实现，请根据实际API文档实现此方法")
