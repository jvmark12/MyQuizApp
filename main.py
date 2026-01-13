import os
# --- FORCE GUI MODE ---
os.environ['KIVY_WINDOW'] = 'sdl2'

import json
import re
import shutil
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

# --- CONFIG ---
Window.softinput_mode = "below_target"
BASE_DIR = "my_collections"
# Standard Android Download path
DOWNLOADS_PATH = "/storage/emulated/0/Download"

class QuizApp(App):
    def build(self):
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR)
        
        # Audio Path Fix - Using try/except so it doesn't crash if files are missing
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            self.snd_correct = SoundLoader.load(os.path.join(cur_dir, 'correct.mp3'))
            self.snd_wrong = SoundLoader.load(os.path.join(cur_dir, 'wrong.mp3'))
        except Exception:
            self.snd_correct = None
            self.snd_wrong = None
        
        self.quiz_data = []  
        self.current_q_idx = 0
        self.score = 0
        
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(ImportScreen(name='import'))
        self.sm.add_widget(FolderBrowser(name='browse'))
        self.sm.add_widget(EditScreen(name='edit'))
        self.sm.add_widget(PlayScreen(name='play'))
        return self.sm

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message, halign='center', valign='middle', text_size=(Window.width * 0.7, None)))
        btn = Button(text="CLOSE", size_hint_y=None, height='50dp')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)
        popup.open()

# --- SCREEN 1: MAIN MENU ---
class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text="EE QUIZ PRO", font_size='26sp', bold=True))
        
        btn_create = Button(text="✨ CREATE / PARSE NEW", size_hint_y=None, height='60dp', background_color=(0.2, 0.6, 1, 1))
        btn_create.bind(on_release=lambda x: setattr(self.manager, 'current', 'import'))
        
        btn_browse = Button(text="📂 BROWSE FOLDERS", size_hint_y=None, height='60dp', background_color=(0.9, 0.5, 0.1, 1))
        btn_browse.bind(on_release=lambda x: setattr(self.manager, 'current', 'browse'))

        self.btn_edit = Button(text="✏️ EDIT ACTIVE QUESTIONS", size_hint_y=None, height='60dp', disabled=True)
        self.btn_edit.bind(on_release=lambda x: setattr(self.manager, 'current', 'edit'))

        self.btn_play = Button(text="▶ PLAY ACTIVE QUIZ", size_hint_y=None, height='60dp', disabled=True)
        self.btn_play.bind(on_release=self.start_quiz)
        
        layout.add_widget(btn_create); layout.add_widget(btn_browse)
        layout.add_widget(self.btn_edit); layout.add_widget(self.btn_play)
        self.add_widget(layout)

    def on_enter(self):
        app = App.get_running_app()
        if app.quiz_data:
            self.btn_play.disabled = False
            self.btn_play.background_color = (0.1, 0.8, 0.1, 1)
            self.btn_edit.disabled = False
            self.btn_edit.background_color = (0.6, 0.4, 0.8, 1)

    def start_quiz(self, instance):
        app = App.get_running_app()
        app.current_q_idx = 0; app.score = 0
        self.manager.current = 'play'

# --- SCREEN 2: BROWSER ---
class FolderBrowser(Screen):
    def on_enter(self):
        self.selected_paths = []
        self.show_folders()

    def show_folders(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="FOLDERS", size_hint_y=None, height='40dp', bold=True))
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        list_box.bind(minimum_height=list_box.setter('height'))
        
        if os.path.exists(BASE_DIR):
            folders = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
            for f in folders:
                btn = Button(text=f"📁 {f.upper()}", size_hint_y=None, height='55dp', background_color=(0.3, 0.3, 0.5, 1))
                btn.bind(on_release=lambda x, folder=f: self.show_quizzes(folder))
                list_box.add_widget(btn)

        scroll.add_widget(list_box); layout.add_widget(scroll)
        btn_back = Button(text="BACK TO MENU", size_hint_y=None, height='50dp')
        btn_back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn_back); self.add_widget(layout)

    def show_quizzes(self, folder):
        self.clear_widgets(); self.selected_paths = []
        path = os.path.join(BASE_DIR, folder)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text=f"FOLDER: {folder}", size_hint_y=None, height='40dp'))
        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        list_box.bind(minimum_height=list_box.setter('height'))
        
        if os.path.exists(path):
            quizzes = [q for q in os.listdir(path) if q.endswith('.quiz')]
            for q in quizzes:
                btn = ToggleButton(text=f"📄 {q}", size_hint_y=None, height='50dp')
                btn.bind(on_press=lambda x, p=os.path.join(path, q): self.toggle_sel(p, x))
                list_box.add_widget(btn)

        scroll.add_widget(list_box); layout.add_widget(scroll)
        self.btn_action = Button(text="LOAD SELECTED (0)", size_hint_y=None, height='60dp', background_color=(0.5,0.5,0.5,1))
        self.btn_action.bind(on_release=self.load_merged)
        layout.add_widget(self.btn_action)
        btn_back = Button(text="BACK TO FOLDERS", size_hint_y=None, height='45dp')
        btn_back.bind(on_release=lambda x: self.show_folders())
        layout.add_widget(btn_back); self.add_widget(layout)

    def toggle_sel(self, path, widget):
        if widget.state == 'down': self.selected_paths.append(path)
        else: self.selected_paths.remove(path)
        count = len(self.selected_paths)
        self.btn_action.text = f"LOAD & MERGE ({count})"
        self.btn_action.background_color = (0, 0.8, 0.3, 1) if count > 0 else (0.5,0.5,0.5,1)

    def load_merged(self, instance):
        if not self.selected_paths: return
        mega_data = []
        app = App.get_running_app()
        for p in self.selected_paths:
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                    if not content: continue
                    data = json.loads(content)
                    if isinstance(data, list):
                        mega_data.extend(data)
            except Exception:
                app.show_popup("File Error", f"Skipping {os.path.basename(p)}")
        
        if mega_data:
            app.quiz_data = mega_data
            self.manager.current = 'menu'

# --- SCREEN 3: MANUAL EDITOR ---
class EditScreen(Screen):
    def on_enter(self):
        self.refresh_editor()

    def refresh_editor(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        layout.add_widget(Label(text="📝 MANUAL QUIZ EDITOR", size_hint_y=None, height='40dp', bold=True))
        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20, padding=10)
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.inputs = []
        app = App.get_running_app()
        for i, q in enumerate(app.quiz_data):
            q_box = BoxLayout(orientation='vertical', size_hint_y=None, height='310dp', spacing=5)
            q_box.add_widget(Label(text=f"Question {i+1}", size_hint_y=None, height='20dp', color=(0.2, 0.6, 1, 1)))
            qi = TextInput(text=str(q.get('q','')), size_hint_y=None, height='60dp')
            opts = q.get('o', ['', '', '', ''])
            oA = TextInput(text=str(opts[0]), size_hint_y=None, height='35dp')
            oB = TextInput(text=str(opts[1]), size_hint_y=None, height='35dp')
            oC = TextInput(text=str(opts[2]), size_hint_y=None, height='35dp')
            oD = TextInput(text=str(opts[3]), size_hint_y=None, height='35dp')
            ai = TextInput(text=str(q.get('a','A')), size_hint_y=None, height='35dp', halign='center')
            self.inputs.append({'q': qi, 'o': [oA, oB, oC, oD], 'a': ai})
            for w in [qi, oA, oB, oC, oD, Label(text="Correct Key (A/B/C/D):", size_hint_y=None, height='20dp'), ai]:
                q_box.add_widget(w)
            self.list_box.add_widget(q_box)
        self.scroll.add_widget(self.list_box); layout.add_widget(self.scroll)
        btn_save = Button(text="✅ SAVE CHANGES", size_hint_y=None, height='50dp', background_color=(0, 0.8, 0.4, 1))
        btn_save.bind(on_release=self.save_edits)
        btn_back = Button(text="CANCEL", size_hint_y=None, height='40dp')
        btn_back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn_save); layout.add_widget(btn_back); self.add_widget(layout)

    def save_edits(self, instance):
        new_data = []
        for inp in self.inputs:
            new_data.append({'q': inp['q'].text, 'o': [o.text for o in inp['o']], 'a': inp['a'].text.upper().strip()})
        App.get_running_app().quiz_data = new_data
        self.manager.current = 'menu'

# --- SCREEN 4: IMPORT & PARSE ---
class ImportScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        self.f_in = TextInput(hint_text="Folder Name (e.g., Science)", size_hint_y=None, height='45dp', multiline=False)
        self.t_in = TextInput(hint_text="Quiz Title", size_hint_y=None, height='45dp', multiline=False)
        self.q_in = TextInput(hint_text="Paste Questions Here...", multiline=True)
        self.a_in = TextInput(hint_text="Key (1.A 2.B...)", size_hint_y=None, height='80dp')
        btn_save = Button(text="💾 SAVE & EDIT", size_hint_y=None, height='50dp', background_color=(0, 0.7, 1, 1))
        btn_save.bind(on_release=self.parse_and_save)
        btn_import = Button(text="📥 SYNC FROM DOWNLOADS", size_hint_y=None, height='50dp', background_color=(0.2, 0.8, 0.2, 1))
        btn_import.bind(on_release=self.sync_from_phone)
        btn_back = Button(text="BACK", size_hint_y=None, height='40dp')
        btn_back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(self.f_in); layout.add_widget(self.t_in)
        layout.add_widget(self.q_in); layout.add_widget(self.a_in)
        layout.add_widget(btn_save); layout.add_widget(btn_import); layout.add_widget(btn_back)
        self.add_widget(layout)

    def sync_from_phone(self, instance):
        target_f = self.f_in.text.strip() or "Imported"
        dest = os.path.join(BASE_DIR, target_f)
        if not os.path.exists(dest): os.makedirs(dest)
        try:
            found = False
            for f in os.listdir(DOWNLOADS_PATH):
                if f.endswith('.quiz'):
                    shutil.copy(os.path.join(DOWNLOADS_PATH, f), os.path.join(dest, f))
                    found = True
            if found:
                self.manager.current = 'browse'
            else:
                App.get_running_app().show_popup("Not Found", "No .quiz files in Downloads.")
        except Exception:
            App.get_running_app().show_popup("Error", "Check storage permissions.")

    def parse_and_save(self, instance):
        folder, title = self.f_in.text or "General", self.t_in.text or "Quiz"
        dest = os.path.join(BASE_DIR, folder)
        if not os.path.exists(dest): os.makedirs(dest)
        
        ans_map = {m[0]: m[1] for m in re.findall(r"(\d+)\s*[\.\)\:]?\s*([A-D])", self.a_in.text.upper())}
        chunks = re.split(r"(?:\n|^)(\d+)\s*[\.\)\:]\s*", self.q_in.text)
        parsed = []
        for i in range(1, len(chunks), 2):
            q_num, body = chunks[i], chunks[i+1]
            q_txt = re.split(r"\s[A]\s*[\.\)\:]", " " + body, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            opts = re.findall(r"([A-D])\s*[\.\)\:]\s*(.*?)(?=\s+[A-D]\s*[\.\)\:]|\n\s*[A-D]\s*[\.\)\:]|$)", body, re.DOTALL | re.IGNORECASE)
            d = {l.upper(): t.strip() for l, t in opts}
            parsed.append({"q": q_txt, "o": [d.get(c, "") for c in "ABCD"], "a": ans_map.get(q_num, "A")})
        
        if parsed:
            fn = f"{re.sub(r'[^a-zA-Z0-9]', '_', title)}.quiz"
            with open(os.path.join(dest, fn), "w", encoding="utf-8") as f: json.dump(parsed, f, indent=4)
            App.get_running_app().quiz_data = parsed
            self.manager.current = 'edit'

# --- SCREEN 5: PLAY SCREEN ---
class PlayScreen(Screen):
    def on_enter(self):
        self.can_click = True; self.load_q()

    def load_q(self):
        self.clear_widgets(); self.can_click = True
        app = App.get_running_app()
        if app.current_q_idx >= len(app.quiz_data):
            l = BoxLayout(orientation='vertical', padding=50, spacing=20)
            l.add_widget(Label(text="FINISH!", font_size='30sp', bold=True))
            l.add_widget(Label(text=f"SCORE: {app.score} / {len(app.quiz_data)}", font_size='20sp'))
            b = Button(text="BACK TO MENU", size_hint_y=None, height='60dp', background_color=(0.2, 0.6, 1, 1))
            b.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
            l.add_widget(b); self.add_widget(l); return
        
        data = app.quiz_data[app.current_q_idx]
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text=f"QUESTION {app.current_q_idx+1}", size_hint_y=None, height='30dp', color=(0.8, 0.8, 0.8, 1)))
        
        # Ensure long questions wrap correctly on phone screens
        layout.add_widget(Label(text=data['q'], font_size='18sp', halign='center', text_size=(Window.width-40, None)))
        
        self.btns = {}
        for i, opt in enumerate(data['o']):
            char = chr(65+i)
            btn = Button(text=f"{char}. {opt}", size_hint_y=None, height='65dp', background_normal='', background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=self.check_ans); self.btns[char] = btn; layout.add_widget(btn)
        self.add_widget(layout)

    def check_ans(self, instance):
        if not self.can_click: return
        self.can_click = False; app = App.get_running_app()
        choice, correct = instance.text[0], app.quiz_data[app.current_q_idx]['a']
        
        if choice == correct:
            instance.background_color = (0, 0.8, 0.2, 1); app.score += 1
            if app.snd_correct: app.snd_correct.play()
        else:
            instance.background_color = (0.8, 0.1, 0.1, 1)
            if correct in self.btns: self.btns[correct].background_color = (0, 0.6, 0.2, 1)
            if app.snd_wrong: app.snd_wrong.play()
            
        Clock.schedule_once(lambda dt: self.next_q(), 1.3)

    def next_q(self):
        App.get_running_app().current_q_idx += 1; self.load_q()

if __name__ == '__main__':
    QuizApp().run()
