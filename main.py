import customtkinter as ctk #Modern ve dinamik kullanıcı arayüzü bileşenleri
from PIL import Image, ImageTk # Görsel işleme ve format dönüştürme işlemleri
from tkinter import messagebox  # Standart kullanıcı bilgilendirme ve hata pencereleri
import os  #Dosya yolları ve dizin yönetimi
import tkinter as tk # Temel arayüz ve Canvas çizim araçları
from collections import Counter #Veri setindeki öğe frekanslarını (en çok tekrar eden) hesaplamak için
import sys # Sistem düzeyinde parametreler ve çıkış işlemleri
import datetime  # Kayıtların tarih ve saat bilgisini tutmak için
import pyodbc  # Microsoft SQL Server veritabanı sürücüsü ve bağlantısı
import hashlib # # Şifrelerin güvenli bir şekilde (SHA-256) maskelenmesi için

# ==========================================
# GÖRSEL TEMA VE RENK YAPILANDIRMASI
# ==========================================
ctk.set_appearance_mode("Dark")
CYBER_BLUE = "#00f0ff" # Uygulamanın ana vurgu rengi
CYBER_RED = "#ff004c" # Kritik uyarı ve hata rengi
CYBER_YELLOW = "#f1c40f" # İstatistiksel veri vurgu rengi
CYBER_GREEN = "#2ecc71" # Başarı ve onay mesajı rengi
BG_COLOR = "#0b0b0b"  # Ana arka plan rengi
PANEL_COLOR = "#141414" # Kontrol panelleri arka plan rengi


IMG_WIDTH = 600  # Vücut haritası görsel genişliği
IMG_HEIGHT = 750  # Vücut haritası görsel yüksekliği


# ==========================================
#  VERİTABANI İŞLEMLERİ
# ==========================================
class DatabaseManager:
    def __init__(self):
        # SQL Server Express bağlantı parametreleri
        self.server = r'YIGIT\SQLEXPRESS'
        self.database = 'TSmartDB'
        self.conn_str = f'DRIVER={{SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;'

    def baglan(self):
        """Aktif bir veritabanı bağlantısı kurar."""
        try: return pyodbc.connect(self.conn_str)
        except: return None

    def hash_sifre(self, sifre):
        """Güvenlik: Girilen şifreyi SHA-256 algoritmasıyla şifreler."""
        return hashlib.sha256(sifre.encode()).hexdigest()

    def giris_yap(self, kadi, sifre):
        """Stored Procedure çağrısı ile kullanıcı kimlik doğrulaması yapar."""
        conn = self.baglan()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("{CALL sp_GirisYap (?, ?)}", (kadi, self.hash_sifre(sifre)))
        user = cursor.fetchone(); conn.close(); return user

    def kayit_ol(self, ad, soyad, kadi, sifre):
        """Yeni sporcu kaydını veritabanına güvenli şifreleme ile işler."""
        conn = self.baglan()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("{CALL sp_KayitOl (?, ?, ?)}", (ad + " " + soyad, kadi, self.hash_sifre(sifre)))
            conn.commit(); conn.close(); return True
        except: return False

    def mac_ekle(self, user_id, veri):
        """Sporcunun girdiği maç istatistiklerini tabloya kaydeder."""
        conn = self.baglan(); cursor = conn.cursor()
        cursor.execute("INSERT INTO Maclar (KullaniciID, Tarih, Rakip, Kulup, Skor, Sehir, Hata, Sonuc) VALUES (?,?,?,?,?,?,?,?)",
                       (user_id, veri['tarih'], veri['rakip'], veri['kulup'], veri['skor'], veri['sehir'], veri['hata'], veri['sonuc']))
        conn.commit(); conn.close()

    def tum_maclari_getir(self, user_id):
        """Oturum açan sporcuya ait tüm maç geçmişini listeler."""
        conn = self.baglan(); cursor = conn.cursor()
        cursor.execute("SELECT Tarih, Rakip, Kulup, Skor, Sehir, Hata, Sonuc FROM Maclar WHERE KullaniciID = ? ORDER BY MacID DESC", (user_id,))
        rows = cursor.fetchall(); conn.close()
        return [{"tarih": r[0], "rakip": r[1], "kulup": r[2], "skor": r[3], "sehir": r[4], "hata": r[5], "sonuc": r[6]} for r in rows]

    def tum_analizleri_getir(self, user_id):
        """Daha önce oluşturulmuş Antrenör raporlarını veritabanından çeker."""
        conn = self.baglan(); cursor = conn.cursor()
        cursor.execute("SELECT Tarih, Bolgeler, Hata, Oneri FROM Analizler WHERE KullaniciID = ? ORDER BY AnalizID DESC", (user_id,))
        rows = cursor.fetchall(); conn.close()
        return [{"tarih": r[0], "bolgeler": r[1], "hata": r[2], "oneri": r[3]} for r in rows]

    def analiz_verisi_getir(self, user_id):
        """İstatistik: Maç geçmişindeki en baskın teknik hatayı hesaplar."""
        maclar = self.tum_maclari_getir(user_id)
        if not maclar: return "Genel Hata", 0
        hatalar = [m["hata"] for m in maclar if m["hata"]]
        if not hatalar: return "Genel Hata", 0
        return Counter(hatalar).most_common(1)[0]

    def analiz_ekle(self, user_id, bolgeler, hata, oneri):
        """Teknik analiz sonucunu kalıcı rapor olarak kaydeder."""
        conn = self.baglan(); cursor = conn.cursor()
        tarih = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO Analizler (KullaniciID, Tarih, Bolgeler, Hata, Oneri) VALUES (?,?,?,?,?)",
                       (user_id, tarih, bolgeler, hata, oneri))
        conn.commit(); conn.close()
    
    def admin_istatistik_getir(self):
        """Yönetici Paneli: Sistemdeki toplam kullanıcı ve analiz sayılarını getirir."""
        conn = self.baglan()
        conn = self.baglan()
        if not conn: return 0, 0
        try:
            cursor = conn.cursor()
           
            cursor.execute("SELECT (SELECT COUNT(*) FROM Kullanicilar), (SELECT COUNT(*) FROM Analizler)")
            counts = cursor.fetchone()
            conn.close()
           
            return (counts[0], counts[1]) if counts else (0, 0)
        except:
            if conn: conn.close()
            return 0, 0
    
    def sifre_guncelle(self, kadi, yeni_sifre):
        """Kullanıcı var mı kontrol eder, varsa şifreyi hashleyerek günceller."""
        conn = self.baglan()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # 1. Kontrol: Kullanıcı veritabanında var mı? (Kritik kontrol burada yapılıyor)
            cursor.execute("SELECT COUNT(*) FROM Kullanicilar WHERE KullaniciAdi = ?", (kadi,))
            if cursor.fetchone()[0] == 0:
                conn.close()
                return False  # Kullanıcı yoksa uyarı verir
            
            # 2. Güncelleme: Şifre SHA-256 ile hashlenir
            cursor.execute("UPDATE Kullanicilar SET Sifre = ? WHERE KullaniciAdi = ?",
                           (self.hash_sifre(yeni_sifre), kadi))
            conn.commit()
            conn.close()
            return True
        except:
            if conn: conn.close()
            return False
        

db = DatabaseManager() # Veritabanı yönetim nesnesi


# ==========================================
# UI BİLEŞENİ: İNTERAKTİF VÜCUT HARİTASI
# ==========================================
class ClickableZone:
    """Canvas üzerindeki poligonları tıklanabilir bölgelere dönüştüren sınıf."""
    def __init__(self, canvas, points, region_name, app_reference):
       
        self.canvas = canvas;
        self.name = region_name;
        self.app = app_reference;
        self.is_selected = False
        # Bölge poligonu ve seçildiğinde oluşacak çerçeve
        self.polygon = canvas.create_polygon(points, fill="", outline="", width=1, tags=f"zone_{region_name}")
        self.border = canvas.create_polygon(points, fill="", outline="", width=3, state="disabled")
        
        # Bölge isim etiketlerinin görsel merkezine yerleştirilmesi
        try:
            xs = points[0::2]
            ys = points[1::2]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            # Font boyutu görselle orantılı
            self.label = canvas.create_text(cx, cy, text=region_name, fill="", font=("Impact", 14), state="disabled")
        except:
            self.label = None
        # Fare olaylarını poligonlara bağlama
        self.canvas.tag_bind(self.polygon, "<Enter>", self.on_enter)
        self.canvas.tag_bind(self.polygon, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.polygon, "<Button-1>", self.on_click)
    
    def on_enter(self, event):
        if self.is_selected: return
        self.canvas.config(cursor="hand2");
        self.canvas.itemconfig(self.border, outline=CYBER_BLUE, width=3)
        if self.label: self.canvas.itemconfig(self.label, fill=CYBER_BLUE)
    
    def on_leave(self, event):
        if self.is_selected: return
        self.canvas.config(cursor="");
        self.canvas.itemconfig(self.border, outline="")
        if self.label: self.canvas.itemconfig(self.label, fill="")
    
    def on_click(self, event):
        """Bölge seçildiğinde görsel geri bildirim ve durum güncellemesi yapar."""
        self.is_selected = not self.is_selected
        color = CYBER_RED if self.is_selected else CYBER_BLUE
        width = 5 if self.is_selected else 3
        self.canvas.itemconfig(self.border, outline=color, width=width)
        if self.label: self.canvas.itemconfig(self.label, fill=color)
        self.app.secimleri_guncelle()


# ==========================================
# ANA UYGULAMA VE NAVİGASYON MANTIĞI
# ==========================================
class TSmartApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("T-SMART SYSTEM")
        self.configure(fg_color=BG_COLOR)
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # # Uygulamayı tam ekran modunda başlatır
        self.attributes("-fullscreen", True)
        
        self.oturum_sahibi = ""
        self.zones = []
        self.secilen_bolge_var = ctk.StringVar(value="SEÇİM YOK")
        
        self.current_frame = None
        self.init_first_screen()
    
    def process_logo(self, size):
        """Logoyu şeffaflaştırır ve istenen boyuta ölçekler."""
        try:
            path = os.path.join(self.project_dir, "t-smart blue logo.png")
            img = Image.open(path).convert("RGBA")
            datas = img.getdata()
            newData = []
            for item in datas:
                if item[0] < 40 and item[1] < 40 and item[2] < 40:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            img.putdata(newData)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except:
            return None
    
    # --- PARALLAX SLIDE GEÇİŞ SİSTEMİ ---
    def init_first_screen(self):
        self.current_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.current_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.giris_ekranini_goster(self.current_frame)
    
    def navigate_to(self, page_function, direction="forward"):
        """Sayfalar arası modern kayma efektiyle geçiş sağlar."""
        screen_width = self.winfo_screenwidth()
        next_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        page_function(next_frame)
        
        # Animasyon başlangıç ve bitiş koordinatlarının ayarlanması
        if direction == "forward":
            next_frame.place(x=screen_width, y=0, relwidth=1, relheight=1)
            start_x_old = 0
            end_x_old = -int(screen_width * 0.3)
            start_x_new = screen_width
            end_x_new = 0
        else:
            next_frame.place(x=-int(screen_width * 0.3), y=0, relwidth=1, relheight=1)
            start_x_old = 0
            end_x_old = screen_width
            start_x_new = -int(screen_width * 0.3)
            end_x_new = 0
            next_frame.lift()
        
        self.animate_parallax(self.current_frame, next_frame, start_x_old, end_x_old, start_x_new, end_x_new)
    
    def animate_parallax(self, old_frame, new_frame, curr_old, target_old, curr_new, target_new):
        """Özyinelemeli animasyon döngüsü ile sayfaları kaydırır."""
        if not old_frame.winfo_exists() or not new_frame.winfo_exists():
            return
        step_old = (target_old - curr_old) * 0.15
        step_new = (target_new - curr_new) * 0.15
        # Hedef koordinata ulaşıldığında animasyonu bitirme
        if abs(target_new - curr_new) < 2:
            new_frame.place(x=0, y=0, relwidth=1, relheight=1)
            if old_frame: old_frame.destroy()
            self.current_frame = new_frame
            return
        
        curr_old += step_old
        curr_new += step_new
        old_frame.place(x=curr_old, y=0)
        new_frame.place(x=curr_new, y=0)
        self.after(10, lambda: self.animate_parallax(old_frame, new_frame, curr_old, target_old, curr_new, target_new))
    
    def geri_butonu_ekle(self, target_func, master_frame):
        ctk.CTkButton(master_frame, text="< GERİ",
                      command=lambda: self.navigate_to(target_func, direction="back"),
                      width=100, height=35,
                      fg_color="#333", border_width=2, border_color=CYBER_BLUE,
                      text_color="white", font=("Arial", 12, "bold"),
                      hover_color="#444").place(x=30, y=30)
    
    # =======================================================
    # SAYFA İÇERİKLERİ
    # =======================================================
    
    # --- 1. GİRİŞ EKRANI ---
    def giris_ekranini_goster(self, master_frame):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        
        bg = tk.Canvas(master_frame, width=sw, height=sh, bg=BG_COLOR, highlightthickness=0);
        bg.place(x=0, y=0)
        bg.create_line(0, 100, sw, 100, fill="#222", width=2);
        bg.create_line(0, sh - 100, sw, sh - 100, fill="#222", width=2)
        
        frame = ctk.CTkFrame(master_frame, width=450, height=650, corner_radius=20, fg_color=PANEL_COLOR,
                             border_color=CYBER_BLUE, border_width=2)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        logo = self.process_logo((200, 200))
        if logo: ctk.CTkLabel(frame, text="", image=logo).pack(pady=30)
        
    
        
        self.entry_user = ctk.CTkEntry(frame, placeholder_text="KULLANICI ADI", width=300, height=45,
                                       border_color=CYBER_BLUE, font=("Arial", 14));
        self.entry_user.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="ŞİFRE", show="●", width=300, height=45,
                                       border_color=CYBER_BLUE, font=("Arial", 14));
        self.entry_pass.pack(pady=10)
        
        ctk.CTkButton(frame, text="Şifremi Unuttum?", width=150, fg_color="transparent", text_color="gray",
                      hover_color="#222", command=lambda: self.navigate_to(self.sifre_unuttum_ekrani)).pack()
        
        ctk.CTkButton(frame, text="GİRİŞ YAP", width=300, height=50, fg_color=CYBER_BLUE, text_color="black",
                      font=("Arial", 14, "bold"), command=self.giris_kontrol).pack(pady=20)
        
        ctk.CTkLabel(frame, text="Hesabın yok mu?", font=("Arial", 12), text_color="white").pack(pady=(5, 0))
        ctk.CTkButton(frame, text="KAYIT OL", width=150, height=30, fg_color="transparent", border_width=1,
                      border_color="white", text_color="white",
                      command=lambda: self.navigate_to(self.kayit_ekranini_goster)).pack(pady=10)
        
        ctk.CTkButton(frame, text="SİSTEMİ KAPAT", width=150, fg_color=CYBER_RED, text_color="white",
                      command=self.sistemi_tamamen_kapat).pack(pady=10)
    
    def giris_kontrol(self):
        """Giriş bilgilerini doğrular ve sisteme güvenli erişim sağlar."""
        # Giriş kutularındaki metinleri alıp boşlukları temizliyoruz
        kadi = self.entry_user.get().strip()
        sifre = self.entry_pass.get().strip()
        
        # --- 1. KONTROL: Boş alan kontrolü ---
        # Eğer kullanıcı hiçbir şey yazmadan giriş yapmaya çalışırsa:
        if not kadi or not sifre:
            messagebox.showwarning("Eksik Bilgi", "Lütfen giriş yapabilmek için tüm alanları doldurun!")
            return  # Fonksiyonu burada durdurur, veritabanı sorgusuna geçmez
        
        # --- 2. KONTROL: Kimlik Doğrulama ---
        # Veritabanı sorgusu sadece alanlar doluysa çalışır
        user = db.giris_yap(kadi, sifre)
        
        if user:
            # Giriş başarılı; kullanıcı verileri oturum değişkenlerine aktarılır
            self.oturum_id = user[0]  # Veritabanındaki ID (KullaniciID)
            self.oturum_sahibi = user[1]  # Veritabanındaki Ad Soyad
            self.giris_yapan_kadi = kadi  # Admin paneli yetki kontrolü için
            
            messagebox.showinfo("Başarılı", f"Hoşgeldin {self.oturum_sahibi.upper()}")
            self.navigate_to(self.dashboard_goster)  # Dashboard ekranına yönlendirir
        else:
            # Alanlar dolu ama eşleşme sağlanamadıysa (Hatalı giriş):
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı!")
      
    def sistemi_tamamen_kapat(self):
        if messagebox.askyesno("Kapat", "Uygulamayı tamamen kapatmak istiyor musunuz?"):
            self.destroy()
            sys.exit()
    
    # --- 2. KAYIT OL ---
    def kayit_ekranini_goster(self, master_frame):
        self.geri_butonu_ekle(self.giris_ekranini_goster, master_frame)
        
        frame = ctk.CTkFrame(master_frame, width=500, height=650, corner_radius=20, fg_color=PANEL_COLOR,
                             border_color=CYBER_BLUE, border_width=2);
        frame.place(relx=0.5, rely=0.5, anchor="center")
        logo = self.process_logo((150, 150));
        if logo: ctk.CTkLabel(frame, text="", image=logo).pack(pady=20)
        ctk.CTkLabel(frame, text="SPORCU KAYIT", font=("Impact", 24), text_color=CYBER_BLUE).pack(pady=10)
        
        self.reg_ad = ctk.CTkEntry(frame, placeholder_text="Ad Soyad", width=350, height=45, font=("Arial", 14));
        self.reg_ad.pack(pady=10)
        self.reg_kadi = ctk.CTkEntry(frame, placeholder_text="Kullanıcı Adı", width=350, height=45, font=("Arial", 14));
        self.reg_kadi.pack(pady=10)
        self.reg_sifre = ctk.CTkEntry(frame, placeholder_text="Şifre", width=350, height=45, show="●",
                                      font=("Arial", 14));
        self.reg_sifre.pack(pady=10)
        
        ctk.CTkButton(frame, text="KAYDI TAMAMLA", width=350, height=50, fg_color=CYBER_BLUE, text_color="black",
                      font=("Arial", 15, "bold"), command=self.kayit_kontrol).pack(pady=30)
    
    def kayit_kontrol(self):
        if not self.reg_ad.get() or not self.reg_kadi.get() or not self.reg_sifre.get():
            messagebox.showwarning("Hata", "Lütfen tüm alanları doldurun!")
            return
        
        if db.kayit_ol("", "", self.reg_kadi.get(), self.reg_sifre.get()):
            messagebox.showinfo("Başarılı", "Kayıt tamamlandı! Giriş yapabilirsiniz.");
            self.navigate_to(self.giris_ekranini_goster, direction="back")
        else:
            messagebox.showerror("Hata", "Bu kullanıcı adı zaten var.")
    
    # --- 3. ŞİFRE SIFIRLAMA ---
    def sifre_unuttum_ekrani(self, master_frame):
        self.geri_butonu_ekle(self.giris_ekranini_goster, master_frame)
        
        frame = ctk.CTkFrame(master_frame, width=500, height=500, corner_radius=20, fg_color=PANEL_COLOR,
                             border_color=CYBER_RED, border_width=2);
        frame.place(relx=0.5, rely=0.5, anchor="center")
        logo = self.process_logo((150, 150));
        if logo: ctk.CTkLabel(frame, text="", image=logo).pack(pady=20)
        ctk.CTkLabel(frame, text="ŞİFRE YENİLEME", font=("Impact", 24), text_color=CYBER_RED).pack(pady=10)
        
        self.reset_kadi = ctk.CTkEntry(frame, placeholder_text="Kullanıcı Adı", width=350, height=45,
                                       font=("Arial", 14));
        self.reset_kadi.pack(pady=10)
        self.reset_sifre = ctk.CTkEntry(frame, placeholder_text="Yeni Şifre", width=350, height=45, show="●",
                                        font=("Arial", 14));
        self.reset_sifre.pack(pady=10)
        
        ctk.CTkButton(frame, text="GÜNCELLE", width=350, height=50, fg_color=CYBER_RED, text_color="white",
                      font=("Arial", 15, "bold"), command=self.sifre_yenile_kontrol).pack(pady=30)
    
    def sifre_yenile_kontrol(self):
        # İçerideki fazladan 'def' satırını sildik, doğrudan değişkenleri alıyoruz
        kadi = self.reset_kadi.get()
        yeni_sifre = self.reset_sifre.get()
        
        if not kadi or not yeni_sifre:
            messagebox.showwarning("Hata", "Lütfen tüm alanları doldurun!")
            return
        
        if db.sifre_guncelle(kadi, yeni_sifre):
            messagebox.showinfo("Başarılı", "Şifreniz başarıyla güncellendi.")
            self.navigate_to(self.giris_ekranini_goster, direction="back")
        else:
            messagebox.showerror("Hata", "Kullanıcı adı bulunamadı!")
    
    # --- 4.DASHBOARD ---
    def dashboard_goster(self, master_frame):
        ctk.CTkLabel(master_frame, text="T-SMART ANASAYFA", font=("Impact", 30), text_color=CYBER_BLUE).place(x=40,
                                                                                                              y=30)
        ctk.CTkLabel(master_frame, text=f"HOŞGELDİN, {self.oturum_sahibi.upper()}", font=("Arial", 14, "bold"),
                     text_color="gray").place(relx=0.85, y=30, anchor="e")
        
        ctk.CTkButton(master_frame, text="Oturumdan Çık", width=100, height=35, fg_color=CYBER_RED, text_color="white",
                      font=("Arial", 12, "bold"), command=self.oturumu_kapat).place(relx=0.92, y=30, anchor="e")
        
        container = ctk.CTkFrame(master_frame, fg_color="transparent");
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        btn_font = ("Arial", 16, "bold")
        btn_w = 400
        btn_h = 70
        
        ctk.CTkButton(container, text="👤 YENİ VÜCUT ANALİZİ", width=btn_w, height=btn_h, fg_color=CYBER_BLUE,
                      text_color="black", font=btn_font, corner_radius=15,
                      command=lambda: self.navigate_to(self.analiz_ekranini_goster)).pack(pady=10)
        
        ctk.CTkButton(container, text="📜 GEÇMİŞ ANALİZ VE RAPORLARIM", width=btn_w, height=btn_h,
                      fg_color="transparent", border_width=2, border_color=CYBER_BLUE,
                      text_color="white", font=btn_font, corner_radius=15, hover_color="#222",
                      command=lambda: self.navigate_to(self.analiz_gecmisi_ekrani)).pack(pady=10)
        
        ctk.CTkButton(container, text="📄 MAÇ KAYDI EKLE", width=btn_w, height=btn_h, fg_color="transparent",
                      border_width=2, border_color=CYBER_BLUE, text_color="white", font=btn_font, corner_radius=15,
                      hover_color="#222", command=lambda: self.navigate_to(self.mac_ekle_ekrani)).pack(pady=10)
        
        ctk.CTkButton(container, text="📂 MAÇ GEÇMİŞİ & İSTATİSTİK", width=btn_w, height=btn_h, fg_color="transparent",
                      border_width=2, border_color=CYBER_BLUE, text_color="white", font=btn_font, corner_radius=15,
                      hover_color="#222", command=lambda: self.navigate_to(self.gecmis_ekrani)).pack(pady=10)
        
        if hasattr(self, 'giris_yapan_kadi') and self.giris_yapan_kadi.lower() == "admin":
            ctk.CTkButton(container, text="🔒 YÖNETİCİ PANELİ", width=btn_w, height=btn_h,
                          fg_color="#333", text_color="white", font=btn_font, corner_radius=15,
                          hover_color="#444", command=lambda: self.navigate_to(self.admin_paneli)).pack(pady=10)
    
    def oturumu_kapat(self):
        if messagebox.askyesno("Oturum Kapat", "Hesabınızdan çıkış yapmak istiyor musunuz?"):
            self.navigate_to(self.giris_ekranini_goster, direction="back")
    
    # --- 5. MAÇ KAYDI ---
    def mac_ekle_ekrani(self, master_frame):
        self.geri_butonu_ekle(self.dashboard_goster, master_frame)
        
        frame = ctk.CTkFrame(master_frame, width=500, height=750, fg_color=PANEL_COLOR, border_color=CYBER_BLUE,
                             border_width=2,
                             corner_radius=15);
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame, text="YENİ MAÇ KAYDI", font=("Impact", 28), text_color=CYBER_BLUE).pack(pady=30)
        
        self.m_rakip = ctk.CTkEntry(frame, placeholder_text="Rakip Adı", width=350, height=40, font=("Arial", 14));
        self.m_rakip.pack(pady=10)
        self.m_kulup = ctk.CTkEntry(frame, placeholder_text="Rakip Kulübü", width=350, height=40, font=("Arial", 14));
        self.m_kulup.pack(pady=10)
        self.m_skor = ctk.CTkEntry(frame, placeholder_text="Skor (Örn: 12-8)", width=350, height=40,
                                   font=("Arial", 14));
        self.m_skor.pack(pady=10)
        self.m_sehir = ctk.CTkEntry(frame, placeholder_text="Şehir / Turnuva Adı", width=350, height=40,
                                    font=("Arial", 14));
        self.m_sehir.pack(pady=10)
        
        ctk.CTkLabel(frame, text="Baskın Hata:", text_color="gray", font=("Arial", 12)).pack(pady=(10, 0))
        self.m_hata = ctk.CTkComboBox(frame,
                                      values=["Gard Düşüklüğü", "Mesafe Hatası", "Refleks Zayıflığı", "Kondisyon"],
                                      width=350, height=40, font=("Arial", 14));
        self.m_hata.pack(pady=5)
        
        ctk.CTkLabel(frame, text="Sonuç:", text_color="gray", font=("Arial", 12)).pack(pady=(10, 0))
        self.m_sonuc = ctk.CTkComboBox(frame, values=["GALİBİYET", "MAĞLUBİYET", "BERABERLİK"],
                                       width=350, height=40, font=("Arial", 14));
        self.m_sonuc.pack(pady=5)
        
        ctk.CTkButton(frame, text="KAYDET", width=350, height=50, fg_color=CYBER_BLUE, text_color="black",
                      font=("Arial", 16, "bold"), command=self.kaydet_islevi).pack(pady=40)
    
    def kaydet_islevi(self):
        """Maç verilerini doğrular, veritabanına işler ve formu bir sonraki kayıt için temizler."""
        
        # Giriş kutularındaki metinleri alıp gereksiz boşlukları temizliyoruz
        rakip = self.m_rakip.get().strip()
        kulup = self.m_kulup.get().strip()
        skor = self.m_skor.get().strip()
        sehir = self.m_sehir.get().strip()
        
        # --- DOĞRULAMA KONTROLÜ (Validation) ---
        # Veritabanı tutarlılığı için tüm alanların dolu olması şart koşulur
        if not rakip or not kulup or not skor or not sehir:
            messagebox.showwarning("Eksik Bilgi", "Lütfen ekrandaki tüm alanları eksiksiz doldurunuz!")
            return  # Eksik veri varsa kayıt işlemini burada keser
        
        # Veritabanı şemasına uygun veri paketi hazırlanıyor
        veri = {
            "tarih": datetime.datetime.now().strftime("%Y-%m-%d"),  # Otomatik tarih damgası
            "rakip": rakip,
            "kulup": kulup,
            "skor": skor,
            "sehir": sehir,
            "hata": self.m_hata.get(),
            "sonuc": self.m_sonuc.get()
        }
        
        # DatabaseManager sınıfı üzerinden veritabanına INSERT sorgusu gönderilir
        db.mac_ekle(self.oturum_id, veri)
        
        # İşlem başarılı mesajı kullanıcıya gösterilir
        messagebox.showinfo("Başarılı", "Maç kaydı başarıyla eklendi.")
        
        # --- FORM SIFIRLAMA İŞLEMİ (Resetting Fields) ---
        # Kayıt başarılı olduktan sonra giriş kutularını (Entry) temizliyoruz
        self.m_rakip.delete(0, 'end')  # Rakip adını siler
        self.m_kulup.delete(0, 'end')  # Kulüp bilgisini siler
        self.m_skor.delete(0, 'end')  # Skor bilgisini siler
        self.m_sehir.delete(0, 'end')  # Şehir bilgisini siler
        
        # Seçim kutularını (ComboBox) varsayılan ilk değerlerine döndürüyoruz
        self.m_hata.set("Gard Düşüklüğü")
        self.m_sonuc.set("GALİBİYET")
        
        # NOT: Kullanıcı dashboard'a sol üstteki 'Geri' butonu ile manuel olarak dönebilir.
    
    # --- 6. GEÇMİŞ MAÇLAR ---
    def gecmis_ekrani(self, master_frame):
        self.geri_butonu_ekle(self.dashboard_goster, master_frame)
        
        ctk.CTkLabel(master_frame, text="MAÇ GEÇMİŞİ", font=("Impact", 40), text_color=CYBER_BLUE).pack(pady=(30, 20))
        
        COL_WIDTHS = [120, 160, 160, 80, 160, 150, 120]
        HEADERS = ["TARİH", "RAKİP", "KULÜP", "SKOR", "ŞEHİR", "HATA", "SONUÇ"]
        
        header_frame = ctk.CTkFrame(master_frame, width=1100, height=50, fg_color="#222", corner_radius=10)
        header_frame.pack(pady=5)
        header_frame.pack_propagate(False)
        maclar = db.tum_maclari_getir(self.oturum_id)
        
        for i, h in enumerate(HEADERS):
            lbl = ctk.CTkLabel(header_frame, text=h, font=("Arial", 12, "bold"),
                               text_color="white", width=COL_WIDTHS[i], anchor="center")
            lbl.pack(side="left", padx=2)
        
        scroll = ctk.CTkScrollableFrame(master_frame, width=1100, height=550, fg_color="transparent")
        scroll.pack(pady=5)
        
       
        
        if not maclar:
            ctk.CTkLabel(scroll, text="Henüz kayıtlı maç yok.", font=("Arial", 16), text_color="gray").pack(pady=50)
            return
        
        for m in maclar:
            row_frame = ctk.CTkFrame(scroll, fg_color=PANEL_COLOR, corner_radius=10,
                                     border_width=1, border_color="#333", height=50)
            row_frame.pack(fill="x", pady=5)
            row_frame.pack_propagate(False)
            
            sonuc = m["sonuc"]
            if sonuc == "GALİBİYET":
                btn_color = CYBER_GREEN
            elif sonuc == "MAĞLUBİYET":
                btn_color = CYBER_RED
            else:
                btn_color = CYBER_YELLOW
            
            values = [m["tarih"], m["rakip"], m["kulup"], m["skor"], m["sehir"], m["hata"]]
            
            for i, val in enumerate(values):
                lbl = ctk.CTkLabel(row_frame, text=str(val), font=("Arial", 12),
                                   text_color="white", width=COL_WIDTHS[i], anchor="center")
                lbl.pack(side="left", padx=2)
            
            ctk.CTkButton(row_frame, text=sonuc, fg_color=btn_color,
                          text_color="black",
                          text_color_disabled="black",
                          font=("Arial", 11, "bold"), height=30, width=COL_WIDTHS[6],
                          corner_radius=15, state="disabled").pack(side="left", padx=2)
    
    # --- YENİ EKRAN: ANALİZ GEÇMİŞİ VE RAPORLAR ---
    def analiz_gecmisi_ekrani(self, master_frame):
        self.geri_butonu_ekle(self.dashboard_goster, master_frame)
        ctk.CTkLabel(master_frame, text="ANALİZ GEÇMİŞİ VE RAPORLARIM", font=("Impact", 36),
                     text_color=CYBER_GREEN).pack(pady=(30, 20))
        
        scroll = ctk.CTkScrollableFrame(master_frame, width=1000, height=600, fg_color="transparent")
        scroll.pack(pady=10)
        
        analizler = db.tum_analizleri_getir(self.oturum_id)
        
        if not analizler:
            ctk.CTkLabel(scroll, text="Henüz kayıtlı analiz yok.", font=("Arial", 16), text_color="gray").pack(pady=50)
            return
        
        for a in analizler:
            card = ctk.CTkFrame(scroll, fg_color=PANEL_COLOR, corner_radius=15, border_width=1, border_color="#444")
            card.pack(fill="x", pady=10, padx=10)
            
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(top_frame, text=f"TARİH: {a['tarih']}", font=("Arial", 14, "bold"),
                         text_color=CYBER_BLUE).pack(side="left")
            ctk.CTkLabel(top_frame, text=f"TESPİT EDİLEN HATA: {a['hata']}", font=("Arial", 14, "bold"),
                         text_color=CYBER_RED).pack(side="right")
            
            ctk.CTkLabel(card, text=f"SEÇİLEN BÖLGELER: {a['bolgeler']}", font=("Arial", 12), text_color="gray").pack(
                anchor="w", padx=15)
            
            ctk.CTkLabel(card, text=" ANTRENÖR TAVSİYESİ:", font=("Arial", 12, "bold"), text_color=CYBER_YELLOW).pack(
                anchor="w", padx=15, pady=(5, 0))
            ctk.CTkLabel(card, text=a['oneri'], font=("Arial", 12), text_color="white", wraplength=900,
                         justify="left").pack(anchor="w", padx=15, pady=(0, 15))
    
    # --- 7. ADMIN PANELİ ---
    def admin_paneli(self, master_frame):
        self.geri_butonu_ekle(self.dashboard_goster, master_frame)
        ctk.CTkLabel(master_frame, text="YÖNETİCİ KONTROL PANELİ", font=("Impact", 30), text_color=CYBER_BLUE).pack(
            pady=50)
        
        f = ctk.CTkFrame(master_frame, width=600, height=400, fg_color=PANEL_COLOR)
        f.pack()
        
        # Veritabanından verileri çekiyoruz
        k_sayi, a_sayi = db.admin_istatistik_getir()
        
        ctk.CTkLabel(f, text=f"👤 Toplam Kullanıcı Sayısı: {k_sayi}", font=("Arial", 22, "bold")).pack(pady=40)
        ctk.CTkLabel(f, text=f"📊 Toplam Analiz Kaydı: {a_sayi}", font=("Arial", 22, "bold"),
                     text_color=CYBER_GREEN).pack(pady=10)
    
    
    # --- 8. VÜCUT ANALİZİ (DÜZELTİLMİŞ GENİŞ GÖRSEL) ---
    def analiz_ekranini_goster(self, master_frame):
        
        # 1. BUG DÜZELTMESİ: GİRİŞTE SEÇİMLERİ SIFIRLA
        self.secilen_bolge_var.set("SEÇİM YOK")
        self.zones = []  # Önceki poligon nesnelerini temizle (Sanal olarak)
        
        left = ctk.CTkFrame(master_frame, fg_color="transparent");
        left.pack(side="left", expand=True, fill="both", padx=50)
        
        # Genişlik arttırıldı (460px)
        self.canvas = tk.Canvas(left, width=IMG_WIDTH, height=IMG_HEIGHT, bg=BG_COLOR, highlightthickness=0);
        self.canvas.pack(pady=20)
        
        try:
            p = os.path.join(self.project_dir, "cyber_body.png")
            # Programmatik olarak görseli genişlet (Strech effect)
            img = Image.open(p).resize((IMG_WIDTH, IMG_HEIGHT), Image.Resampling.LANCZOS);
            self.bg_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")
        except:
            self.canvas.create_text(IMG_WIDTH / 2, IMG_HEIGHT / 2, text="Vücut Görseli Yok", fill="white")
        
        # --- YENİ VE GENİŞLETİLMİŞ KOORDİNATLAR (460x550) ---
        # Görseli yanlara doğru açtığımız için koordinatları da açtık
        points_data_raw = [
            # KAFA: 230 ekseni (Ortada)
            ([200, 20, 260, 20, 270, 75, 230, 90, 190, 75], "KAFA"),
            
            # GÖVDE: Geniş göğüs (230 eksen)
            ([180, 100, 280, 100, 300, 140, 280, 280, 180, 280, 160, 140], "GÖVDE"),
            
            # SAĞ KOL (Ekrana göre SOLDA):
            # Boşluğa tıklanmaması için x değerlerini kıstım ve içeri aldım
            ([160, 110, 120, 110, 90, 180, 80, 250, 110, 260, 140, 180, 170, 130], "SAĞ KOL"),
            
            # SOL KOL (Ekrana göre SAĞDA):
            ([300, 110, 340, 110, 370, 180, 380, 250, 350, 260, 320, 180, 290, 130], "SOL KOL"),
            
            # SAĞ BACAK (Solda)
            ([180, 290, 220, 290, 225, 380, 210, 540, 170, 540, 160, 380], "SAĞ BACAK"),
            
            # SOL BACAK (Sağda)
            ([240, 290, 280, 290, 300, 380, 290, 540, 250, 540, 235, 380], "SOL BACAK")
        ]
        
        oran_x=IMG_WIDTH / 460;
        oran_y=IMG_HEIGHT / 550;
        for points, name in points_data_raw:
            # Her bir noktayı (x, y) yeni boyuta göre matematiksel olarak çarpıyoruz
            scaled_points = []
            for i in range(len(points)):
                if i %2==0:
                    scaled_points.append(points[i]*oran_x)
                else:
                    scaled_points.append(points[i]*oran_y)
        
            self.zones.append(ClickableZone(self.canvas,scaled_points,name,self))
        
        right = ctk.CTkFrame(master_frame, width=400, fg_color=PANEL_COLOR);
        right.pack(side="right", fill="y", padx=20)
        logo = self.process_logo((120, 120));
        if logo: ctk.CTkLabel(right, text="", image=logo).pack(pady=20)
        ctk.CTkLabel(right, text="[ HEDEFLER ]", font=("Arial", 16), text_color=CYBER_BLUE).pack(pady=10)
        self.lbl_secilenler = ctk.CTkLabel(right, textvariable=self.secilen_bolge_var, font=("Arial", 14, "bold"),
                                           text_color="white", wraplength=350);
        self.lbl_secilenler.pack()
        
        ctk.CTkButton(right, text="ANALİZİ BİTİR", height=50, fg_color=CYBER_BLUE, text_color="black",
                      font=("Arial", 14, "bold"), command=self.analiz_sonuc).pack(side="bottom", pady=(10, 50),
                                                                                  fill="x", padx=30)
        
        ctk.CTkButton(right, text="ANASAYFAYA DÖN", height=50, fg_color="#333", text_color="white", border_width=2,
                      border_color="#555",
                      font=("Arial", 14, "bold"), hover_color="#444",
                      command=lambda: self.navigate_to(self.dashboard_goster, "back")).pack(side="bottom", pady=(0, 10),
                                                                                            fill="x", padx=30)
    
    def secimleri_guncelle(self):
        secili = [z.name for z in self.zones if z.is_selected]
        self.secilen_bolge_var.set(", ".join(secili) if secili else "SEÇİM YOK")
    
    def analiz_sonuc(self):
        """İstatistiksel hata verisi ve kullanıcı seçimine göre dinamik öneri üretir."""
        secili = [z.name for z in self.zones if z.is_selected]
        if not secili: messagebox.showwarning("Hata", "Bölge seçmediniz!"); return
        
        # Veritabanındaki maç istatistiklerinden en sık yapılan hata çekilir
        hata, sayi = db.analiz_verisi_getir(self.oturum_id)
        
        # Karar Mekanizması: Hata türü ve bölgeye göre özel teknik öneri
        oneri_metni = ""
        if "KAFA" in secili and hata == "Gard Düşüklüğü":
            oneri_metni = "⚠️ KRİTİK UYARI: Kafa bölgesi seçili ve geçmişte gardınız çok düşmüş.\n👉 DRILL: Lastik ile omuz kuvvetlendirme ve çene koruma çalışın."
        elif "GÖVDE" in secili and hata == "Mesafe Hatası":
            oneri_metni = "⚠️ UYARI: Gövde açık veriyorsunuz, mesafe ayarınız bozuk.\n👉 DRILL: Torbaya mesafeli yan tekme (Cut Kick) çalışın."
        else:
            oneri_metni = f"Seçilen bölgeler için standart kuvvet antrenmanı yapın.\nAyrıca '{hata}' sorunu için teknik tekrar sayısını artırın."
            
        # Veriyi kaydet ve rapor ekranını (Toplevel) tetikle
        db.analiz_ekle(self.oturum_id, ", ".join(secili), hata, oneri_metni)
        
        top = ctk.CTkToplevel(self);
        top.geometry("600x500");
        top.attributes("-topmost", True);
        top.configure(fg_color=PANEL_COLOR)
        
        top.attributes("-alpha", 0.0)
        
        def fade_in_popup(alpha=0):
            alpha += 0.05
            if alpha < 1.0:
                top.attributes("-alpha", alpha)
                top.after(10, lambda: fade_in_popup(alpha))
            else:
                top.attributes("-alpha", 1.0)
        
        fade_in_popup()
        
        top.overrideredirect(True)
        ctk.CTkButton(top, text="X", width=30, height=30, fg_color="red", command=top.destroy).place(relx=0.95,
                                                                                                     rely=0.05,
                                                                                                     anchor="center")
        
        ctk.CTkLabel(top, text="ANTRENÖR RAPORU", font=("Impact", 28), text_color=CYBER_BLUE).pack(pady=20)
        textbox = ctk.CTkTextbox(top, width=550, height=350, font=("Consolas", 14), fg_color="#1a1a1a",
                                 text_color="white");
        textbox.pack(pady=10)
        
        r = f"SPORCU: {self.oturum_sahibi.upper()}\n" + "-" * 40 + "\n"
        r += f"SEÇİLEN BÖLGELER: {', '.join(secili)}\n"
        r += f"GEÇMİŞ ANALİZİ: En sık '{hata}' ({sayi} kez) hatası yapılmış.\n\nAI ÖNERİSİ:\n{oneri_metni}\n\n(Bu rapor geçmişinize kaydedildi.)"
        
        textbox.insert("0.0", r);
        textbox.configure(state="disabled")

# ==========================================
# ÇALIŞTIRMA KATMANI
# ==========================================
if __name__ == "__main__":
    app = TSmartApp() #Uygulama nesnesi başlatılır
    app.mainloop() # Arayüz olay döngüsü çalıştırılır