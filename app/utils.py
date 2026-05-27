import os
import sys

# Kode Warna ANSI untuk Terminal Premium
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
CYAN = "\033[96m"
WHITE = "\033[97m"

# Aktifkan Dukungan ANSI di Terminal Windows secara Programatik
if sys.platform.startswith('win'):
    try:
        import colorama
        colorama.init()
    except ImportError:
        # Menggunakan ctypes untuk mengaktifkan Virtual Terminal Processing di Windows 10/11
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            # STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            # Diamkan jika gagal, sistem CLI akan berjalan dengan teks biasa/ANSI mentah
            pass

def print_success(message: str):
    """Mencetak pesan sukses berwarna hijau."""
    print(f"{GREEN}{BOLD}[SUKSES]{RESET} {GREEN}{message}{RESET}")

def print_info(message: str):
    """Mencetak pesan informasi berwarna biru."""
    print(f"{BLUE}{BOLD}[INFO]{RESET} {BLUE}{message}{RESET}")

def print_warning(message: str):
    """Mencetak pesan peringatan berwarna kuning."""
    print(f"{YELLOW}{BOLD}[PERINGATAN]{RESET} {YELLOW}{message}{RESET}")

def print_error(message: str):
    """Mencetak pesan kesalahan berwarna merah."""
    print(f"{RED}{BOLD}[EROR]{RESET} {RED}{message}{RESET}")

def print_header(title: str):
    """Mencetak header menu dengan kotak/garis premium berwarna cyan."""
    width = 70
    print(f"\n{CYAN}{'=' * width}{RESET}")
    print(f"{CYAN}{BOLD}{title.center(width)}{RESET}")
    print(f"{CYAN}{'=' * width}{RESET}")
