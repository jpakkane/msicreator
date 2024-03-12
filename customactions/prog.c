#include<windows.h>

int APIENTRY WinMain(HINSTANCE hInstance,
		     HINSTANCE hPrevInstance,
		     LPSTR lpszCmdLine,
		     int nCmdShow) {
    DWORD size;
    WCHAR result[MAX_PATH];
    HANDLE file = INVALID_HANDLE_VALUE;
    if (ExpandEnvironmentStringsW(L"%PROGRAMFILES%\\customactions\\testgui.txt", result, MAX_PATH) > MAX_PATH) return 1;
    file = CreateFileW(result, GENERIC_WRITE, 0, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return 1;
    WriteFile(file, "hello world\n", 12, &size, NULL);
    CloseHandle(file);
    return 0;
}
