"""
Setup and Installation Script
این فایل تمام مراحل راه‌اندازی و نصب را انجام می‌دهد
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    """بررسی نسخه Python"""
    print("🔍 بررسی نسخه Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ نیاز به Python 3.8 یا بالاتر دارید!")
        print(f"   نسخه فعلی: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} پیدا شد!")
    return True


def check_file_exists(file_path):
    """بررسی وجود فایل"""
    return os.path.exists(file_path)


def check_required_files():
    """بررسی وجود فایل‌های ضروری"""
    print("\n🔍 بررسی فایل‌های ضروری...")
    required_files = [
        "main.py",
        "requirements.txt",
        "bot/__init__.py",
        "bot/config.py",
        "bot/telegram_bot.py",
        "bot/conversation/openrouter_client.py",
        "bot/interview/interview_agent.py"
    ]
    
    all_exists = True
    for file in required_files:
        if check_file_exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} پیدا نشد!")
            all_exists = False
    
    return all_exists


def install_packages():
    """نصب پکیج‌های مورد نیاز"""
    print("\n📦 نصب پکیج‌های مورد نیاز...")
    
    if not check_file_exists("requirements.txt"):
        print("❌ فایل requirements.txt پیدا نشد!")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        print("✅ pip به‌روزرسانی شد!")
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ تمام پکیج‌ها با موفقیت نصب شدند!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در نصب پکیج‌ها: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {str(e)}")
        return False


def verify_installation():
    """بررسی صحت نصب"""
    print("\n🔍 بررسی نصب پکیج‌ها...")
    
    packages_to_check = [
        ("telegram", "python-telegram-bot"),
        ("requests", "requests")
    ]
    
    all_installed = True
    for module_name, package_name in packages_to_check:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} نصب نشده است!")
            all_installed = False
    
    return all_installed


def check_config():
    """بررسی تنظیمات"""
    print("\n🔍 بررسی تنظیمات...")
    
    try:
        from bot import config
        
        # بررسی وجود توکن تلگرام
        if hasattr(config, 'TELEGRAM_BOT_TOKEN') and config.TELEGRAM_BOT_TOKEN:
            print("✅ توکن تلگرام تنظیم شده است")
        else:
            print("⚠️  توکن تلگرام تنظیم نشده است!")
        
        # بررسی وجود API key OpenRouter
        if hasattr(config, 'OPENROUTER_API_KEY') and config.OPENROUTER_API_KEY:
            print("✅ کلید API OpenRouter تنظیم شده است")
        else:
            print("⚠️  کلید API OpenRouter تنظیم نشده است!")
        
        # بررسی مدل
        if hasattr(config, 'OPENROUTER_MODEL') and config.OPENROUTER_MODEL:
            print(f"✅ مدل: {config.OPENROUTER_MODEL}")
        else:
            print("⚠️  مدل تنظیم نشده است!")
        
        return True
        
    except ImportError:
        print("❌ نتوانست فایل bot/config.py را وارد کند!")
        return False
    except Exception as e:
        print(f"❌ خطا در بررسی تنظیمات: {str(e)}")
        return False


def display_instructions():
    """نمایش دستورالعمل‌های بعدی"""
    print("\n" + "="*50)
    print("✅ راه‌اندازی با موفقیت انجام شد!")
    print("="*50)
    print("\n📝 برای اجرای ربات، دستور زیر را وارد کنید:")
    print("   python main.py")
    print("\n💡 نکات:")
    print("   - برای توقف ربات، Ctrl+C را فشار دهید")
    print("   - تمام تنظیمات در فایل bot/config.py قابل تغییر است")
    print("   - در صورت مشکل، فایل README.md را مطالعه کنید")
    print("\n" + "="*50)


def main():
    """تابع اصلی راه‌اندازی"""
    print("="*50)
    print("🚀 شروع راه‌اندازی Telegram Bot")
    print("="*50)
    
    # بررسی نسخه Python
    if not check_python_version():
        sys.exit(1)
    
    # بررسی فایل‌های ضروری
    if not check_required_files():
        print("\n❌ برخی فایل‌های ضروری پیدا نشدند!")
        sys.exit(1)
    
    # نصب پکیج‌ها
    if not install_packages():
        print("\n❌ خطا در نصب پکیج‌ها!")
        sys.exit(1)
    
    # بررسی نصب
    if not verify_installation():
        print("\n❌ برخی پکیج‌ها به درستی نصب نشده‌اند!")
        sys.exit(1)
    
    # بررسی تنظیمات
    check_config()
    
    # نمایش دستورالعمل‌ها
    display_instructions()


if __name__ == "__main__":
    main()

