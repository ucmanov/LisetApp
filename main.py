import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, os, json, csv
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), "liset.db")

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    display_name TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS meds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sheets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient TEXT,
                    date TEXT,
                    med_id INTEGER,
                    dose TEXT,
                    instr TEXT,
                    created_at TEXT
                )""")
    conn.commit()
    # create default admin if none
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0]==0:
        cur.execute("INSERT INTO users (username,password,display_name) VALUES (?,?,?)", ("admin","1234","Админ"))
    conn.commit()
    conn.close()

class LisetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Liset — Учёт листов назначений")
        self.lang = "ru"  # or "uz"
        self.create_login()

    def t(self, ru, uz):
        return ru if self.lang=="ru" else uz

    def create_login(self):
        for w in self.root.winfo_children(): w.destroy()
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=self.t("Вход в Liset","Lisetga kirish"), font=("Segoe UI",14)).pack(pady=6)
        ttk.Label(frm, text=self.t("Логин","Login")).pack(anchor="w")
        self.e_user = ttk.Entry(frm); self.e_user.pack(fill="x")
        ttk.Label(frm, text=self.t("Пароль","Parol")).pack(anchor="w")
        self.e_pass = ttk.Entry(frm, show="*"); self.e_pass.pack(fill="x")
        ttk.Button(frm, text=self.t("Войти","Kirish"), command=self.login).pack(pady=8)
        ttk.Button(frm, text=self.t("Меню языка: Русский/Ўзбек","Til: Rus/O'zbek"), command=self.toggle_lang).pack()

    def toggle_lang(self):
        self.lang = "uz" if self.lang=="ru" else "ru"
        self.create_login()

    def login(self):
        user = self.e_user.get().strip()
        pwd = self.e_pass.get().strip()
        conn = sqlite3.connect(DB); cur=conn.cursor()
        cur.execute("SELECT id,display_name FROM users WHERE username=? AND password=?", (user,pwd))
        r = cur.fetchone(); conn.close()
        if r:
            self.user = {"id":r[0],"display_name":r[1]}
            self.create_main()
        else:
            messagebox.showerror(self.t("Ошибка","Xato"), self.t("Неверный логин или пароль","Noto'g'ri login yoki parol"))

    def create_main(self):
        for w in self.root.winfo_children(): w.destroy()
        pan = ttk.Panedwindow(self.root, orient="horizontal")
        pan.pack(fill="both", expand=True)
        left = ttk.Frame(pan, width=300, padding=8)
        right = ttk.Frame(pan, padding=8)
        pan.add(left); pan.add(right)

        # top controls
        ttk.Label(left, text=self.t("Пользователь: ","Foydalanuvchi: ")+self.user["display_name"]).pack(anchor="w")
        ttk.Button(left, text=self.t("Добавить профиль","Profil qo'shish"), command=self.add_profile).pack(fill="x", pady=2)
        ttk.Button(left, text=self.t("Все препараты","Barcha dorilar"), command=self.show_meds).pack(fill="x", pady=2)
        ttk.Button(left, text=self.t("Экспорт/Импорт","Eksport/Import"), command=self.show_export).pack(fill="x", pady=2)
        ttk.Button(left, text=self.t("Резервная копия","Zaxira"), command=self.backup_db).pack(fill="x", pady=2)
        ttk.Button(left, text=self.t("Выход","Chiqish"), command=self.create_login).pack(fill="x", pady=12)

        # sheet table
        self.tree = ttk.Treeview(right, columns=("patient","date","med","dose","instr"), show="headings")
        for c,h in [("patient",self.t("Пациент","Bemor")),("date",self.t("Дата","Sana")),("med",self.t("Препарат","Dori")),("dose",self.t("Доза","Doza")),("instr",self.t("Инструкция","Ko'rsatma"))]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True)
        frm = ttk.Frame(right)
        frm.pack(fill="x", pady=6)
        ttk.Button(frm, text=self.t("Добавить лист","List qo'shish"), command=self.add_sheet).pack(side="left")
        ttk.Button(frm, text=self.t("Редактировать","Tahrirlash"), command=self.edit_sheet).pack(side="left", padx=6)
        ttk.Button(frm, text=self.t("Удалить","O'chirish"), command=self.del_sheet).pack(side="left")
        self.load_sheets()

    def add_profile(self):
        def save():
            un = e1.get().strip(); pw=e2.get().strip(); dn=e3.get().strip()
            if not un or not pw: messagebox.showerror("Error","Введите логин и пароль"); return
            conn=sqlite3.connect(DB); cur=conn.cursor()
            try:
                cur.execute("INSERT INTO users (username,password,display_name) VALUES (?,?,?)",(un,pw,dn or un))
                conn.commit(); conn.close(); top.destroy(); messagebox.showinfo("Ok","Профиль создан")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        top = tk.Toplevel(self.root); top.title(self.t("Новый профиль","Yangi profil"))
        ttk.Label(top, text=self.t("Логин","Login")).pack(); e1=ttk.Entry(top); e1.pack()
        ttk.Label(top, text=self.t("Пароль","Parol")).pack(); e2=ttk.Entry(top); e2.pack()
        ttk.Label(top, text=self.t("Отображаемое имя (необязательно)","Ko'rsatish nomi (ixtiyoriy)")).pack(); e3=ttk.Entry(top); e3.pack()
        ttk.Button(top, text=self.t("Сохранить","Saqlash"), command=save).pack(pady=6)

    def show_meds(self):
        top = tk.Toplevel(self.root); top.title(self.t("Препараты","Dorilar"))
        lst = tk.Listbox(top); lst.pack(fill="both", expand=True)
        conn=sqlite3.connect(DB); cur=conn.cursor(); cur.execute("SELECT name FROM meds ORDER BY name"); rows=cur.fetchall(); conn.close()
        for r in rows: lst.insert("end", r[0])
        frm = ttk.Frame(top); frm.pack(fill="x")
        e=ttk.Entry(frm); e.pack(side="left", fill="x", expand=True)
        def add():
            name=e.get().strip()
            if not name: return
            conn=sqlite3.connect(DB); cur=conn.cursor(); 
            try:
                cur.execute("INSERT INTO meds (name) VALUES (?)",(name,)); conn.commit(); conn.close(); lst.insert("end", name); e.delete(0,"end")
            except Exception as ex: messagebox.showerror("Error", str(ex))
        ttk.Button(frm, text=self.t("Добавить","Qo'shish"), command=add).pack(side="left")

    def show_export(self):
        top = tk.Toplevel(self.root); top.title(self.t("Экспорт / Импорт","Eksport / Import"))
        ttk.Button(top, text=self.t("Экспорт в CSV","CSV ga eksport"), command=self.export_csv).pack(fill="x", pady=4)
        ttk.Button(top, text=self.t("Экспорт в JSON","JSON ga eksport"), command=self.export_json).pack(fill="x", pady=4)
        ttk.Button(top, text=self.t("Импорт CSV","CSV import"), command=self.import_csv).pack(fill="x", pady=4)
        ttk.Button(top, text=self.t("Импорт JSON","JSON import"), command=self.import_json).pack(fill="x", pady=4)

    def export_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not p: return
        conn=sqlite3.connect(DB); cur=conn.cursor(); cur.execute("SELECT patient,date,med_id,dose,instr,created_at FROM sheets"); rows=cur.fetchall(); conn.close()
        # expand med_id
        conn=sqlite3.connect(DB); cur=conn.cursor()
        with open(p,"w",newline="",encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["patient","date","med","dose","instr","created_at"])
            for r in rows:
                cur.execute("SELECT name FROM meds WHERE id=?", (r[2],))
                med = cur.fetchone()
                medname = med[0] if med else ""
                writer.writerow([r[0], r[1], medname, r[3], r[4], r[5]])
        conn.close()
        messagebox.showinfo("Ok", self.t("Экспорт завершён","Eksport tugadi"))

    def export_json(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not p: return
        conn=sqlite3.connect(DB); cur=conn.cursor(); cur.execute("SELECT id,patient,date,med_id,dose,instr,created_at FROM sheets"); rows=cur.fetchall()
        data = []
        for r in rows:
            cur.execute("SELECT name FROM meds WHERE id=?", (r[3],))
            med = cur.fetchone()
            data.append({"patient":r[1],"date":r[2],"med": med[0] if med else "","dose":r[4],"instr":r[5],"created_at":r[6]})
        conn.close()
        with open(p,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
        messagebox.showinfo("Ok", self.t("Экспорт завершён","Eksport tugadi"))

    def import_csv(self):
        p = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if not p: return
        conn=sqlite3.connect(DB); cur=conn.cursor()
        with open(p, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                medname = row.get("med","").strip()
                med_id = None
                if medname:
                    cur.execute("SELECT id FROM meds WHERE name=?", (medname,))
                    r = cur.fetchone()
                    if r: med_id = r[0]
                    else:
                        cur.execute("INSERT INTO meds (name) VALUES (?)",(medname,)); med_id = cur.lastrowid
                cur.execute("INSERT INTO sheets (patient,date,med_id,dose,instr,created_at) VALUES (?,?,?,?,?,?)",
                            (row.get("patient",""), row.get("date",""), med_id, row.get("dose",""), row.get("instr",""), datetime.utcnow().isoformat()))
        conn.commit(); conn.close(); messagebox.showinfo("Ok", self.t("Импорт завершён","Import tugadi")); self.load_sheets()

    def import_json(self):
        p = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not p: return
        with open(p, encoding="utf-8") as f: data=json.load(f)
        conn=sqlite3.connect(DB); cur=conn.cursor()
        for item in data:
            medname = item.get("med","").strip()
            med_id = None
            if medname:
                cur.execute("SELECT id FROM meds WHERE name=?", (medname,))
                r = cur.fetchone()
                if r: med_id = r[0]
                else:
                    cur.execute("INSERT INTO meds (name) VALUES (?)",(medname,)); med_id = cur.lastrowid
            cur.execute("INSERT INTO sheets (patient,date,med_id,dose,instr,created_at) VALUES (?,?,?,?,?,?)",
                        (item.get("patient",""), item.get("date",""), med_id, item.get("dose",""), item.get("instr",""), datetime.utcnow().isoformat()))
        conn.commit(); conn.close(); messagebox.showinfo("Ok", self.t("Импорт завершён","Import tugadi")); self.load_sheets()

    def backup_db(self):
        p = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB","*.db")])
        if not p: return
        try:
            import shutil; shutil.copyfile(DB,p)
            messagebox.showinfo("Ok", self.t("Резервная копия создана","Zaxira yaratildi"))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_sheets(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn=sqlite3.connect(DB); cur=conn.cursor()
        cur.execute("SELECT s.id,s.patient,s.date,m.name,s.dose,s.instr FROM sheets s LEFT JOIN meds m ON s.med_id=m.id ORDER BY s.date DESC")
        for r in cur.fetchall():
            self.tree.insert("", "end", iid=r[0], values=(r[1], r[2], r[3] or "", r[4], r[5]))
        conn.close()

    def add_sheet(self):
        top = tk.Toplevel(self.root); top.title(self.t("Новый лист","Yangi list"))
        ttk.Label(top, text=self.t("Пациент","Bemor")).pack(); e1=ttk.Entry(top); e1.pack(fill="x")
        ttk.Label(top, text=self.t("Дата (YYYY-MM-DD)","Sana (YYYY-MM-DD)")).pack(); e2=ttk.Entry(top); e2.pack(fill="x"); e2.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ttk.Label(top, text=self.t("Препарат","Dori")).pack(); e3=ttk.Entry(top); e3.pack(fill="x")
        ttk.Label(top, text=self.t("Доза","Doza")).pack(); e4=ttk.Entry(top); e4.pack(fill="x")
        ttk.Label(top, text=self.t("Инструкция","Ko'rsatma")).pack(); e5=ttk.Entry(top); e5.pack(fill="x")
        def save():
            patient=e1.get().strip(); date=e2.get().strip(); medname=e3.get().strip(); dose=e4.get().strip(); instr=e5.get().strip()
            med_id = None
            conn=sqlite3.connect(DB); cur=conn.cursor()
            if medname:
                cur.execute("SELECT id FROM meds WHERE name=?", (medname,)); r=cur.fetchone()
                if r: med_id=r[0]
                else:
                    cur.execute("INSERT INTO meds (name) VALUES (?)",(medname,)); med_id=cur.lastrowid
            cur.execute("INSERT INTO sheets (patient,date,med_id,dose,instr,created_at) VALUES (?,?,?,?,?,?)",
                        (patient,date,med_id,dose,instr, datetime.utcnow().isoformat()))
            conn.commit(); conn.close(); top.destroy(); self.load_sheets()
        ttk.Button(top, text=self.t("Сохранить","Saqlash"), command=save).pack(pady=6)

    def edit_sheet(self):
        sel = self.tree.selection()
        if not sel: return
        sid = sel[0]
        conn=sqlite3.connect(DB); cur=conn.cursor(); cur.execute("SELECT patient,date,med_id,dose,instr FROM sheets WHERE id=?", (sid,)); r=cur.fetchone(); conn.close()
        if not r: return
        top = tk.Toplevel(self.root); top.title(self.t("Редактировать","Tahrirlash"))
        ttk.Label(top, text=self.t("Пациент","Bemor")).pack(); e1=ttk.Entry(top); e1.pack(fill="x"); e1.insert(0,r[0])
        ttk.Label(top, text=self.t("Дата (YYYY-MM-DD)","Sana (YYYY-MM-DD)")).pack(); e2=ttk.Entry(top); e2.pack(fill="x"); e2.insert(0,r[1])
        medname = ""
        if r[2]:
            conn=sqlite3.connect(DB); cur=conn.cursor(); cur.execute("SELECT name FROM meds WHERE id=?", (r[2],)); mr=cur.fetchone(); conn.close()
            medname = mr[0] if mr else ""
        ttk.Label(top, text=self.t("Препарат","Dori")).pack(); e3=ttk.Entry(top); e3.pack(fill="x"); e3.insert(0,medname)
        ttk.Label(top, text=self.t("Доза","Doza")).pack(); e4=ttk.Entry(top); e4.pack(fill="x"); e4.insert(0,r[3])
        ttk.Label(top, text=self.t("Инструкция","Ko'rsatma")).pack(); e5=ttk.Entry(top); e5.pack(fill="x"); e5.insert(0,r[4])
        def save():
            patient=e1.get().strip(); date=e2.get().strip(); medname=e3.get().strip(); dose=e4.get().strip(); instr=e5.get().strip()
            med_id = None
            conn=sqlite3.connect(DB); cur=conn.cursor()
            if medname:
                cur.execute("SELECT id FROM meds WHERE name=?", (medname,)); rr=cur.fetchone()
                if rr: med_id=rr[0]
                else:
                    cur.execute("INSERT INTO meds (name) VALUES (?)",(medname,)); med_id=cur.lastrowid
            cur.execute("UPDATE sheets SET patient=?,date=?,med_id=?,dose=?,instr=? WHERE id=?",(patient,date,med_id,dose,instr,sid))
            conn.commit(); conn.close(); top.destroy(); self.load_sheets()
        ttk.Button(top, text=self.t("Сохранить","Saqlash"), command=save).pack(pady=6)

    def del_sheet(self):
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("Confirm", self.t("Удалить выбранный лист?","Tanlangan listni oʻchirish?")): return
        sid = sel[0]
        conn=sqlite3.connect(DB); cur=conn.cursor(); cur.execute("DELETE FROM sheets WHERE id=?", (sid,)); conn.commit(); conn.close(); self.load_sheets()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = LisetApp(root)
    root.geometry("900x600")
    root.mainloop()
