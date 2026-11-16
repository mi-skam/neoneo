// Draws the neoneo menu bar icon ("nn", black on transparent, used as a
// template image) and packs it into an .icns file.
//
// usage: swift tools/make-icon.swift OUT.icns
import AppKit

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write("usage: make-icon.swift OUT.icns\n".data(using: .utf8)!)
    exit(2)
}
let out = URL(fileURLWithPath: CommandLine.arguments[1])
let iconset = FileManager.default.temporaryDirectory
    .appendingPathComponent("neoneo-\(UUID().uuidString).iconset")
try FileManager.default.createDirectory(at: iconset, withIntermediateDirectories: true)

func png(pixels: Int) -> Data {
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: pixels, pixelsHigh: pixels,
        bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    let side = CGFloat(pixels)
    // Glyph outlines of "nn", scaled so the ink fills 88% of the width, centred.
    let font = NSFont.systemFont(ofSize: 100, weight: .heavy) as CTFont
    let line = CTLineCreateWithAttributedString(
        NSAttributedString(string: "nn", attributes: [.font: font]))
    let path = CGMutablePath()
    for run in CTLineGetGlyphRuns(line) as! [CTRun] {
        let count = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: count)
        var positions = [CGPoint](repeating: .zero, count: count)
        CTRunGetGlyphs(run, CFRange(location: 0, length: count), &glyphs)
        CTRunGetPositions(run, CFRange(location: 0, length: count), &positions)
        for (glyph, pos) in zip(glyphs, positions) {
            if let outline = CTFontCreatePathForGlyph(font, glyph, nil) {
                path.addPath(outline, transform: CGAffineTransform(translationX: pos.x, y: pos.y))
            }
        }
    }
    let box = path.boundingBoxOfPath
    let scale = side * 0.88 / box.width
    var fit = CGAffineTransform(translationX: (side - box.width * scale) / 2,
                                y: (side - box.height * scale) / 2)
        .scaledBy(x: scale, y: scale)
        .translatedBy(x: -box.minX, y: -box.minY)
    let cg = NSGraphicsContext.current!.cgContext
    cg.addPath(path.copy(using: &fit)!)
    cg.setFillColor(NSColor.black.cgColor)
    cg.fillPath()
    NSGraphicsContext.restoreGraphicsState()
    return rep.representation(using: .png, properties: [:])!
}

for (name, pixels) in [
    ("icon_16x16.png", 16), ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32), ("icon_32x32@2x.png", 64),
] {
    try png(pixels: pixels).write(to: iconset.appendingPathComponent(name))
}

let task = Process()
task.executableURL = URL(fileURLWithPath: "/usr/bin/iconutil")
task.arguments = ["-c", "icns", iconset.path, "-o", out.path]
try task.run()
task.waitUntilExit()
try FileManager.default.removeItem(at: iconset)
exit(task.terminationStatus)
