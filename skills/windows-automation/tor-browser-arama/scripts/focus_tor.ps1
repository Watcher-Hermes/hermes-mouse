Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
}
"@

$callback = {
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 256
    [WinAPI]::GetWindowText($hWnd, $sb, 256)
    $title = $sb.ToString()
    if ($title -like '*Tor*Browser*' -and [WinAPI]::IsWindowVisible($hWnd)) {
        Write-Host "FOCUSED: $title"
        [WinAPI]::SetForegroundWindow($hWnd)
        return $false
    }
    return $true
}

[WinAPI]::EnumWindows($callback, [IntPtr]::Zero)
