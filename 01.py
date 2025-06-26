import time
import cv2
import mediapipe as mp
import numpy as np

# تنظیمات اولیه
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# دیکشنری کد مورس برای تمام حروف HELLO WORLD
MORSE_CODE_DICT = {
    'H': '....',
    'E': '.',
    'L': '.-..',
    'O': '---',
    'W': '.--',
    'R': '.-.',
    'D': '-..',
    ' ': ' '
}

# متن مورد نظر برای تایپ
TARGET_TEXT = "HELLO WORLD"
target_morse = [MORSE_CODE_DICT[char] for char in TARGET_TEXT]

# متغیرهای حالت
current_letter_index = 0
current_morse = ""
detected_text = ""
last_hand_states = {}
cooldown = False
cooldown_time = 0
last_action_time = time.time()

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    # پردازش تصویر
    image = cv2.flip(image, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    # نمایش اطلاعات
    cv2.putText(image, f"Target: {TARGET_TEXT}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(image, f"Detected: {detected_text}", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # نمایش حرف فعلی و کد مورس هدف آن
    if current_letter_index < len(TARGET_TEXT):
        current_char = TARGET_TEXT[current_letter_index]

        # نمایش کد مورس برای فاصله (space) به صورت واضح
        morse_display = MORSE_CODE_DICT[current_char]
        if current_char == ' ':
            morse_display = "[SPACE]"

        cv2.putText(image, f"Current Char: {current_char} ({morse_display})",
                    (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)

    cv2.putText(image, f"Your Input: {current_morse}", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    if results.multi_hand_landmarks:
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness = results.multi_handedness[hand_idx].classification[0].label

            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

            h, w, c = image.shape
            thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
            index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)

            distance = np.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)

            current_hand_state = "CLOSED" if distance < 30 else "OPEN"

            color = (0, 255, 0) if handedness == "Right" else (255, 0, 0)
            cv2.circle(image, (thumb_x, thumb_y), 10, color, -1)
            cv2.circle(image, (index_x, index_y), 10, color, -1)
            cv2.line(image, (thumb_x, thumb_y), (index_x, index_y), color, 2)

            cv2.putText(image, f"{handedness} Hand: {current_hand_state}",
                        (10, 450 + hand_idx * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            hand_key = f"{handedness}_{hand_idx}"
            last_state = last_hand_states.get(hand_key)

            if current_hand_state != last_state and not cooldown:
                last_hand_states[hand_key] = current_hand_state
                cooldown = True
                cooldown_time = time.time()
                last_action_time = time.time()

                if current_hand_state == "CLOSED":
                    if handedness == "Right":
                        current_morse += '.'
                        print("Right hand closed: added DOT (.)")
                    elif handedness == "Left":
                        current_morse += '-'
                        print("Left hand closed: added DASH (-)")

    # مدیریت زمان خنک‌سازی
    if cooldown and time.time() - cooldown_time > 0.5:
        cooldown = False

    # بررسی تکمیل حرف فعلی (حل مشکل تطبیق برای WORLD)
    if current_letter_index < len(TARGET_TEXT):
        target_char = TARGET_TEXT[current_letter_index]
        target_morse_str = MORSE_CODE_DICT[target_char]

        # اگر کاربر فاصله را وارد کرده
        if target_char == ' ':
            if current_morse == "":
                detected_text += ' '
                current_letter_index += 1
                last_action_time = time.time()
                print("Space added")

        # تطبیق کد مورس با حرف هدف
        elif current_morse == target_morse_str:
            detected_text += target_char
            current_letter_index += 1
            current_morse = ""
            last_action_time = time.time()
            print(f"Letter completed: {target_char}")

            # نمایش پیام تکمیل جمله
            if current_letter_index >= len(TARGET_TEXT):
                cv2.putText(image, "COMPLETED! SUCCESS!", (200, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                print("Full sentence completed!")

    # ریست پس از 3 ثانیه عدم فعالیت
    if current_morse and time.time() - last_action_time > 1.5:
        print(f"Timeout! Resetting current input: {current_morse}")
        current_morse = ""
        last_action_time = time.time()

    # نمایش تصویر
    cv2.imshow('Dual-Hand Morse Code Typing: HELLO WORLD', image)

    # خروج با فشار دادن کلید 'q'
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

# آزادسازی منابع
cap.release()
cv2.destroyAllWindows()