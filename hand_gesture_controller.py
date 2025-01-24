import cv2
import mediapipe as mp
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MoveImageApp:
    def __init__(self, root, camera_label, image_frame):
        self.root = root
        self.camera_label = camera_label
        self.image_frame = image_frame
        self.image_path = r'C:\Users\mehrdad\Desktop\media pipe\src\photo.PNG'
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            print(f"Error: Unable to load image at {self.image_path}. Please check the file path.")
            exit()
        self.image_height, self.image_width, _ = self.image.shape
        self.x_offset = 0
        self.y_offset = 0
        self.hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.image_label = ctk.CTkLabel(self.image_frame, text="")
        self.image_label.pack()

    def is_finger_pointing_up(self, hand_landmarks):
        tip_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
        pip_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
        return tip_y < pip_y

    def is_finger_pointing_down(self, hand_landmarks):
        tip_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
        pip_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
        return tip_y > pip_y

    def is_finger_pointing_left(self, hand_landmarks):
        tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
        pip_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].x
        return tip_x < pip_x

    def is_finger_pointing_right(self, hand_landmarks):
        tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
        pip_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].x
        return tip_x > pip_x

    def update_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2),  # Red dots
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)   # Green lines
                )
                if self.is_finger_pointing_up(hand_landmarks):
                    self.y_offset -= 5
                elif self.is_finger_pointing_down(hand_landmarks):
                    self.y_offset += 5
                if self.is_finger_pointing_left(hand_landmarks):
                    self.x_offset -= 5
                elif self.is_finger_pointing_right(hand_landmarks):
                    self.x_offset += 5
        self.y_offset = max(0, min(self.y_offset, frame.shape[0] - self.image_height))
        self.x_offset = max(0, min(self.x_offset, frame.shape[1] - self.image_width))
        background = np.zeros_like(frame)
        background[self.y_offset:self.y_offset + self.image_height, self.x_offset:self.x_offset + self.image_width] = self.image
        combined_frame = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
        combined_frame = Image.fromarray(combined_frame)
        combined_frame = ImageTk.PhotoImage(image=combined_frame)
        self.image_label.configure(image=combined_frame)
        self.image_label.image = combined_frame

class BrightnessVolumeApp:
    def __init__(self, root):
        self.root = root
        self.hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mode = "brightness"
        self.brightness_label = ctk.CTkLabel(root, text="Brightness: ?", font=("Arial", 20))
        self.brightness_label.pack()
        self.volume_label = ctk.CTkLabel(root, text="Volume: ?", font=("Arial", 20))
        self.volume_label.pack()
        self.button_frame = ctk.CTkFrame(root)
        self.button_frame.pack(pady=10)
        self.brightness_button = ctk.CTkButton(self.button_frame, text="Brightness", command=self.set_mode_brightness, width=100, height=100, corner_radius=50, fg_color="green")
        self.brightness_button.grid(row=0, column=0, padx=10)
        self.volume_button = ctk.CTkButton(self.button_frame, text="Volume", command=self.set_mode_volume, width=100, height=100, corner_radius=50, fg_color="gray")
        self.volume_button.grid(row=0, column=1, padx=10)

    def adjust_brightness(self, up):
        current_brightness = sbc.get_brightness()[0]
        step = 2
        if up:
            new_brightness = min(current_brightness + step, 100)
            sbc.set_brightness(new_brightness)
        else:
            new_brightness = max(current_brightness - step, 0)
            sbc.set_brightness(new_brightness)
        self.brightness_label.configure(text=f"Brightness: {new_brightness}%")

    def adjust_volume(self, up):
        current_volume = volume.GetMasterVolumeLevelScalar()
        step = 0.05
        if up:
            new_volume = min(current_volume + step, 1.0)
            volume.SetMasterVolumeLevelScalar(new_volume, None)
        else:
            new_volume = max(current_volume - step, 0.0)
            volume.SetMasterVolumeLevelScalar(new_volume, None)
        self.volume_label.configure(text=f"Volume: {int(new_volume * 100)}%")

    def update_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2),  # Red dots
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)   # Green lines
                )
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                if index_finger_tip.y < thumb_tip.y:
                    if self.mode == "brightness":
                        self.adjust_brightness(True)
                    elif self.mode == "volume":
                        self.adjust_volume(True)
                elif index_finger_tip.y > thumb_tip.y:
                    if self.mode == "brightness":
                        self.adjust_brightness(False)
                    elif self.mode == "volume":
                        self.adjust_volume(False)

    def set_mode_brightness(self):
        self.mode = "brightness"
        self.brightness_button.configure(fg_color="green")
        self.volume_button.configure(fg_color="gray")

    def set_mode_volume(self):
        self.mode = "volume"
        self.volume_button.configure(fg_color="green")
        self.brightness_button.configure(fg_color="gray")

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Control")
        self.root.geometry("1200x900")
        self.root.configure(bg="black")
        self.move_image_app = None
        self.brightness_volume_app = None
        self.frame_container = ctk.CTkFrame(root)
        self.frame_container.pack(pady=20)
        self.camera_frame = ctk.CTkFrame(self.frame_container, width=600, height=400)
        self.camera_frame.grid(row=0, column=0)
        self.image_frame = ctk.CTkFrame(self.frame_container, width=600, height=400)
        self.image_frame.grid(row=0, column=1)
        self.image_frame.grid_remove()
        self.camera_label = ctk.CTkLabel(self.camera_frame, text="")
        self.camera_label.pack()
        self.button_frame = ctk.CTkFrame(root)
        self.button_frame.pack(pady=20)
        self.move_image_button = ctk.CTkButton(self.button_frame, text="Move Image", command=self.show_move_image_app, width=200, height=50)
        self.move_image_button.grid(row=0, column=0, padx=10)
        self.brightness_volume_button = ctk.CTkButton(self.button_frame, text="Brightness/Volume", command=self.show_brightness_volume_app, width=200, height=50)
        self.brightness_volume_button.grid(row=0, column=1, padx=10)
        self.quit_button = ctk.CTkButton(root, text="Quit", fg_color="red", command=self.quit_app, width=200, height=50)
        self.quit_button.pack(side="bottom", pady=20)
        self.update_camera_feed()

    def show_move_image_app(self):
        if self.brightness_volume_app:
            self.brightness_volume_app.brightness_label.pack_forget()
            self.brightness_volume_app.volume_label.pack_forget()
            self.brightness_volume_app.button_frame.pack_forget()
        if not self.move_image_app:
            self.move_image_app = MoveImageApp(self.root, self.camera_label, self.image_frame)
        self.image_frame.grid()

    def show_brightness_volume_app(self):
        if self.move_image_app:
            self.image_frame.grid_remove()
        if not self.brightness_volume_app:
            self.brightness_volume_app = BrightnessVolumeApp(self.root)
        self.brightness_volume_app.brightness_label.pack()
        self.brightness_volume_app.volume_label.pack()
        self.brightness_volume_app.button_frame.pack()

    def update_camera_feed(self):
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            if self.move_image_app:
                self.move_image_app.update_frame(frame)
            if self.brightness_volume_app:
                self.brightness_volume_app.update_frame(frame)
            camera_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            camera_img = Image.fromarray(camera_img)
            camera_img = ImageTk.PhotoImage(image=camera_img)
            self.camera_label.configure(image=camera_img)
            self.camera_label.image = camera_img
        self.root.after(10, self.update_camera_feed)

    def quit_app(self):
        self.root.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    app = MainApp(root)
    root.mainloop()

cap.release()
cv2.destroyAllWindows()