import os

p = r'c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app\out\mainImpl.js'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: getSqmMachineId
target1 = '''async function getSqmMachineId(errorLogger) {
  if (isWindows2) {
    const Registry2 = await import("@vscode/windows-registry");
    try {
      return Registry2.GetStringRegKey("HKEY_LOCAL_MACHINE", SQM_KEY, "MachineId") || "";
    } catch (err) {
      errorLogger(err);
      return "";
    }
  }
  return "";
}'''

replacement1 = '''async function getSqmMachineId(errorLogger) {
  if (isWindows2) {
    try {
      const Registry2 = await import("@vscode/windows-registry");
      return Registry2.GetStringRegKey("HKEY_LOCAL_MACHINE", SQM_KEY, "MachineId") || "";
    } catch (err) {
      errorLogger(err);
      return "";
    }
  }
  return "";
}'''

# Fix 2: windowsGetStringRegKey
target2 = '''async windowsGetStringRegKey(windowId, hive, path3, name) {
        if (!isWindows2) {
          return void 0;
        }
        const Registry2 = await import("@vscode/windows-registry");
        try {
          return Registry2.GetStringRegKey(hive, path3, name);
        } catch {
          return void 0;
        }
      }'''

replacement2 = '''async windowsGetStringRegKey(windowId, hive, path3, name) {
        if (!isWindows2) {
          return void 0;
        }
        try {
          const Registry2 = await import("@vscode/windows-registry");
          return Registry2.GetStringRegKey(hive, path3, name);
        } catch {
          return void 0;
        }
      }'''

print('Found target1:', target1 in content)
print('Found target2:', target2 in content)

if target1 in content:
    content = content.replace(target1, replacement1)
if target2 in content:
    content = content.replace(target2, replacement2)

with open(p, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied successfully to VSCode-win32-x64!')
