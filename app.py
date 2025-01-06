import streamlit as st
import moviepy.editor as mp
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import pysrt
import os
import numpy as np

# 기본 폰트 설정
font_path = "./fonts/BMDOHYEON.ttf"  # 폰트 파일 경로를 정확히 지정
font_size = 32
font_color = 'white'
stroke_color = 'black'
stroke_width = 1

# 텍스트의 가로 길이를 기준으로 줄바꿈 처리
def split_text_by_width(text, font, max_width):
    words = text.split()  # 단어 단위로 분리
    lines = []
    current_line = ""

    # 가상 이미지 객체 생성
    image = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(image)

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        width, _ = draw.textsize(test_line, font=font)

        if width > max_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line)

    return lines

# 텍스트 이미지를 생성하는 함수
def create_text_image(text, width, max_height):
    font = ImageFont.truetype(font_path, font_size)
    lines = split_text_by_width(text, font, width - 40)  # 좌우 20px 패딩 적용
    line_height = font_size + 10
    height = len(lines) * line_height + 20
    height = min(height, max_height)

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    y = 10
    for line in lines:
        text_width, _ = draw.textsize(line, font=font)
        x = (width - text_width) // 2
        draw.text((x, y), line, font=font, fill=font_color, stroke_width=stroke_width, stroke_fill=stroke_color)
        y += line_height

    return np.array(image)

# 텍스트 크기를 계산하는 함수 수정
def get_text_size(text, font):
    # textsize() 대신 textbbox() 사용
    bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font)
    width = bbox[2] - bbox[0]  # bbox의 좌측과 우측 차이로 텍스트의 너비 계산
    height = bbox[3] - bbox[1]  # bbox의 상단과 하단 차이로 텍스트의 높이 계산
    return width, height

def extract_speaker_emotion(subtitle_text):
    # 자막 텍스트에서 화자와 감정을 추출
    if "|" in subtitle_text:
        parts = subtitle_text.split("|")
        text = parts[0].strip()

        if len(parts) > 1:
            emotion_info = parts[1].strip()
            # 화자와 감정 정보가 있을 경우
            if "(" in emotion_info and ")" in emotion_info:
                speaker, emotion = emotion_info.split("(")
                speaker = speaker.strip()
                emotion = emotion.replace(")", "").strip()
                return text, speaker, emotion
        return text, "Unknown", "neutral"
    return subtitle_text, "Unknown", "neutral"

def create_text_image(text, width, height):
    # PIL을 사용하여 텍스트 이미지 생성
    font = ImageFont.truetype(font_path, font_size)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    text_size = draw.textbbox((0, 0), text, font=font)  # textsize() 대신 textbbox() 사용
    text_position = ((width - text_size[2] + text_size[0]) // 2, (height - text_size[3] + text_size[1]) // 2)
    
    # 텍스트를 흰색으로 그리기
    draw.text(text_position, text, font=font, fill=font_color)
    
    return np.array(image)

def merge_subtitles(video_file, srt_file):
    # 임시 파일 경로 설정
    temp_video_path = "temp_video.mp4"
    temp_srt_path = "temp_subtitles.srt"

    # 업로드된 파일을 임시 파일로 저장
    with open(temp_video_path, "wb") as f:
        f.write(video_file.read())
    with open(temp_srt_path, "wb") as f:
        f.write(srt_file.read())

    # MoviePy를 사용하여 동영상에 자막 추가
    video = mp.VideoFileClip(temp_video_path)

    # SRT 파일을 UTF-8 인코딩으로 읽고 파싱
    subs = pysrt.open(temp_srt_path, encoding='utf-8')

    # 자막 클립을 생성하는 함수
    subtitle_clips = []
    for sub in subs:
        start = sub.start.ordinal / 1000
        end = sub.end.ordinal / 1000
        text, speaker, emotion = extract_speaker_emotion(sub.text)

        full_text = f"({speaker})({emotion}) {text}"
        text_img = create_text_image(full_text, video.w, 100)
        
        txt_clip = mp.ImageClip(text_img).set_start(start).set_end(end).set_position(('center', video.h - 100))
        subtitle_clips.append(txt_clip)

    # 자막을 비디오에 오버레이
    final_video = CompositeVideoClip([video] + subtitle_clips)

    # 결과 비디오를 임시 파일로 저장
    output_path = "output_video.mp4"
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')

    # 임시 파일 삭제
    os.remove(temp_video_path)
    os.remove(temp_srt_path)

    return output_path

def main():
    st.title("(화자)(감정) 자막 프로그램")

    st.write("동영상 파일과 srt 자막 파일을 업로드하세요. 자막은 `(화자)(감정)(자막)` 형식으로 작성됩니다.")

    # 파일 업로드
    video_file = st.file_uploader("동영상 파일 업로드", type=["mp4", "avi", "mov"])
    srt_file = st.file_uploader("srt 자막 파일 업로드", type=["srt"])

    if video_file is not None and srt_file is not None:
        if st.button("동영상 만들기"):
            with st.spinner('처리 중... 잠시만 기다려주세요.'):
                try:
                    output_video_path = merge_subtitles(video_file, srt_file)
                    st.success("처리가 완료되었습니다!")

                    # 처리된 비디오를 스트리밍하여 표시
                    video_bytes = open(output_video_path, 'rb').read()
                    st.video(video_bytes)

                    # 결과 비디오 다운로드 링크 제공
                    st.download_button(
                        label="완성 비디오 다운로드",
                        data=video_bytes,
                        file_name="output_video.mp4",
                        mime="video/mp4"
                    )

                    # 처리된 비디오 파일 삭제
                    os.remove(output_video_path)

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
