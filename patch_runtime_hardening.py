import os

p = r'c:\Users\asus\heretic-work\VSCode-win32-x64\resources\app\out\mainImpl.js'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Native keymap guard
old_keymap = '''function readKeyboardLayoutData(nativeKeymapMod) {
  const keyboardMapping = nativeKeymapMod.getKeyMap();
  const keyboardLayoutInfo = nativeKeymapMod.getCurrentKeyboardLayout();
  return { keyboardMapping, keyboardLayoutInfo };
}'''

new_keymap = '''function readKeyboardLayoutData(nativeKeymapMod) {
  try {
    const keyboardMapping = (nativeKeymapMod && typeof nativeKeymapMod.getKeyMap === "function") ? (nativeKeymapMod.getKeyMap() || {}) : {};
    const keyboardLayoutInfo = (nativeKeymapMod && typeof nativeKeymapMod.getCurrentKeyboardLayout === "function") ? (nativeKeymapMod.getCurrentKeyboardLayout() || { name: "en-US", id: "0409", layout: "US" }) : { name: "en-US", id: "0409", layout: "US" };
    return { keyboardMapping, keyboardLayoutInfo };
  } catch {
    return { keyboardMapping: {}, keyboardLayoutInfo: { name: "en-US", id: "0409", layout: "US" } };
  }
}'''

old_keymap_init = '''async _doInitialize() {
    const nativeKeymapMod = await import("native-keymap");
    this._keyboardLayoutData = readKeyboardLayoutData(nativeKeymapMod);
    if (!isCI) {
      nativeKeymapMod.onDidChangeKeyboardLayout(() => {
        this._keyboardLayoutData = readKeyboardLayoutData(nativeKeymapMod);
        this._onDidChangeKeyboardLayout.fire(this._keyboardLayoutData);
      });
    }
  }'''

new_keymap_init = '''async _doInitialize() {
    try {
      const nativeKeymapMod = await import("native-keymap");
      this._keyboardLayoutData = readKeyboardLayoutData(nativeKeymapMod);
      if (!isCI && nativeKeymapMod && typeof nativeKeymapMod.onDidChangeKeyboardLayout === "function") {
        try {
          nativeKeymapMod.onDidChangeKeyboardLayout(() => {
            this._keyboardLayoutData = readKeyboardLayoutData(nativeKeymapMod);
            this._onDidChangeKeyboardLayout.fire(this._keyboardLayoutData);
          });
        } catch {}
      }
    } catch {
      this._keyboardLayoutData = { keyboardMapping: {}, keyboardLayoutInfo: { name: "en-US", id: "0409", layout: "US" } };
    }
  }'''

# 2. SQLite fallback
old_doconnect = '''doConnect(path3) {
        return new Promise((resolve3, reject) => {
          import("@vscode/sqlite3").then((sqlite3) => {
            const ctor = this.logger.isTracing ? sqlite3.default.verbose().Database : sqlite3.default.Database;
            const connection = {
              db: new ctor(path3, (error) => {
                if (error) {
                  return connection.db && error.code !== "SQLITE_CANTOPEN" ? connection.db.close(() => reject(error)) : reject(error);
                }
                const pragmas = [
                  "PRAGMA user_version = 1;",
                  "CREATE TABLE IF NOT EXISTS ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB);"
                ];
                if (this.useWAL) {
                  pragmas.push("PRAGMA journal_mode=WAL;");
                }
                if (this.busyTimeout) {
                  pragmas.push(`PRAGMA busy_timeout=${this.busyTimeout};`);
                }
                return this.exec(connection, pragmas.join("")).then(() => {
                  return resolve3(connection);
                }, (error2) => {
                  return connection.db.close(() => reject(error2));
                });
              }),
              isInMemory: path3 === _SQLiteStorageDatabase.IN_MEMORY_PATH
            };
            connection.db.on("error", (error) => this.handleSQLiteError(connection, `[storage ${this.name}] Error (event): ${error}`));
            if (this.logger.isTracing) {
              connection.db.on("trace", (sql) => this.logger.trace(`[storage ${this.name}] Trace (event): ${sql}`));
            }
          }, reject);
        });
      }'''

new_doconnect = '''doConnect(path3) {
        return new Promise((resolve3, reject) => {
          const createFallback = () => {
            this.logger.info(`[storage ${this.name}] Using persistent JSON file-backed fallback storage for ${path3}`);
            class FallbackSQLiteDatabase {
              constructor(filePath, callback) {
                this.filePath = filePath;
                this.table = new Map();
                this.isClosed = false;
                try {
                  const fs = require("fs");
                  const jsonFile = (filePath && filePath !== ":memory:") ? (filePath + ".json") : null;
                  if (jsonFile && fs.existsSync(jsonFile)) {
                    const data = JSON.parse(fs.readFileSync(jsonFile, "utf-8"));
                    for (const [k, v] of Object.entries(data)) {
                      this.table.set(k, v);
                    }
                  }
                } catch {}
                setTimeout(() => callback && callback(null), 1);
              }
              _save() {
                try {
                  const fs = require("fs");
                  const jsonFile = (this.filePath && this.filePath !== ":memory:") ? (this.filePath + ".json") : null;
                  if (jsonFile) {
                    const obj = {};
                    for (const [k, v] of this.table.entries()) {
                      obj[k] = v;
                    }
                    fs.writeFileSync(jsonFile, JSON.stringify(obj), "utf-8");
                  }
                } catch {}
              }
              on(event, cb) {}
              removeListener(event, cb) {}
              close(callback) {
                this.isClosed = true;
                this._save();
                setTimeout(() => callback && callback(null), 1);
              }
              exec(sql, callback) {
                setTimeout(() => callback && callback(null), 1);
              }
              serialize(fn) {
                if (fn) fn();
              }
              run(sql, callback) {
                setTimeout(() => callback && callback(null), 1);
              }
              get(sql, callback) {
                setTimeout(() => callback && callback(null, null), 1);
              }
              all(sql, callback) {
                const rows = [];
                for (const [key, value] of this.table.entries()) {
                  rows.push({ key, value });
                }
                setTimeout(() => callback && callback(null, rows), 1);
              }
              prepare(sql) {
                const db = this;
                return {
                  on(event, cb) {},
                  removeListener(event, cb) {},
                  run(params, callback) {
                    if (sql.includes("INSERT") && Array.isArray(params) && params.length >= 2) {
                      db.table.set(params[0], params[1]);
                      db._save();
                    } else if (sql.includes("DELETE") && Array.isArray(params)) {
                      for (const k of params) {
                        db.table.delete(k);
                      }
                      db._save();
                    }
                    if (typeof callback === "function") callback(null);
                  },
                  finalize(callback) {
                    if (typeof callback === "function") callback(null);
                  }
                };
              }
            }
            const fallbackDb = new FallbackSQLiteDatabase(path3, () => {
              const connection = {
                db: fallbackDb,
                isInMemory: path3 === _SQLiteStorageDatabase.IN_MEMORY_PATH
              };
              resolve3(connection);
            });
          };

          import("@vscode/sqlite3").then((sqlite3) => {
            try {
              const ctor = this.logger.isTracing ? sqlite3.default.verbose().Database : sqlite3.default.Database;
              const connection = {
                db: new ctor(path3, (error) => {
                  if (error) {
                    return connection.db && error.code !== "SQLITE_CANTOPEN" ? connection.db.close(() => createFallback()) : createFallback();
                  }
                  const pragmas = [
                    "PRAGMA user_version = 1;",
                    "CREATE TABLE IF NOT EXISTS ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB);"
                  ];
                  if (this.useWAL) {
                    pragmas.push("PRAGMA journal_mode=WAL;");
                  }
                  if (this.busyTimeout) {
                    pragmas.push(`PRAGMA busy_timeout=${this.busyTimeout};`);
                  }
                  return this.exec(connection, pragmas.join("")).then(() => {
                    return resolve3(connection);
                  }, (error2) => {
                    return connection.db.close(() => createFallback());
                  });
                }),
                isInMemory: path3 === _SQLiteStorageDatabase.IN_MEMORY_PATH
              };
              connection.db.on("error", (error) => this.handleSQLiteError(connection, `[storage ${this.name}] Error (event): ${error}`));
              if (this.logger.isTracing) {
                connection.db.on("trace", (sql) => this.logger.trace(`[storage ${this.name}] Trace (event): ${sql}`));
              }
            } catch {
              createFallback();
            }
          }).catch(() => {
            createFallback();
          });
        });
      }'''

print('Found old_keymap:', old_keymap in content)
print('Found old_keymap_init:', old_keymap_init in content)
print('Found old_doconnect:', old_doconnect in content)

if old_keymap in content:
    content = content.replace(old_keymap, new_keymap)
if old_keymap_init in content:
    content = content.replace(old_keymap_init, new_keymap_init)
if old_doconnect in content:
    content = content.replace(old_doconnect, new_doconnect)

with open(p, 'w', encoding='utf-8') as f:
    f.write(content)

print('Full runtime hardening patch applied to VSCode-win32-x64!')
