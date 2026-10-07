import CoreAudio
import Foundation

private func emit(available: Bool, active: Bool, reason: String? = nil) {
    var message: [String: Any] = [
        "available": available,
        "active": active,
    ]
    if let reason { message["reason"] = reason }
    let data = try? JSONSerialization.data(withJSONObject: message)
    guard let data else { return }
    var line = data
    line.append(0x0A)
    try? FileHandle.standardOutput.write(contentsOf: line)
}

@available(macOS 14.2, *)
private func microphoneInputIsActive() throws -> Bool {
    let processes = try AudioHardwareSystem.shared.processes
    for process in processes {
        // Browser calls can capture from renderer/helper processes whose
        // bundle IDs differ across browsers, versions, and wrapper apps.
        // Core Audio exposes whether each client has a live input stream.
        guard (try? process.isRunningInput) == true else { continue }
        return true
    }
    return false
}

if #available(macOS 14.2, *) {
    while true {
        do {
            emit(available: true, active: try microphoneInputIsActive())
        } catch {
            emit(available: false, active: false, reason: error.localizedDescription)
            break
        }
        Thread.sleep(forTimeInterval: 1)
    }
} else {
    emit(available: false, active: false)
}
