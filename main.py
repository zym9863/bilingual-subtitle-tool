"""
双语字幕工具 - Gradio Web界面
A lightweight tool for adding bilingual subtitles to videos with English audio
"""

import os
import gradio as gr
import logging
from typing import Optional, Tuple, List
import tempfile
import shutil

# 导入自定义模块
from src.config import config
from src.audio_extractor import AudioExtractor
from src.speech_recognizer import SpeechRecognizer
from src.translator import BaiduTranslator
from src.subtitle_generator import SubtitleGenerator
from src.video_processor import VideoProcessor
from src.utils import (
    is_video_file,
    validate_file_size,
    get_file_size_mb,
    ProgressCallback,
    ensure_dir,
    sanitize_filename
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保临时目录存在
ensure_dir(config.TEMP_DIR)

# 初始化环境
try:
    from src.environment import initialize_environment
    initialize_environment()
except ImportError:
    logger.warning("环境初始化模块未找到，使用默认配置")


class BilingualSubtitleApp:
    """双语字幕应用主类"""

    def __init__(self):
        self.audio_extractor = AudioExtractor()
        self.speech_recognizer = SpeechRecognizer()
        self.translator = BaiduTranslator()
        self.subtitle_generator = SubtitleGenerator()
        self.video_processor = VideoProcessor()

    def process_video(
        self,
        video_file,
        whisper_model_size: str,
        baidu_appid: str,
        baidu_appkey: str,
        subtitle_type: str,
        burn_subtitles: bool,
        font_size: int,
        font_color: str,
        progress=gr.Progress()
    ) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
        """
        处理视频文件，生成双语字幕

        Returns:
            Tuple: (视频文件路径, 字幕文件路径, 日志信息, 状态信息)
        """
        try:
            # 验证输入
            if video_file is None:
                return None, None, None, "❌ 请上传视频文件"

            video_path = video_file.name

            # 验证文件格式
            if not is_video_file(video_path):
                return None, None, None, f"❌ 不支持的视频格式，支持的格式: {', '.join(config.SUPPORTED_VIDEO_FORMATS)}"

            # 验证文件大小
            if not validate_file_size(video_path):
                file_size = get_file_size_mb(video_path)
                return None, None, None, f"❌ 文件过大 ({file_size:.1f}MB)，最大支持 {config.MAX_FILE_SIZE}MB"

            # 配置翻译器
            if baidu_appid and baidu_appkey:
                self.translator.appid = baidu_appid
                self.translator.appkey = baidu_appkey

            if not self.translator.is_configured():
                return None, None, None, "❌ 请配置百度翻译API的APPID和APPKEY"

            # 配置语音识别器
            self.speech_recognizer.model_size = whisper_model_size

            log_messages = []

            # 步骤1: 提取音频
            progress(0.1, "正在提取音频...")
            log_messages.append("🎵 开始提取音频...")

            audio_path = self.audio_extractor.extract_audio(video_path)
            log_messages.append(f"✅ 音频提取完成: {os.path.basename(audio_path)}")

            # 步骤2: 语音识别
            progress(0.3, "正在进行语音识别...")
            log_messages.append("🎤 开始语音识别...")

            segments = self.speech_recognizer.transcribe(audio_path)
            log_messages.append(f"✅ 语音识别完成，识别到 {len(segments)} 个段落")

            # 步骤3: 翻译
            progress(0.6, "正在翻译文本...")
            log_messages.append("🌐 开始翻译文本...")

            translated_segments = self.translator.translate_segments(segments)
            log_messages.append(f"✅ 翻译完成，处理了 {len(translated_segments)} 个段落")

            # 步骤4: 生成字幕文件
            progress(0.8, "正在生成字幕文件...")
            log_messages.append("📝 开始生成字幕文件...")

            base_filename = sanitize_filename(os.path.splitext(os.path.basename(video_path))[0])
            subtitle_path = self.subtitle_generator.create_srt_from_segments(
                translated_segments,
                subtitle_type=subtitle_type
            )
            log_messages.append(f"✅ 字幕文件生成完成: {os.path.basename(subtitle_path)}")

            output_video_path = None

            # 步骤5: 烧录字幕（可选）
            if burn_subtitles:
                progress(0.9, "正在烧录字幕到视频...")
                log_messages.append("🔥 开始烧录字幕到视频...")

                subtitle_style = {
                    "font_size": font_size,
                    "font_color": font_color
                }

                output_video_path = self.video_processor.burn_subtitles(
                    video_path,
                    subtitle_path,
                    subtitle_style=subtitle_style
                )
                log_messages.append(f"✅ 字幕烧录完成: {os.path.basename(output_video_path)}")

            progress(1.0, "处理完成！")
            log_messages.append("🎉 所有处理步骤完成！")

            log_text = "\n".join(log_messages)
            status = "✅ 处理完成！可以下载生成的文件。"

            return output_video_path, subtitle_path, log_text, status

        except Exception as e:
            error_msg = f"❌ 处理失败: {str(e)}"
            logger.error(error_msg)
            return None, None, str(e), error_msg


    def create_interface(self):
        """创建Gradio界面"""

        # 自定义CSS样式
        css = """
        .gradio-container {
            max-width: 1200px !important;
        }
        .status-box {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        """

        with gr.Blocks(
            title="双语字幕工具",
            theme=gr.themes.Soft(),
            css=css
        ) as interface:

            gr.Markdown("""
            # 🎬 双语字幕工具

            一个轻量级的工具，为带英文音频的视频添加中英双语字幕。

            **功能特点:**
            - 🎵 自动提取视频音频
            - 🎤 AI语音识别（支持GPU加速）
            - 🌐 百度翻译API翻译
            - 📝 生成SRT字幕文件
            - 🔥 可选字幕烧录到视频
            """)

            with gr.Row():
                with gr.Column(scale=2):
                    # 文件上传
                    video_input = gr.File(
                        label="📁 上传视频文件",
                        file_types=config.SUPPORTED_VIDEO_FORMATS,
                        type="filepath"
                    )

                    # 配置选项
                    with gr.Accordion("⚙️ 配置选项", open=True):
                        whisper_model = gr.Dropdown(
                            choices=["tiny", "base", "small", "medium", "large"],
                            value="base",
                            label="🎤 Whisper模型大小",
                            info="更大的模型识别更准确但速度更慢"
                        )

                        with gr.Row():
                            baidu_appid = gr.Textbox(
                                label="🔑 百度翻译APPID",
                                placeholder="请输入百度翻译API的APPID",
                                type="password"
                            )
                            baidu_appkey = gr.Textbox(
                                label="🔐 百度翻译APPKEY",
                                placeholder="请输入百度翻译API的密钥",
                                type="password"
                            )

                    # 字幕选项
                    with gr.Accordion("📝 字幕选项", open=True):
                        subtitle_type = gr.Radio(
                            choices=[
                                ("双语字幕", "bilingual"),
                                ("仅英文", "original"),
                                ("仅中文", "translated")
                            ],
                            value="bilingual",
                            label="字幕类型"
                        )

                        burn_subtitles = gr.Checkbox(
                            label="🔥 烧录字幕到视频",
                            value=False,
                            info="将字幕永久嵌入视频中"
                        )

                        with gr.Row():
                            font_size = gr.Slider(
                                minimum=12,
                                maximum=48,
                                value=24,
                                step=2,
                                label="字体大小"
                            )
                            font_color = gr.Dropdown(
                                choices=["white", "yellow", "cyan", "green"],
                                value="white",
                                label="字体颜色"
                            )

                    # 处理按钮
                    process_btn = gr.Button(
                        "🚀 开始处理",
                        variant="primary",
                        size="lg"
                    )

                with gr.Column(scale=1):
                    # 状态显示
                    status_display = gr.Textbox(
                        label="📊 处理状态",
                        value="等待上传视频文件...",
                        interactive=False,
                        lines=2
                    )

                    # 输出文件
                    output_video = gr.File(
                        label="📹 输出视频",
                        visible=False
                    )

                    output_subtitle = gr.File(
                        label="📝 字幕文件",
                        visible=False
                    )

                    # 处理日志
                    log_display = gr.Textbox(
                        label="📋 处理日志",
                        lines=10,
                        max_lines=20,
                        interactive=False,
                        visible=False
                    )

            # 系统信息
            with gr.Accordion("ℹ️ 系统信息", open=False):
                gr.Markdown(f"""
                - **GPU可用**: {'✅ 是' if config.is_gpu_available() else '❌ 否'}
                - **推荐设备**: {config.get_device()}
                - **最大文件大小**: {config.MAX_FILE_SIZE}MB
                - **支持格式**: {', '.join(config.SUPPORTED_VIDEO_FORMATS)}
                """)

            # 事件处理
            def update_outputs(video, subtitle, log, status):
                """更新输出组件的可见性"""
                return (
                    gr.update(value=video, visible=video is not None),
                    gr.update(value=subtitle, visible=subtitle is not None),
                    gr.update(value=log, visible=log is not None)
                )

            process_btn.click(
                fn=self.process_video,
                inputs=[
                    video_input,
                    whisper_model,
                    baidu_appid,
                    baidu_appkey,
                    subtitle_type,
                    burn_subtitles,
                    font_size,
                    font_color
                ],
                outputs=[output_video, output_subtitle, log_display, status_display]
            ).then(
                fn=update_outputs,
                inputs=[output_video, output_subtitle, log_display, status_display],
                outputs=[output_video, output_subtitle, log_display]
            )

        return interface


def main():
    """主函数"""
    app = BilingualSubtitleApp()
    interface = app.create_interface()

    # 启动应用
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
