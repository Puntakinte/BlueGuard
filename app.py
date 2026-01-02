# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime, date
import os
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

# --- TEMEL YAPILANDIRMA ---
# ... (app.config ayarları aynı, değişiklik yok) ...
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cankurtaran.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'bu-cok-gizli-bir-anahtar-olmalı-12345'
app.config['ADMIN_USERNAME'] = 'admin'
# !!! ÖNEMLİ !!! BU SATIRI KENDİ OLUŞTURDUĞUNUZ HASH İLE DEĞİŞTİRİN
app.config['ADMIN_PASSWORD_HASH'] = 'pbkdf2:sha256:600000$P9ZtYQJtqTqYl0E4$120f269d71c1103b41c04f4b23b3f27e5d808d4b3f88f8d53d712411c5b8b958'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')


db = SQLAlchemy(app)
mail = Mail(app)

# --- Veritabanı Modelleri ---
# ... (Egitim, Ogrenci, OnBasvuru modelleri olduğu gibi kalıyor, değişiklik yok) ...
class Egitim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    tarih = db.Column(db.String(50), nullable=False)
    kontenjan = db.Column(db.Integer, nullable=False)
    ogrenciler = relationship("Ogrenci", backref="egitim", cascade="all, delete-orphan")

class Ogrenci(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    tc_no = db.Column(db.String(11), nullable=False)
    dogum_tarihi = db.Column(db.String(20), nullable=False)
    egitim_id = db.Column(db.Integer, db.ForeignKey('egitim.id'), nullable=False)

class OnBasvuru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_soyad = db.Column(db.String(100), nullable=False)
    tc_no = db.Column(db.String(11), nullable=False)
    dogum_tarihi = db.Column(db.String(20), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    kurs_tipi = db.Column(db.String(50), nullable=False)
    basvuru_tarihi = db.Column(db.DateTime, default=datetime.utcnow)

# --- Admin Koruma Fonksiyonu ---
# ... (admin_required fonksiyonu olduğu gibi kalıyor, değişiklik yok) ...
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session:
            flash('Bu sayfayı görmek için yönetici girişi yapmalısınız.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Görünümler (Routes) ---

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/yonetmelikler')
def yonetmelikler_sayfasi():
    return render_template('yonetmelikler.html')

@app.route('/hizmetlerimiz')
def hizmetlerimiz_sayfasi():
    return render_template('hizmetlerimiz.html')

@app.route('/hakkimizda')
def hakkimizda_sayfasi():
    return render_template('hakkimizda.html')

@app.route('/iletisim')
def iletisim_sayfasi():
    return render_template('iletisim.html')

# === YENİ EKLENEN SAYFA ===
@app.route('/malzemeler')
def malzemeler_sayfasi():
    return render_template('malzemeler.html')
# ===========================

@app.route('/egitimler', methods=['GET', 'POST'])
def egitimler_sayfasi():
    # ... (Bu fonksiyonun tamamı olduğu gibi kalıyor, değişiklik yok) ...
    if request.method == 'POST':
        try:
            # ... (ön başvuru işleme kodu aynı) ...
            dogum_tarihi_str = request.form['dogum_tarihi']
            ad_soyad = request.form['ad_soyad']
            tc_no = request.form['tc_no']
            telefon = request.form['telefon']
            email = request.form['email']
            kurs_tipi = request.form['kurs_tipi']

            dogum_tarihi_obj = datetime.strptime(dogum_tarihi_str, '%Y-%m-%d').date()
            bugun = date.today()
            yas = bugun.year - dogum_tarihi_obj.year - ((bugun.month, bugun.day) < (dogum_tarihi_obj.month, dogum_tarihi_obj.day))

            if yas < 18:
                flash("18 yaşından küçükler ön başvuru yapamaz!", "danger")
            else:
                yeni_on_basvuru = OnBasvuru(
                    ad_soyad=ad_soyad, tc_no=tc_no, dogum_tarihi=dogum_tarihi_str,
                    telefon=telefon, email=email, kurs_tipi=kurs_tipi
                )
                db.session.add(yeni_on_basvuru)
                db.session.commit()

                try:
                    msg = Message(subject=f"Yeni ÖN BAŞVURU: {kurs_tipi} Cankurtaran", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
                    msg.body = f"Merhaba, '{kurs_tipi}' eğitimi için yeni bir ÖN BAŞVURU yapıldı..."
                    mail.send(msg)
                except Exception as e:
                    print(f"E-posta gönderilemedi: {e}")

                flash(f"{kurs_tipi} Cankurtaran Eğitimi için ön başvurunuz başarıyla alınmıştır...", "success")

            return redirect(url_for('egitimler_sayfasi'))

        except Exception as e:
            flash(f"Bir hata oluştu: {e}", "danger")
            return redirect(url_for('egitimler_sayfasi'))

    egitim_listesi = Egitim.query.all()
    return render_template('egitimler.html', egitimler=egitim_listesi)

# ... (Geri kalan tüm fonksiyonlar 'on_basvurular', 'login', 'logout', 'egitim_ekle' vs. olduğu gibi kalıyor) ...

@app.route('/on-basvurular')
@admin_required
def on_basvurular():
    # ... (kod aynı) ...
    bronze_listesi = OnBasvuru.query.filter_by(kurs_tipi='Bronz').order_by(OnBasvuru.basvuru_tarihi.desc()).all()
    gumus_listesi = OnBasvuru.query.filter_by(kurs_tipi='Gümüş').order_by(OnBasvuru.basvuru_tarihi.desc()).all()
    return render_template('on_basvurular.html', bronze_listesi=bronze_listesi, gumus_listesi=gumus_listesi)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (kod aynı) ...
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == app.config['ADMIN_USERNAME'] and check_password_hash(app.config['ADMIN_PASSWORD_HASH'], password):
            session['is_admin'] = True
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('egitimler_sayfasi'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    # ... (kod aynı) ...
    session.pop('is_admin', None)
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('ana_sayfa'))

@app.route('/ekle', methods=['GET', 'POST'])
@admin_required
def egitim_ekle():
    # ... (kod aynı) ...
    if request.method == 'POST':
        yeni_egitim_ad = request.form['ad']
        yeni_egitim_tarih = request.form['tarih']
        yeni_egitim_kontenjan = request.form['kontenjan']
        yeni_egitim = Egitim(ad=yeni_egitim_ad, tarih=yeni_egitim_tarih, kontenjan=yeni_egitim_kontenjan)
        db.session.add(yeni_egitim)
        db.session.commit()
        flash('Yeni eğitim başarıyla eklendi.', 'success')
        return redirect(url_for('egitimler_sayfasi'))
    return render_template('egitim_ekle.html')

@app.route('/egitim/<int:egitim_id>', methods=['GET', 'POST'])
def egitim_detay(egitim_id):
    # ... (kod aynı) ...
    secilen_egitim = Egitim.query.get_or_404(egitim_id)
    basvuru_sayisi = len(secilen_egitim.ogrenciler)
    kontenjan_dolu = basvuru_sayisi >= secilen_egitim.kontenjan
    hata_mesaji = None

    if request.method == 'POST':
        if not kontenjan_dolu:
            dogum_tarihi_str = request.form['dogum_tarihi']
            dogum_tarihi_obj = datetime.strptime(dogum_tarihi_str, '%Y-%m-%d').date()
            bugun = date.today()
            yas = bugun.year - dogum_tarihi_obj.year - ((bugun.month, bugun.day) < (dogum_tarihi_obj.month, dogum_tarihi_obj.day))

            if yas < 18:
                hata_mesaji = "18 yaşından küçükler başvuru yapamaz!"
            else:
                ogrenci_ad_soyad = request.form['ad_soyad']
                ogrenci_tc_no = request.form['tc_no']
                yeni_ogrenci = Ogrenci(ad_soyad=ogrenci_ad_soyad, tc_no=ogrenci_tc_no, dogum_tarihi=dogum_tarihi_str, egitim_id=secilen_egitim.id)
                db.session.add(yeni_ogrenci)
                db.session.commit()

                if 'is_admin' not in session:
                    try:
                        msg = Message(subject=f"Yeni Başvuru: {secilen_egitim.ad}", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
                        msg.body = f"Merhaba, '{secilen_egitim.ad}' eğitimine yeni bir başvuru yapıldı..."
                        mail.send(msg)
                    except Exception as e:
                        print(f"E-posta gönderilemedi: {e}")

                flash('Başvurunuz başarıyla alınmıştır!', 'success')
                return redirect(url_for('egitim_detay', egitim_id=secilen_egitim.id))

    return render_template('egitim_detay.html', egitim=secilen_egitim, ogrenciler=secilen_egitim.ogrenciler, kontenjan_dolu=kontenjan_dolu, hata_mesaji=hata_mesaji)

@app.route('/sil/<int:egitim_id>', methods=['POST'])
@admin_required
def egitim_sil(egitim_id):
    # ... (kod aynı) ...
    egitim = Egitim.query.get_or_404(egitim_id)
    db.session.delete(egitim)
    db.session.commit()
    flash(f"'{egitim.ad}' eğitimi başarıyla silindi.", 'success')
    return redirect(url_for('egitimler_sayfasi'))

@app.route('/duzenle/<int:egitim_id>', methods=['GET', 'POST'])
@admin_required
def egitim_duzenle(egitim_id):
    # ... (kod aynı) ...
    egitim = Egitim.query.get_or_404(egitim_id)
    if request.method == 'POST':
        egitim.ad = request.form['ad']
        egitim.tarih = request.form['tarih']
        egitim.kontenjan = request.form['kontenjan']
        db.session.commit()
        flash(f"'{egitim.ad}' eğitimi başarıyla güncellendi.", 'success')
        return redirect(url_for('egitimler_sayfasi'))
    return render_template('egitim_duzenle.html', egitim=egitim)

# ... (veritabanı oluşturma ve main bloğu aynı) ...
with app.app_context():
    db.create_all()
    if Egitim.query.count() == 0:
        egitim1 = Egitim(ad="Bronz Cankurtaran Eğitimi", tarih="1-15 Kasım 2025", kontenjan=2)
        egitim2 = Egitim(ad="Gümüş Cankurtaran Eğitimi", tarih="1-15 Aralık 2025", kontenjan=15)
        db.session.add(egitim1)
        db.session.add(egitim2)
        db.session.commit()

if __name__ == '__main__':
    # Render PORT ismini otomatik verir, vermezse 10000 kullanır
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
