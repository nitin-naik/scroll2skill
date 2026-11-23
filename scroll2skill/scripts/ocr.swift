// On-device OCR with Apple Vision. Free, offline, no dependencies.
// Usage: ocr IMAGE [IMAGE ...]  -> JSON {"path": "recognized text", ...} on stdout
import Foundation
import Vision
import AppKit

var out: [String: String] = [:]
for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        out[path] = ""
        continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    if #available(macOS 13.0, *) { req.automaticallyDetectsLanguage = true }
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    try? handler.perform([req])
    let lines = (req.results ?? [])
        .filter { ($0.topCandidates(1).first?.confidence ?? 0) >= 0.4 }
        .sorted { $0.boundingBox.minY > $1.boundingBox.minY }  // top to bottom
        .compactMap { $0.topCandidates(1).first?.string }
    out[path] = lines.joined(separator: " / ")
}
let data = try JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
FileHandle.standardOutput.write(data)
