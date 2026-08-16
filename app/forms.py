"""Forms WTForms RuangCeritamu."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, TextAreaField, BooleanField,
                     SelectField, SubmitField, IntegerField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, ValidationError,
                                Optional, Regexp, NumberRange)
from flask_login import current_user
from app.models import User
import re


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Kata Sandi", validators=[DataRequired()])
    remember_me = BooleanField("Ingat saya")
    submit = SubmitField("Masuk Ke Akun")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Kata Sandi", validators=[DataRequired(), Length(min=8, message="Minimal 8 karakter.")])
    submit = SubmitField("Daftar Sekarang")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username sudah dipakai.")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email sudah terdaftar.")

    def validate_password(self, password):
        p = password.data
        if not re.search(r'[A-Z]', p):
            raise ValidationError("Harus ada minimal 1 huruf besar.")
        if not re.search(r'[0-9]', p):
            raise ValidationError("Harus ada minimal 1 angka.")


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Nama Lengkap", validators=[Optional(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])
    avatar = FileField("Foto Profil", validators=[FileAllowed(["jpg", "jpeg", "png"], "Hanya JPG/PNG.")])
    submit = SubmitField("Simpan Perubahan")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            if User.query.filter_by(username=username.data).first():
                raise ValidationError("Username sudah dipakai.")

    def validate_email(self, email):
        if email.data.lower() != self.original_email.lower():
            if User.query.filter_by(email=email.data.lower()).first():
                raise ValidationError("Email sudah terdaftar.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Password Saat Ini", validators=[DataRequired()])
    new_password = PasswordField("Password Baru", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Konfirmasi Password Baru",
                                     validators=[DataRequired(), EqualTo("new_password", message="Tidak cocok.")])
    submit = SubmitField("Ubah Password")

    def validate_new_password(self, new_password):
        p = new_password.data
        if not re.search(r'[A-Z]', p):
            raise ValidationError("Harus ada minimal 1 huruf besar.")
        if not re.search(r'[0-9]', p):
            raise ValidationError("Harus ada minimal 1 angka.")


class DeleteAccountForm(FlaskForm):
    confirm_text = StringField("Ketik 'HAPUS' untuk konfirmasi", validators=[DataRequired()])
    submit = SubmitField("Hapus Akun Saya")


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Kirim Tautan Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Kata Sandi Baru", validators=[
        DataRequired(),
        Length(min=8, message="Minimal 8 karakter."),
        Regexp(r'^(?=.*[A-Z])(?=.*\d).*$',
               message="Wajib 1 huruf besar dan 1 angka.")
    ])
    confirm_password = PasswordField("Konfirmasi Kata Sandi Baru",
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Simpan Kata Sandi")


class StartCurhatForm(FlaskForm):
    topic = SelectField("Topik", choices=[
        ("", "— Pilih topik (opsional) —"),
        ("kuliah", "Kuliah / Akademik"), ("karir", "Karir & Pekerjaan"),
        ("keluarga", "Keluarga"), ("percintaan", "Hubungan / Percintaan"),
        ("pertemanan", "Pertemanan"), ("kesehatan_mental", "Kesehatan Mental"),
        ("lainnya", "Lainnya"),
    ], validators=[Optional()])
    submit = SubmitField("Mulai Curhat")


class MessageForm(FlaskForm):
    content = TextAreaField("Pesan", validators=[DataRequired(), Length(max=2000)])
    image = FileField("Lampiran", validators=[FileAllowed(["jpg", "jpeg", "png"], "Hanya JPG/PNG, max 2MB.")])
    submit = SubmitField("Kirim")


class ForumPostForm(FlaskForm):
    title = StringField("Judul", validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField("Cerita", validators=[DataRequired(), Length(min=20, max=5000)])
    mood_tag = SelectField("Tag", choices=[
        ("", "— Pilih tag —"), ("Lelah", "Lelah"), ("Cemas", "Cemas"),
        ("Sedih", "Sedih"), ("Marah", "Marah"), ("Bingung", "Bingung"),
        ("Syukur", "Syukur"), ("Self-Care", "Self-Care"), ("Refleksi", "Refleksi"),
    ], validators=[Optional()])
    pseudonym = StringField("Nama samaran", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Kirim Cerita")


class CommentForm(FlaskForm):
    content = TextAreaField("Komentar", validators=[DataRequired(), Length(min=2, max=1000)])
    pseudonym = StringField("Nama samaran", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Kirim Balasan")


class MoodForm(FlaskForm):
    mood = SelectField("Mood", choices=[
        ("happy", "😊 Senang"), ("neutral", "😐 Biasa Saja"),
        ("sad", "😭 Sedih"), ("anxious", "😰 Cemas"),
        ("overthink", "🌀 Overthinking"),
    ], validators=[DataRequired()])
    note = TextAreaField("Cerita singkat", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Simpan Perasaan")


class ReportForm(FlaskForm):
    reason = TextAreaField("Alasan", validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField("Kirim Laporan")


class MarqueeItemForm(FlaskForm):
    label = StringField("Teks", validators=[DataRequired(), Length(min=2, max=80)])
    icon = StringField("Ikon (Material Symbols)", validators=[Optional(), Length(max=60)],
                       default="emergency_home")
    display_order = IntegerField("Urutan", validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField("Simpan")


class AdminCreatePsikologForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("Nama Lengkap", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Kata Sandi", validators=[DataRequired(), Length(min=6)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Tambah Psikolog")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username sudah dipakai.")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email sudah terdaftar.")
