import ctypes
import sys

def configure_console():
    try:
        kernel32 = ctypes.windll.kernel32
        
        # Open real console input handle CONIN$
        # GENERIC_READ (0x80000000) | GENERIC_WRITE (0x40000000) = 0xC0000000
        # FILE_SHARE_READ (1) | FILE_SHARE_WRITE (2) = 3
        # OPEN_EXISTING = 3
        h_in = kernel32.CreateFileW("CONIN$", 0xC0000000, 3, None, 3, 0, None)
        if h_in != -1 and h_in != 0:
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(h_in, ctypes.byref(mode)):
                # Disable ENABLE_QUICK_EDIT_MODE (0x0040)
                # Enable ENABLE_EXTENDED_FLAGS (0x0080)
                # Enable ENABLE_VIRTUAL_TERMINAL_INPUT (0x0200)
                new_mode = (mode.value & ~0x0040) | 0x0080 | 0x0200
                kernel32.SetConsoleMode(h_in, new_mode)
            
            # Set STD_INPUT_HANDLE to CONIN$
            kernel32.SetStdHandle(-10, h_in)
            kernel32.CloseHandle(h_in)
            
        # Also configure CONOUT$ for virtual terminal processing
        h_out = kernel32.CreateFileW("CONOUT$", 0xC0000000, 3, None, 3, 0, None)
        if h_out != -1 and h_out != 0:
            out_mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(h_out, ctypes.byref(out_mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                # DISABLE_NEWLINE_AUTO_RETURN = 0x0008
                kernel32.SetConsoleMode(h_out, out_mode.value | 0x0004 | 0x0008)
            kernel32.CloseHandle(h_out)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    success = configure_console()
    print("Console configured:", success)
