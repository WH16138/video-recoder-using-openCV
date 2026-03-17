import cv2 as cv
import numpy as np
from datetime import datetime

background = None

def detect_motion(frame):
    global background

    # 노이즈 완화
    frame_blur = cv.GaussianBlur(frame, (9, 9), 3).astype(np.float64)

    # 첫 프레임을 초기 배경으로 사용
    if background is None:
        background = frame_blur.copy()
        return frame.copy(), None

    # 현재 프레임과 배경 차이
    diff = frame_blur - background
    norm = np.linalg.norm(diff, axis=2)

    # threshold로 움직임 마스크 생성
    MOTION_THRESHOLD = 40 # 민감도
    mask = np.zeros_like(norm, dtype=np.uint8)
    mask[norm > MOTION_THRESHOLD] = 255

    # morphology로 잡음 제거 및 영역 보정
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

    # 윤곽선 검출
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    display = frame.copy()

    for contour in contours:
        area = cv.contourArea(contour)
        if area < 700:
            continue

        x, y, w, h = cv.boundingRect(contour)

        # 박스 표시
        cv.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 면적 표시 - 그냥 넣음
        cv.putText(
            display,
            f"Motion: {int(area)}",
            (x, max(y - 10, 20)),
            cv.FONT_HERSHEY_DUPLEX,
            0.5,
            (0, 255, 0),
            1
        )

    alpha = 0.07 # 배경 갱신 속도
    background = alpha * frame_blur + (1-alpha) * background

    return display, mask

def make_writer(frame_width, frame_height, fps):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"record_{now}.avi"
    fourcc = cv.VideoWriter_fourcc(*"XVID")
    writer = cv.VideoWriter(filename, fourcc, fps, (frame_width, frame_height))
    return writer, filename

def main():
    global background

    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("카메라를 열 수 없습니다?")
        return

    valid, frame = cap.read()
    if not valid:
        print("프레임 읽기 실패.")
        cap.release()
        return

    height, width = frame.shape[:2]
    fps = cap.get(cv.CAP_PROP_FPS)
    is_recording = False
    writer = None
    current_filename = None
    show_mask = True

    while True:
        valid, frame = cap.read()
        if not valid:
            print("프레임을 읽지 못했습니다. 프로그램을 종료합니다.")
            break

        # 움직임 검출
        motion_display, motion_mask = detect_motion(frame)

        display = motion_display.copy()

        # 현재 모드 표시 및 녹화 관리
        if is_recording:
            cv.circle(display, (width - 30, 30), 10, (0, 0, 255), -1)
            cv.putText(
                display,
                "RECORD",
                (10, 30),
                cv.FONT_HERSHEY_DUPLEX,
                0.8,
                (127, 127, 127),
                3
            )
            cv.putText(
                display,
                "RECORD",
                (10, 30),
                cv.FONT_HERSHEY_DUPLEX,
                0.8,
                (0, 0, 255),
                2
            )

            if writer is not None:
                writer.write(display)
        else:
            cv.putText(
                display,
                "PREVIEW",
                (10, 30),
                cv.FONT_HERSHEY_DUPLEX,
                0.8,
                (127, 127, 127),
                3
            )
            cv.putText(
                display,
                "PREVIEW",
                (10, 30),
                cv.FONT_HERSHEY_DUPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        cv.putText(
            display,
            "SPACE: Start/Stop Recording   ESC: Exit   M: Mask On/Off",
            (10, 60),
            cv.FONT_HERSHEY_DUPLEX,
            0.5,
            (127, 127, 127),
            2
        )
        cv.putText(
            display,
            "SPACE: Start/Stop Recording   ESC: Exit   M: Mask On/Off",
            (10, 60),
            cv.FONT_HERSHEY_DUPLEX,
            0.5,
            (255, 255, 255),
            1
        )

        cv.imshow("Video Recorder", display)

        if show_mask and motion_mask is not None:
            cv.imshow("Motion Mask", motion_mask)

        key = cv.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break
        elif key == ord(' '):  # Space
            if not is_recording:
                writer, current_filename = make_writer(width, height, fps)
                if not writer.isOpened():
                    print("녹화 파일을 생성할 수 없습니다.")
                    writer = None
                    current_filename = None
                    continue
                is_recording = True
                print(f"녹화 시작: {current_filename}")
            else:
                is_recording = False
                if writer is not None:
                    writer.release()
                    print(f"녹화 저장 완료: {current_filename}")
                    writer = None
                    current_filename = None
        elif key == ord('m') or key == ord('M'):
            show_mask = not show_mask
            if not show_mask:
                cv.destroyWindow("Motion Mask")

    if writer is not None:
        writer.release()
        print(f"녹화 저장 완료: {current_filename}")

    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()