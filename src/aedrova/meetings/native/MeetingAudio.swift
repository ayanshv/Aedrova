import Foundation
import AppKit
import AVFoundation
import ScreenCaptureKit
import CoreMedia
import CoreAudio
import ApplicationServices

let browserIDs = ["com.apple.Safari", "com.google.Chrome", "com.microsoft.edgemac",
                  "org.mozilla.firefox", "com.brave.Browser", "company.thebrowser.Browser"]

func isBrowser(_ id: String) -> Bool {
    browserIDs.contains { id == $0 || id.hasPrefix($0 + ".") }
}

@MainActor func frontGoogleMeet() -> Bool {
    guard let front = NSWorkspace.shared.frontmostApplication,
          let id = front.bundleIdentifier, isBrowser(id) else { return false }
    func isMeetTitle(_ title: String) -> Bool {
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        return title.caseInsensitiveCompare("Google Meet") == .orderedSame ||
            title.range(of: #"^(?:Google Meet|Meet)\s*[-–—|]\s*\S"#,
                        options: [.regularExpression, .caseInsensitive]) != nil
    }
    if AXIsProcessTrusted() {
        let app = AXUIElementCreateApplication(front.processIdentifier)
        var value: CFTypeRef?
        if AXUIElementCopyAttributeValue(app, kAXFocusedWindowAttribute as CFString, &value) == .success,
           let value = value, CFGetTypeID(value) == AXUIElementGetTypeID() {
            let window = unsafeBitCast(value, to: AXUIElement.self)
            var title: CFTypeRef?
            if AXUIElementCopyAttributeValue(window, kAXTitleAttribute as CFString, &title) == .success,
               let title = title as? String, isMeetTitle(title) { return true }
        }
    }
    let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements],
                                           kCGNullWindowID) as? [[String: Any]] ?? []
    return windows.first {
        $0[kCGWindowOwnerPID as String] as? pid_t == front.processIdentifier &&
        $0[kCGWindowLayer as String] as? Int == 0
    }.flatMap { $0[kCGWindowName as String] as? String }.map(isMeetTitle) ?? false
}

let outputLock = NSLock()
func emit(_ event: [String: Any]) {
    outputLock.lock(); defer { outputLock.unlock() }
    if let data = try? JSONSerialization.data(withJSONObject: event) {
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([10]))
    }
}

final class Chunks {
    let root: URL
    let source: String
    let lock = NSLock()
    let started = ProcessInfo.processInfo.systemUptime
    var file: AVAudioFile?
    var frames: Int64 = 0
    var offset: Double = 0
    var name = ""
    var lastLevel = 0.0
    init(root: URL, source: String) { self.root = root; self.source = source }
    func finishLocked() {
        if file != nil {
            file = nil
            emit(["event": "chunk", "file": name, "source": source, "offset": offset])
            frames = 0
        }
    }
    func append(_ buffer: AVAudioPCMBuffer) {
        lock.lock(); defer { lock.unlock() }
        do {
            let now = ProcessInfo.processInfo.systemUptime
            if now - lastLevel >= 0.15, let samples = buffer.floatChannelData?[0] {
                lastLevel = now
                let count = Int(buffer.frameLength)
                var square: Float = 0
                for index in stride(from: 0, to: count, by: 16) { square += samples[index] * samples[index] }
                let level = min(1, sqrt(square / Float(max(1, count / 16))))
                emit(["event": "level", "value": level.isFinite ? level : 0])
            }
            if file == nil {
                offset = ProcessInfo.processInfo.systemUptime - started
                name = source + "-" + UUID().uuidString + ".wav"
                let target = root.appendingPathComponent(name)
                file = try AVAudioFile(forWriting: target, settings: buffer.format.settings)
                try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: target.path)
            }
            try file?.write(from: buffer)
            frames += Int64(buffer.frameLength)
            if Double(frames) / buffer.format.sampleRate >= 15 { finishLocked() }
        } catch { emit(["event": "error", "reason": "audio_write_failed"]) }
    }
    func finish() { lock.lock(); defer { lock.unlock() }; finishLocked() }
}

final class AudioOutput: NSObject, SCStreamOutput, SCStreamDelegate {
    let chunks: Chunks
    init(_ chunks: Chunks) { self.chunks = chunks }
    func stream(_ stream: SCStream, didStopWithError error: Error) {
        emit(["event": "error", "reason": "system_audio_stopped"])
    }
    func stream(_ stream: SCStream, didOutputSampleBuffer sample: CMSampleBuffer,
                of type: SCStreamOutputType) {
        guard type == .audio, CMSampleBufferDataIsReady(sample),
              let description = CMSampleBufferGetFormatDescription(sample),
              let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(description),
              asbd.pointee.mChannelsPerFrame == 1,
              let format = AVAudioFormat(streamDescription: asbd),
              let block = CMSampleBufferGetDataBuffer(sample) else { return }
        let count = CMSampleBufferGetNumSamples(sample)
        guard count > 0, count < 192000,
              let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(count))
        else { return }
        buffer.frameLength = AVAudioFrameCount(count)
        let list = buffer.mutableAudioBufferList.pointee
        guard list.mNumberBuffers == 1, let destination = list.mBuffers.mData,
              CMBlockBufferGetDataLength(block) <= Int(list.mBuffers.mDataByteSize) else { return }
        let status = CMBlockBufferCopyDataBytes(block, atOffset: 0,
            dataLength: CMBlockBufferGetDataLength(block), destination: destination)
        if status == kCMBlockBufferNoErr { chunks.append(buffer) }
    }
}

@main struct MeetingAudio {
    @MainActor static func main() async {
        let application = NSApplication.shared
        application.setActivationPolicy(.accessory)
        if CommandLine.arguments.contains("--detect") {
            let known = ["us.zoom.xos": "Zoom", "com.microsoft.teams2": "Teams",
                         "com.microsoft.teams": "Teams", "com.cisco.webexmeetingsapp": "Webex"]
            let meet = frontGoogleMeet()
            var names = meet ? ["Google Meet"] : []
            var active = meet
            let safariFront = NSWorkspace.shared.frontmostApplication?.bundleIdentifier == "com.apple.Safari"
            if #available(macOS 14.2, *) {
                var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyProcessObjectList,
                    mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
                var size: UInt32 = 0
                if AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject),
                                                   &address, 0, nil, &size) == noErr, size > 0 {
                    var processes = [AudioObjectID](repeating: 0, count: Int(size) / MemoryLayout<AudioObjectID>.size)
                    let status = processes.withUnsafeMutableBytes { bytes in
                        AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject),
                                                   &address, 0, nil, &size, bytes.baseAddress!)
                    }
                    if status == noErr {
                        for process in processes {
                            var input: UInt32 = 0
                            var valueSize = UInt32(MemoryLayout<UInt32>.size)
                            var inputAddress = AudioObjectPropertyAddress(mSelector: kAudioProcessPropertyIsRunningInput,
                                mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
                            guard AudioObjectGetPropertyData(process, &inputAddress, 0, nil,
                                                             &valueSize, &input) == noErr, input != 0 else { continue }
                            var bundle: CFString? = nil
                            var bundleSize = UInt32(MemoryLayout<CFString?>.size)
                            var bundleAddress = AudioObjectPropertyAddress(mSelector: kAudioProcessPropertyBundleID,
                                mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
                            let bundleStatus = withUnsafeMutablePointer(to: &bundle) { pointer in
                                AudioObjectGetPropertyData(process, &bundleAddress, 0, nil,
                                                           &bundleSize, pointer)
                            }
                            if bundleStatus == noErr, let bundle = bundle {
                                let id = bundle as String
                                if let name = known[id] { names.append(name); active = true }
                                else if isBrowser(id) ||
                                    (safariFront && id.hasPrefix("com.apple.WebKit.")) {
                                    names.append("Browser"); active = true
                                }
                            }
                        }
                    }
                }
            }
            if names.isEmpty {
                names = NSWorkspace.shared.runningApplications.compactMap { known[$0.bundleIdentifier ?? ""] }
            }
            emit(["event": "apps", "names": Array(Set(names)).sorted(), "active": active]); return

        }
        guard CommandLine.arguments.count == 2 else { exit(2) }
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: root.path, isDirectory: &isDirectory),
              isDirectory.boolValue else { exit(2) }
        let microphone = AVAudioEngine()
        let mic = Chunks(root: root, source: "microphone")
        let system = Chunks(root: root, source: "computer")
        var capture: SCStream?
        var tapped = false
        do {
            emit(["event": "permission", "target": "microphone"])
            guard await AVCaptureDevice.requestAccess(for: .audio) else {
                emit(["event": "error", "reason": "microphone_permission"]); return
            }
            emit(["event": "permission", "target": "system_audio"])
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            guard let display = content.displays.first else {
                emit(["event": "error", "reason": "no_display"]); return
            }
            let filter = SCContentFilter(display: display, excludingApplications: [], exceptingWindows: [])
            let config = SCStreamConfiguration()
            config.capturesAudio = true
            config.excludesCurrentProcessAudio = true
            config.sampleRate = 16000
            config.channelCount = 1
            config.width = 2; config.height = 2
            config.minimumFrameInterval = CMTime(value: 1, timescale: 1)
            let handler = AudioOutput(system)
            let stream = SCStream(filter: filter, configuration: config, delegate: handler)
            capture = stream
            try stream.addStreamOutput(handler, type: .audio,
                                       sampleHandlerQueue: DispatchQueue(label: "aedrova.meeting.audio"))
            try await stream.startCapture()
            let input = microphone.inputNode
            let format = input.outputFormat(forBus: 0)
            guard format.sampleRate > 0, format.channelCount > 0 else {
                throw NSError(domain: "Aedrova", code: 1)
            }
            input.installTap(onBus: 0, bufferSize: 4096, format: format) { buffer, _ in mic.append(buffer) }
            tapped = true
            try microphone.start()
            emit(["event": "ready"])
            await withCheckedContinuation { (done: CheckedContinuation<Void, Never>) in
                DispatchQueue.global().async { _ = readLine(); done.resume() }
            }
            microphone.stop(); input.removeTap(onBus: 0); tapped = false
            try await stream.stopCapture()
            withExtendedLifetime(handler) { system.finish(); mic.finish() }
            emit(["event": "stopped"])
        } catch {
            microphone.stop()
            if tapped { microphone.inputNode.removeTap(onBus: 0) }
            if let stream = capture { try? await stream.stopCapture() }
            system.finish(); mic.finish()
            emit(["event": "error", "reason": "capture_unavailable"])
        }
    }
}
