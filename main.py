from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from gpiozero import Button
from gpiozero import LED
import pickle
import face_recognition
import numpy as np
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray

Window.size = (800, 480)
Window.fullscreen=True

camera = PiCamera()
camera.resolution = (320, 240)
output = np.empty((240, 320, 3), dtype=np.uint8)
# camera.rotation = 90
camera.framerate = 24
rawCapture = PiRGBArray(camera, size=(320, 240))
rawCapture.truncate()


btn1 = Button(26)
btn2 = Button(6)
btn3 = Button(13)
btn4 = Button(19)

door = LED(21)

class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name='home_screen'
        self.home_loop=None


    def on_enter(self):
        print('Entered '+self.name)
        btn1.when_pressed = self.close_app
        btn2.when_pressed = self.go_enrole_screen
        btn3.when_pressed = self.go_scan_screen
        btn4.when_pressed = None
        self.home_loop=Clock.schedule_interval(self.loop,0)
    def on_pre_leave(self):
        Clock.unschedule(self.home_loop)
        print('Leaving '+self.name)

    def close_app(self):
        my_app.get_running_app().stop()

    def go_enrole_screen(self):
        my_app.screen_manager.current='enrole_screen'

    def go_scan_screen(self):
        my_app.screen_manager.current='scan_screen'

    # def go_check_screen(self):
    #     my_app.screen_manager.current='list_select_screen'

    def loop(self,dt):
        pass
class EnroleScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name='enrole_screen'
        self.i=0
    def clear(self):
        data={'encodings':[],'id':[],'name':[]}
        with  open('encodings.pickle', "wb") as f:
            f.write(pickle.dumps(data))

    def on_enter(self):
        self.data=pickle.loads(open('encodings.pickle', "rb").read())
        print('Entered '+self.name)
        btn1.when_pressed = self.back
        btn2.when_pressed = self.submit
        btn3.when_pressed = None
        btn4.when_pressed = None
        self.ids['uID'].text=f"{len(self.data['id'])}"
        self.ids['uName'].text=""
        self.pi_image=None

        self.face_locations=None
        self.this_loop=Clock.schedule_interval(self.loop,0)
    def fidPlus(self):
        self.i+=1
        self.ids['uID'].text=f"{self.i}"
    def fidMinus(self):
        self.i-=1
        self.ids['uID'].text=f"{self.i}"
    def on_pre_leave(self):
        Clock.unschedule(self.this_loop)
        print('Leaving '+self.name)
    def back(self):
        my_app.screen_manager.current='home_screen'
    def submit(self):
        # self.data=pickle.loads(open('encodings.pickle', "rb").read())
        try:
            face_encodings = face_recognition.face_encodings(output, self.face_locations)[0]
            self.data['encodings'].append(face_encodings)
            self.data['id'].append(self.ids['uID'].text)
            self.data['name'].append(self.ids['uName'].text)
            with  open('encodings.pickle', "wb") as f:
                f.write(pickle.dumps(self.data))
            self.back()
        except:
            pass
    def loop(self,dt):
        rawCapture.truncate(0)
        camera.capture(rawCapture, format="rgb",use_video_port=True)
        self.pi_image = rawCapture.array
        self.pi_image = cv2.rotate(self.pi_image, cv2.ROTATE_180)
        

        self.pi_image = cv2.flip(self.pi_image, 1)
        buf=self.pi_image.tostring()
        image_texture= Texture.create(size=(self.pi_image.shape[1],self.pi_image.shape[0]),colorfmt='rgb')
        image_texture.blit_buffer(buf,colorfmt='rgb',bufferfmt='ubyte')
        self.ids['preview'].texture =image_texture

        camera.capture(output, format="rgb")
        self.face_locations = face_recognition.face_locations(output)
        self.ids['instruction'].text=("Found {} faces in image.".format(len(self.face_locations)))

        rawCapture.truncate(0)
class ScanScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name='scan_screen'
        self.i=0
    def clear(self):
        data={}
        with  open('encodings.pickle', "wb") as f:
            f.write(pickle.dumps(data))

    def on_enter(self):
        print('Entered '+self.name)
        self.data=pickle.loads(open('encodings.pickle', "rb").read())
        btn1.when_pressed = self.back
        btn2.when_pressed = self.submit
        btn3.when_pressed = None
        btn4.when_pressed = self.door_open
        self.ids['uID'].text=""
        self.ids['uName'].text=""
        self.pi_image=None
        self.face_locations=None
        self.waiting=False
        self.this_loop=Clock.schedule_interval(self.loop,0)
    def fidPlus(self):
        self.i+=1
        self.ids['uID'].text=f"{self.i}"
    def fidMinus(self):
        self.i-=1
        self.ids['uID'].text=f"{self.i}"
    def on_pre_leave(self):
        Clock.unschedule(self.this_loop)
        print('Leaving '+self.name)
    def back(self):
        my_app.screen_manager.current='home_screen'
    def wait_over(self,dt):
        self.ids['uID'].text=""
        self.ids['uName'].text=""
        door.off()
        self.waiting=False
    def door_open(self):
        door.on()
        self.waiting=True
        Clock.schedule_once(self.wait_over, 5)
    def submit(self):
        
        pass
    def loop(self,dt):
        if not self.waiting:
            rawCapture.truncate(0)
            camera.capture(rawCapture, format="rgb",use_video_port=True)
            self.pi_image = rawCapture.array
            self.pi_image = cv2.rotate(self.pi_image, cv2.ROTATE_180)

            self.pi_image = cv2.flip(self.pi_image, 1)
            buf=self.pi_image.tostring()
            image_texture= Texture.create(size=(self.pi_image.shape[1],self.pi_image.shape[0]),colorfmt='rgb')
            image_texture.blit_buffer(buf,colorfmt='rgb',bufferfmt='ubyte')
            self.ids['preview'].texture =image_texture

            camera.capture(output, format="rgb")
            self.face_locations = face_recognition.face_locations(output)
            self.ids['instruction'].text=("Found {} faces in image.".format(len(self.face_locations)))

            try:
                face_encodings = face_recognition.face_encodings(output, self.face_locations)
                matches = face_recognition.compare_faces(self.data['encodings'], face_encodings[0],tolerance=0.4)
                name = "Unknown"
                
                # # If a match was found in known_face_encodings, just use the first one.
                # if True in matches:
                #     first_match_index = matches.index(True)
                #     name = known_face_names[first_match_index]

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(self.data['encodings'], face_encodings[0])
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    self.ids['uID'].text=f"{best_match_index}"
                    self.ids['uName'].text=f"{self.data['name'][best_match_index]}"
                    self.ids['instruction'].text="Go now.."
                    door.on()
                    self.waiting=True
                    Clock.schedule_once(self.wait_over, 5)
                # else:
                #     self.ids['instruction'].text="Unknown"
                #     self.waiting=True
                #     Clock.schedule_once(self.wait_over, 2)
            except:
                pass

            rawCapture.truncate(0)
class DoorApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):

        self.screen_manager = ScreenManager()

        self.home_screen = HomeScreen()
        self.screen_manager.add_widget(self.home_screen)

        self.enrole_screen = EnroleScreen()
        self.screen_manager.add_widget(self.enrole_screen)

        self.scan_screen = ScanScreen()
        self.screen_manager.add_widget(self.scan_screen)

        # self.book_list_screen = BookListScreen()
        # self.screen_manager.add_widget(self.book_list_screen)

        # self.student_list_screen = StudentListScreen()
        # self.screen_manager.add_widget(self.student_list_screen)

        # self.list_select_screen = ListSelectScreen()
        # self.screen_manager.add_widget(self.list_select_screen)

        # self.exchange_select_screen = ExchangeListScreen()
        # self.screen_manager.add_widget(self.exchange_select_screen)

        # self.atd_complete_page = AtdCompletePage()
        # self.screen_manager.add_widget(self.atd_complete_page)

        return self.screen_manager

if __name__ == "__main__":
    my_app = DoorApp()

    my_app.run()