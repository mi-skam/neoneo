// Usage: swift tools/dump-layout.swift <input-source-id>
// Prints keycode<TAB>modifiers<TAB>output (U+XXXX ...) for codes 0-127.
import Carbon
import Foundation

let sets: [(String, UInt32)] = [
    ("none", 0),
    ("shift", UInt32(shiftKey)),
    ("option", UInt32(optionKey)),
    ("shift+option", UInt32(shiftKey | optionKey)),
    ("caps", UInt32(alphaLock)),
    ("caps+shift", UInt32(alphaLock | shiftKey)),
    ("caps+option", UInt32(alphaLock | optionKey)),
    ("caps+shift+option", UInt32(alphaLock | shiftKey | optionKey)),
    ("command", UInt32(cmdKey)),
    ("control", UInt32(controlKey)),
]

func fail(_ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(1)
}

guard CommandLine.arguments.count == 2 else { fail("usage: dump-layout.swift <input-source-id>") }
let id = CommandLine.arguments[1]
let filter = [kTISPropertyInputSourceID as String: id] as CFDictionary
guard let list = TISCreateInputSourceList(filter, true)?.takeRetainedValue() as? [TISInputSource],
      let source = list.first
else { fail("input source not found: \(id)") }
guard let ptr = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData) else {
    fail("no uchr data: \(id)")
}
let data = Unmanaged<CFData>.fromOpaque(ptr).takeUnretainedValue() as Data
let kbdType = UInt32(LMGetKbdType())

data.withUnsafeBytes { (raw: UnsafeRawBufferPointer) in
    let layout = raw.bindMemory(to: UCKeyboardLayout.self).baseAddress!
    for code in 0..<128 {
        for (name, mods) in sets {
            var dead: UInt32 = 0
            var chars = [UniChar](repeating: 0, count: 8)
            var len = 0
            let status = UCKeyTranslate(
                layout, UInt16(code), UInt16(kUCKeyActionDown), (mods >> 8) & 0xFF, kbdType,
                OptionBits(kUCKeyTranslateNoDeadKeysBit), &dead, chars.count, &len, &chars)
            if status != noErr { fail("UCKeyTranslate \(status) at \(code) \(name)") }
            let out = String(utf16CodeUnits: chars, count: len).unicodeScalars
                .map { String(format: "U+%04X", $0.value) }.joined(separator: " ")
            print("\(code)\t\(name)\t\(out)")
        }
    }
}
