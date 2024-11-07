import streamlit as st
import moviepy.editor as mp
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.config import change_settings
import pysrt
import os

# 필요한 경우 ImageMagick 경로 설정
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

# 기본 폰트 설정
font_path = "./fonts/BMDOHYEON.ttf"  # 폰트 파일 경로를 정확히 지정
font_size = 36
font_color = 'white'
stroke_color = 'black'
stroke_width = 1

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
        start = sub.start.ordinal / 1000  # ms to seconds
        end = sub.end.ordinal / 1000  # ms to seconds
        text, speaker, emotion = extract_speaker_emotion(sub.text)

        # 자막 텍스트 (화자와 감정 추가)
        full_text = f"({speaker})({emotion}) {text}"

        # 자막 텍스트 생성 (기본 폰트 사용)
        txt_clip = TextClip(full_text, font=font_path, fontsize=font_size,
                                    color=font_color, stroke_color=stroke_color,
                                    stroke_width=stroke_width)

        # 자막 클립 위치 및 시간 설정
        txt_clip = txt_clip.set_start(start).set_end(end).set_position(('center', video.h - 100))

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

    st.write("동영상 파일과 SRT 자막 파일을 업로드해라. 자막은 `(화자)(감정)(자막)` 형식으로 작성된다.")

    # 파일 업로드
    video_file = st.file_uploader("동영상 파일 업로드", type=["mp4", "avi", "mov"])
    srt_file = st.file_uploader("SRT 자막 파일 업로드", type=["srt"])

    if video_file is not None and srt_file is not None:
        if st.button("처리 시작"):
            with st.spinner('처리 중... 잠시만 기다려주세요.'):
                try:
                    output_video_path = merge_subtitles(video_file, srt_file)
                    st.success("처리가 완료되었습니다!")

                    # 처리된 비디오를 스트리밍하여 표시
                    video_bytes = open(output_video_path, 'rb').read()
                    st.video(video_bytes)

                    # 결과 비디오 다운로드 링크 제공
                    st.download_button(
                        label="결과 비디오 다운로드",
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
