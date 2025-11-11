import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import time
import io
from PIL import Image, ImageTk
import threading

class RobloxBadgeRemoverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Badge Remover")
        self.root.geometry("1200x700")

        # Variables
        self.roblox_token = tk.StringVar()
        self.user_id = tk.StringVar()
        self.exempt_games = tk.StringVar()
        self.exempt_keywords = tk.StringVar()
        self.dry_run = tk.BooleanVar(value=True)
        self.session = None
        self.badges_data = []
        self.game_info = {}  # Cache for game names and thumbnails
        self.tree = None
        self.item_map = {}  # Map badge_id to tree item
        self.avatar_img = None

        self.setup_ui()

    def setup_ui(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="ROBLOSECURITY:").grid(row=0, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.roblox_token, width=50, show="*").grid(row=0, column=1, padx=5)
        ttk.Label(input_frame, text="User ID:").grid(row=1, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.user_id, width=20).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(input_frame, text="Exempt Games (comma-separated IDs):").grid(row=2, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.exempt_games, width=50).grid(row=2, column=1, padx=5)
        ttk.Label(input_frame, text="Exempt Keywords (comma-separated):").grid(row=3, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.exempt_keywords, width=50).grid(row=3, column=1, padx=5)

        ttk.Checkbutton(input_frame, text="Dry Run (Preview Only)", variable=self.dry_run).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        # Buttons
        ttk.Button(input_frame, text="Load Badges", command=self.load_badges_thread).grid(row=5, column=0, pady=5)
        ttk.Button(input_frame, text="Delete Selected", command=self.delete_selected_thread).grid(row=5, column=1, pady=5)
        ttk.Button(input_frame, text="Select All", command=self.select_all).grid(row=5, column=2, pady=5, padx=5)

        # Avatar display
        self.avatar_label = ttk.Label(input_frame)
        self.avatar_label.grid(row=0, column=3, rowspan=5, padx=10)

        # Treeview Frame
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Select", "Badge ID", "Name", "Game Name", "Description")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=50 if col=="Select" else 150)

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        self.tree.bind("<Button-1>", self.on_tree_click)

        # Status Log
        log_frame = ttk.LabelFrame(self.root, text="Status Log", padding=5)
        log_frame.pack(fill="x", padx=10, pady=5)
        self.status_log = scrolledtext.ScrolledText(log_frame, height=8, state="disabled", wrap=tk.WORD)
        self.status_log.pack(fill="both", expand=True)

    def log(self, message):
        self.status_log.config(state="normal")
        self.status_log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.status_log.see(tk.END)
        self.status_log.config(state="disabled")
        self.root.update_idletasks()

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if item and col == "#1":
            current = self.tree.set(item, "Select")
            new_val = "☐" if current == "☑" else "☑"
            self.tree.set(item, "Select", new_val)

    def setup_session(self):
        self.session = requests.Session()
        self.session.cookies['.ROBLOSECURITY'] = self.roblox_token.get().strip()
        header_resp = self.session.post('https://catalog.roblox.com/v1/topic/get-topics')
        if 'X-CSRF-TOKEN' in header_resp.headers:
            self.session.headers['X-CSRF-TOKEN'] = header_resp.headers['X-CSRF-TOKEN']

    def load_avatar(self):
        try:
            if not self.session:
                self.setup_session()
            r = self.session.get("https://users.roblox.com/v1/users/authenticated")
            if r.status_code != 200:
                self.log("Failed to fetch user info for avatar")
                return
            user_info = r.json()
            user_id = str(user_info.get("id"))
            avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=150&height=150&format=png"
            resp = requests.get(avatar_url)
            if resp.status_code == 200:
                pil_img = Image.open(io.BytesIO(resp.content)).resize((100,100))
                self.avatar_img = ImageTk.PhotoImage(pil_img)
                self.avatar_label.config(image=self.avatar_img)
                self.avatar_label.image = self.avatar_img
        except Exception as e:
            self.log(f"Failed to load avatar: {str(e)}")

    def fetch_game_info(self, game_ids):
        if not game_ids:
            return
        unique_ids = list(set(game_ids))
        batch_size = 100
        for i in range(0, len(unique_ids), batch_size):
            batch = unique_ids[i:i+batch_size]
            universe_str = ",".join(map(str, batch))
            r = self.session.get(f"https://games.roblox.com/v1/games?universeIds={universe_str}")
            if r.status_code == 200:
                games = r.json().get('data', [])
                for game in games:
                    gid = str(game['id'])
                    self.game_info[gid] = {'name': game.get('name', gid)}
            thumb_r = self.session.get(f"https://thumbnails.roblox.com/v1/games/icons?universeIds={universe_str}&size=150x150&format=Png")
            if thumb_r.status_code == 200:
                thumbs = thumb_r.json().get('data', [])
                for thumb in thumbs:
                    gid = str(thumb['targetId'])
                    if gid in self.game_info:
                        self.game_info[gid]['thumb_url'] = thumb['imageUrl']

    def load_badges(self):
        token = self.roblox_token.get().strip()
        uid = self.user_id.get().strip()
        if not token or not uid:
            messagebox.showerror("Error", "Please enter ROBLOSECURITY and User ID.")
            return
        try:
            self.setup_session()
            self.load_avatar()
            self.badges_data = []
            self.game_info = {}
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.item_map = {}

            exempt_games_list = [g.strip() for g in self.exempt_games.get().split(',') if g.strip()]
            exempt_keywords_list = [k.strip() for k in self.exempt_keywords.get().split(',') if k.strip()]

            self.log("Loading badges...")
            cursor = ''
            page = 0
            game_ids = []

            while True:
                url = f'https://badges.roblox.com/v1/users/{uid}/badges?sortOrder=Desc&limit=100'
                if cursor:
                    url += f'&cursor={cursor}'
                r = self.session.get(url)
                if r.status_code != 200:
                    self.log(f"API error fetching badges: {r.status_code}")
                    return
                content = r.json()
                data = content.get('data', [])
                cursor = content.get('nextPageCursor')

                for badge in data:
                    badge_data = {
                        'id': str(badge['id']),
                        'name': badge['name'],
                        'description': badge.get('description',''),
                        'gameID': str(badge['awarder']['id'])
                    }
                    game_ids.append(badge_data['gameID'])
                    self.badges_data.append(badge_data)

                page += 1
                self.log(f"Scraped page {page} ({len(data)} badges)")
                if not cursor:
                    break

            self.fetch_game_info(game_ids)

            game_exempt = 0
            keyword_exempt = 0
            total = len(self.badges_data)

            for badge in self.badges_data:
                gid = badge['gameID']
                game_name = self.game_info.get(gid, {}).get('name', f"Unknown Game ({gid})")
                desc_snip = (badge['description'][:50]+"...") if len(badge['description'])>50 else badge['description']

                exempt_reason = ""
                if gid in exempt_games_list:
                    exempt_reason = " (Exempt: Game)"
                    game_exempt += 1
                else:
                    for kw in exempt_keywords_list:
                        if kw.lower() in badge['name'].lower() or kw.lower() in badge['description'].lower():
                            exempt_reason = f" (Exempt: Keyword '{kw}')"
                            keyword_exempt += 1
                            break

                select_val = "⚠"+exempt_reason if exempt_reason else "☐"

                item = self.tree.insert("", "end", values=(select_val, badge['id'], badge['name'], game_name, desc_snip))
                self.item_map[badge['id']] = item

            self.log(f"Loaded {total} badges. Exempt by game: {game_exempt}, by keyword: {keyword_exempt}. Unique games: {len(self.game_info)}")

        except Exception as e:
            self.log(f"Error loading badges: {str(e)}")
            messagebox.showerror("Error", str(e))

    def load_badges_thread(self):
        threading.Thread(target=self.load_badges, daemon=True).start()

    def delete_selected(self):
        if self.dry_run.get():
            selected_count = sum(1 for item in self.tree.get_children() if self.tree.set(item,"Select").startswith("☑"))
            self.log(f"Dry run: Would delete {selected_count} badges.")
            return
        selected_ids = []
        for item in self.tree.get_children():
            select_val = self.tree.set(item,"Select")
            if select_val.startswith("☑"):
                badge_id = self.tree.item(item)['values'][1]
                selected_ids.append(badge_id)
        if not selected_ids:
            messagebox.showwarning("No Selection","No badges selected for deletion.")
            return
        if not messagebox.askyesno("Confirm Deletion", f"Delete {len(selected_ids)} badges permanently?"):
            return
        deleted = 0
        failed = 0
        for badge_id in selected_ids:
            if self.delete_badge(badge_id):
                deleted += 1
                if badge_id in self.item_map:
                    self.tree.delete(self.item_map[badge_id])
                    del self.item_map[badge_id]
            else:
                failed += 1
        self.log(f"Deletion complete: {deleted} successful, {failed} failed.")

    def delete_badge(self,badge_id):
        max_retries = 5
        retry = 0
        while retry<max_retries:
            try:
                r = self.session.delete(f'https://badges.roblox.com/v1/user/badges/{badge_id}')
                time.sleep(0.5)
                if r.status_code == 200:
                    self.log(f"Deleted badge {badge_id}")
                    return True
                elif r.status_code==429:
                    delay = 2**retry
                    self.log(f"Rate limited for {badge_id} (retry {retry+1}/{max_retries}), waiting {delay}s...")
                    time.sleep(delay)
                    retry += 1
                else:
                    self.log(f"Failed to delete {badge_id}: {r.status_code} - {r.text[:100]}")
                    return False
            except Exception as e:
                self.log(f"Exception deleting {badge_id}: {str(e)}")
                return False
        self.log(f"Gave up on {badge_id} after {max_retries} retries")
        return False

    def delete_selected_thread(self):
        threading.Thread(target=self.delete_selected, daemon=True).start()

    def select_all(self):
        for item in self.tree.get_children():
            current_val = self.tree.set(item, "Select")
            if not current_val.startswith("⚠"):
                self.tree.set(item,"Select","☑")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobloxBadgeRemoverGUI(root)
    root.mainloop()
