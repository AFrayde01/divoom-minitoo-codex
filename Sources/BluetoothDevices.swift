import Foundation
import IOBluetooth

// Read the paired-device inventory without opening audio or RFCOMM channels.
// Device names are used only as model hints; availability is checked by the
// normal authenticated bridge when the monitor starts.
let paired = IOBluetoothDevice.pairedDevices() as? [IOBluetoothDevice] ?? []
var devices: [[String: Any]] = []
for device in paired {
    let name = device.name ?? ""
    let hint = name.lowercased().filter { $0.isLetter || $0.isNumber }
    guard hint.contains("minitoo") || hint.contains("timeboxmini") || hint.contains("divoom"),
          let address = device.addressString else { continue }
    devices.append(["name": name, "address": address, "connected": device.isConnected()])
}
do {
    let data = try JSONSerialization.data(withJSONObject: ["devices": devices], options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([0x0A]))
} catch {
    FileHandle.standardError.write(Data("Could not read the Bluetooth device inventory.\n".utf8))
    exit(1)
}
