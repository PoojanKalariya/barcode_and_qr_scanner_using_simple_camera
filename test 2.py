import cv2
from pyzbar import pyzbar
import time
import pyautogui
import winsound
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

# Dictionary to store the last detected time for each code
last_detected_time = {}


def play_beep_sound():
    # Play a beep sound (frequency: 1000Hz, duration: 100ms)
    winsound.Beep(3000, 70)


def get_connected_cameras():
    camera_list = []
    index = 0
    while True:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.read()[0]:
            break
        else:
            camera_list.append(index)
        cap.release()
        index += 1

    return camera_list


class BarcodeDetectionApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Barcode Detection (Version 1.2)")
        self.window.geometry("800x700")  # Set the initial window size
        self.selected_camera = tk.IntVar(value=0)  # Initialize as an IntVar
        self.iteration_counter = 0

        # Set default values for add_gap and fps
        self.add_gap_default = "2"
        self.fps_default = "10"

        self.add_gap_var = tk.StringVar(value=self.add_gap_default)
        self.fps_var = tk.StringVar(value=self.fps_default)

        # Row 1 - RTSP Entry Box
        self.top_frame = tk.Frame(self.window, padx=10, pady=10)
        self.top_frame.pack()
        self.add_rtsp_label = tk.Label(self.top_frame, text="Add RTSP For IP Camera:\n(Only for IP camera use)")
        self.add_rtsp_label.pack(side="left", pady=5, padx=5)
        self.add_rtsp_var = tk.StringVar()
        self.add_rtsp = tk.Entry(self.top_frame, width=40, textvariable=self.add_rtsp_var)
        self.add_rtsp.pack(side="left", pady=5, padx=5)
        self.add_rtsp_button = tk.Button(self.top_frame, text="SET", command=self.add_rtsp_to_camera_options)
        self.add_rtsp_button.pack(side="left", pady=5, padx=5)

        # Row 2 - Camera Selection and Start Button
        self.middle_frame = tk.Frame(self.window, padx=10, pady=10)
        self.middle_frame.pack()
        self.camera_options = get_connected_cameras()
        self.camera_var = tk.StringVar(value='0')
        self.camera_selection_label = tk.Label(self.middle_frame, text="Select Camera:")
        self.camera_selection_label.pack(side="left", pady=5, padx=5)
        self.camera_combobox = ttk.Combobox(self.middle_frame, values=self.camera_options,
                                            textvariable=self.camera_var, width=10)
        self.camera_combobox.pack(side="left", pady=5, padx=5)
        self.camera_button = tk.Button(self.middle_frame, text="Start", command=self.change_camera,
                                       font=("Arial", 12, "bold"))
        self.camera_button.pack(side="left", pady=5, padx=5)

        self.exit_button = tk.Button(self.middle_frame, text="Exit", command=self.quit)
        self.exit_button.pack(side="left", pady=5, padx=5)

        # Row 3 - Settings
        self.bottom_frame = tk.Frame(self.window, padx=10, pady=10)
        self.bottom_frame.pack()
        self.add_gap_label = tk.Label(self.bottom_frame, text="Detection Gap (Eg: 1 sec):")
        self.add_gap_label.pack(side="left", pady=5, padx=5)
        self.add_gap = tk.Entry(self.bottom_frame, validate="key",
                                validatecommand=(self.window.register(self.validate_entry), "%P"), width=5,
                                textvariable=self.add_gap_var)
        self.add_gap.pack(side="left", pady=5, padx=5)
        self.fps_label = tk.Label(self.bottom_frame, text="FPS (Eg: 2 frames per second):")
        self.fps_label.pack(side="left", pady=5, padx=5)
        self.fps = tk.Entry(self.bottom_frame, validate="key",
                            validatecommand=(self.window.register(self.validate_entry), "%P"), width=5,
                            textvariable=self.fps_var)
        self.fps.pack(side="left", pady=5, padx=5)
        self.newline_options = ['None', '\\n', '\\r\\n']
        self.newline_var = tk.StringVar(value='\\n')
        self.newline_label = tk.Label(self.bottom_frame, text="Newline char:")
        self.newline_label.pack(side="left", pady=5, padx=5)
        self.newline_combobox = ttk.Combobox(self.bottom_frame, values=self.newline_options,
                                             textvariable=self.newline_var, width=7)
        self.newline_combobox.pack(side="left", pady=5, padx=5)

        # Row 4 - Video Stream
        self.video_frame = tk.Frame(self.window)  # Create a frame for the video stream
        self.video_frame.pack()

        self.video_label = None
        self.cap = None

        self.window.protocol("WM_DELETE_WINDOW", self.quit)

    def add_rtsp_to_camera_options(self):
        rtsp_value = self.add_rtsp_var.get()
        if rtsp_value:
            self.camera_options.append(rtsp_value)
            self.camera_combobox["values"] = self.camera_options

    def change_camera(self):
        cam_var = self.camera_var.get()
        if self.cap is not None:
            self.cap.release()
            self.video_label.pack_forget()

        # if cam_var is None:
        #     messagebox.showwarning("Camera Selection", "Please select a camera.")
        #     return
        #
        # if len(cam_var) == 1:
        #     camera_index = int(cam_var)
        # else:
        #     camera_index = str(cam_var)
        #
        #
        # self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        # if not self.cap.isOpened():
        #     messagebox.showwarning("Camera Error", "Failed to open the selected camera.")
        #     return

        try:
            # Try to convert the selected camera value to an integer (camera index)
            camera_index = int(cam_var)

            # If successful, it's a camera index
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        except ValueError:
            # If not successful, it's an RTSP URL (string)
            self.cap = cv2.VideoCapture(cam_var)

        self.video_label = tk.Label(self.window)
        self.video_label.pack()

        self.update_video()

    def validate_entry(self, new_value):
        if new_value == "" or (new_value.isdigit() and 1 <= int(new_value) <= 30):
            return True
        else:
            return False

    def update_video(self):
        ret, frame = self.cap.read()
        add_gap_value = float(self.add_gap.get())
        fps_val = int(100 / int(self.fps.get()))  #transfroming fps to itration set

        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)

            self.video_label.configure(image=img_tk)
            self.video_label.image = img_tk

        if self.iteration_counter % fps_val == 0:
            self.process_frame(frame, add_gap_value)

        self.iteration_counter += 1
        # print(self.iteration_counter)
        self.window.after(1, self.update_video)

    def process_frame(self, frame, gap):
        barcodes = pyzbar.decode(frame)
        selected_newline = self.newline_var.get()
        print(selected_newline)
        if selected_newline =="\\n":
            newline = '\n'
        elif selected_newline == "\\r\\n":
            newline = '\r\n'
        else:
            newline = ""

        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")

            current_time = time.time()

            if barcode_data in last_detected_time and current_time - last_detected_time[barcode_data] < gap:
                continue

            last_detected_time[barcode_data] = current_time

            pyautogui.typewrite(barcode_data + str(newline))

            play_beep_sound()

    def quit(self):
        if self.cap is not None:
            self.cap.release()

        self.window.quit()


if __name__ == '__main__':
    app = BarcodeDetectionApp()
    app.window.mainloop()
