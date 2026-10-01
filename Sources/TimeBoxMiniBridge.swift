import Foundation
import IOBluetooth
import Network

private struct BridgeRequest: Decodable {
    let authToken: String?
    let framesBase64: [String]
    let speedMs: UInt16
}

private final class LocalConnectionState {
    var receiving = true
    var deadline: DispatchWorkItem?
}

private struct BridgeResponse: Encodable {
    let ok: Bool
    let message: String
    let chunks: Int?
    let acknowledged: Bool?
}

/// The TimeBox Mini sends a short HELLO message and command acknowledgements.
/// The callback consumes those bytes so its RFCOMM receive buffer cannot fill.
private final class TimeBoxMiniDelegate: NSObject, IOBluetoothRFCOMMChannelDelegate {
    func rfcommChannelClosed(_ rfcommChannel: IOBluetoothRFCOMMChannel!) {
        fputs("TimeBox Mini bridge: Bluetooth RFCOMM channel closed.\n", stderr)
    }

    func rfcommChannelData(
        _ rfcommChannel: IOBluetoothRFCOMMChannel!,
        data dataPointer: UnsafeMutableRawPointer!,
        length dataLength: Int
    ) {
        // Receiving the callback is enough to drain the device's RFCOMM stream.
    }
}

private final class TimeBoxMiniBridge {
    private let address: String
    private let port: UInt16
    private let authToken: String
    private let requestTimeout: TimeInterval
    private let connectionLimit: Int
    private var connections: [ObjectIdentifier: LocalConnectionState] = [:]
    private let delegate = TimeBoxMiniDelegate()
    private let workQueue = DispatchQueue(label: "divoom.timeboxmini.work")
    private let transferQueue = DispatchQueue(label: "divoom.timeboxmini.transfer")
    private var device: IOBluetoothDevice?
    private var channel: IOBluetoothRFCOMMChannel?
    private var listener: NWListener?

    init(address: String, port: UInt16, authToken: String,
         requestTimeout: TimeInterval = 10, connectionLimit: Int = 4) {
        self.address = address
        self.port = port
        self.authToken = authToken
        self.requestTimeout = requestTimeout
        self.connectionLimit = connectionLimit
    }

    func start() throws {
        guard let device = IOBluetoothDevice(addressString: address) else {
            throw bridgeError("Bluetooth device not found at \(address). Pair the TimeBox Mini first.")
        }
        self.device = device
        var opened: IOBluetoothRFCOMMChannel?
        let result = device.openRFCOMMChannelSync(&opened, withChannelID: 4, delegate: delegate)
        guard result == kIOReturnSuccess, let opened else {
            throw bridgeError(
                "Could not open TimeBox Mini RFCOMM channel 4 (0x\(String(result, radix: 16))). " +
                "Close the Divoom app's connection, then retry."
            )
        }
        channel = opened
        try startListener()
    }

    private func startListener() throws {
        guard let nwPort = NWEndpoint.Port(rawValue: port) else {
            throw bridgeError("Invalid local bridge port.")
        }
        let parameters = NWParameters.tcp
        // Exclusive binding prevents a competing local listener from sharing this port.
        parameters.allowLocalEndpointReuse = false
        parameters.requiredLocalEndpoint = .hostPort(host: .ipv4(.loopback), port: nwPort)
        listener = try NWListener(using: parameters)
        listener?.newConnectionHandler = { [weak self] connection in
            self?.handle(connection)
        }
        listener?.stateUpdateHandler = { state in
            if case .ready = state {
                fputs("TimeBox Mini bridge: authenticated local listener ready on port \(nwPort).\n", stderr)
            } else if case .failed(let error) = state {
                fputs("TimeBox Mini bridge listener failed: \(error)\n", stderr)
                exit(1)
            }
        }
        listener?.start(queue: workQueue)
    }

    private func handle(_ connection: NWConnection) {
        guard connections.count < connectionLimit else {
            connection.cancel()
            return
        }
        let state = LocalConnectionState()
        connections[ObjectIdentifier(connection)] = state
        connection.stateUpdateHandler = { [weak self, weak connection] status in
            guard let self, let connection else { return }
            switch status {
            case .failed, .cancelled:
                self.finishConnection(connection)
            default:
                break
            }
        }
        let timeout = DispatchWorkItem { [weak self, weak connection] in
            guard let self, let connection,
                  self.connections[ObjectIdentifier(connection)]?.receiving == true else { return }
            self.finishConnection(connection)
        }
        state.deadline = timeout
        workQueue.asyncAfter(deadline: .now() + requestTimeout, execute: timeout)
        connection.start(queue: workQueue)
        receiveRequest(connection, accumulated: Data())
    }

    private func finishConnection(_ connection: NWConnection) {
        if let state = connections.removeValue(forKey: ObjectIdentifier(connection)) {
            state.receiving = false
            state.deadline?.cancel()
        }
        connection.cancel()
    }

    private func authenticated(_ token: String?) -> Bool {
        guard let token, token.utf8.count == 64 else { return false }
        let expected = Array(authToken.utf8)
        let supplied = Array(token.utf8)
        guard expected.count == supplied.count else { return false }
        var difference: UInt8 = 0
        for index in expected.indices { difference |= expected[index] ^ supplied[index] }
        return difference == 0
    }

    private func receiveRequest(_ connection: NWConnection, accumulated: Data) {
        connection.receive(minimumIncompleteLength: 1, maximumLength: 512 * 1024) { [weak self] data, _, complete, error in
            guard let self else {
                connection.cancel()
                return
            }
            guard self.connections[ObjectIdentifier(connection)]?.receiving == true else { return }
            if let error {
                self.reply(connection, BridgeResponse(ok: false, message: error.localizedDescription, chunks: nil, acknowledged: nil))
                return
            }
            let current = accumulated + (data ?? Data())
            if current.isEmpty && complete {
                self.finishConnection(connection)
                return
            }
            if current.count > 512 * 1024 {
                self.reply(connection, BridgeResponse(ok: false, message: "Image request is too large.", chunks: nil, acknowledged: nil))
                return
            }
            if let newline = current.firstIndex(of: 0x0a) {
                self.processRequest(Data(current[..<newline]), on: connection)
            } else if !complete {
                self.receiveRequest(connection, accumulated: current)
            } else {
                self.processRequest(current, on: connection)
            }
        }
    }

    private func decodeAuthenticatedRequest(_ data: Data) throws -> BridgeRequest {
        let request = try JSONDecoder().decode(BridgeRequest.self, from: data)
        guard authenticated(request.authToken) else {
            throw bridgeError("Unauthorized local bridge request.")
        }
        return request
    }

    private func processRequest(_ data: Data, on connection: NWConnection) {
        guard let state = connections[ObjectIdentifier(connection)], state.receiving else { return }
        state.receiving = false
        state.deadline?.cancel()
        do {
            let request = try decodeAuthenticatedRequest(data)
            guard request.framesBase64.count == 1,
                  let packedPixels = Data(base64Encoded: request.framesBase64[0]),
                  packedPixels.count == 182 else {
                throw bridgeError("TimeBox Mini expects one packed 11x11 RGB444 image (182 bytes).")
            }
            transferQueue.async {
                guard self.workQueue.sync(execute: { self.connections[ObjectIdentifier(connection)] != nil }) else { return }
                do {
                    try self.sendImage(packedPixels)
                    self.reply(connection, BridgeResponse(ok: true, message: "image sent", chunks: 1, acknowledged: nil))
                } catch {
                    self.reply(connection, BridgeResponse(ok: false, message: error.localizedDescription, chunks: nil, acknowledged: nil))
                }
            }
        } catch {
            reply(connection, BridgeResponse(ok: false, message: error.localizedDescription, chunks: nil, acknowledged: nil))
        }
    }

    private func reply(_ connection: NWConnection, _ response: BridgeResponse) {
        workQueue.async { [self, connection] in
            guard let state = self.connections[ObjectIdentifier(connection)] else { return }
            state.receiving = false
            state.deadline?.cancel()
            let timeout = DispatchWorkItem { [weak self, weak connection] in
                guard let self, let connection else { return }
                self.finishConnection(connection)
            }
            state.deadline = timeout
            self.workQueue.asyncAfter(deadline: .now() + 5, execute: timeout)
            let data = (try? JSONEncoder().encode(response)) ?? Data("{\"ok\":false,\"message\":\"response encoding failed\"}".utf8)
            connection.send(content: data + Data([0x0a]), completion: .contentProcessed { _ in
                self.finishConnection(connection)
            })
        }
    }

    private func sendImage(_ packedPixels: Data) throws {
        guard let channel, channel.isOpen() else {
            throw bridgeError("Bluetooth connection to TimeBox Mini is closed.")
        }
        // Static image: command 0x44, mode 0, 11 rows, 11 columns, RGB444.
        var command = Data([0x44, 0x00, 0x0A, 0x0A, 0x04])
        command.append(packedPixels)
        try write(encodePacket(command))
    }

    private func encodePacket(_ command: Data) -> Data {
        var message = Data([0x00, 0x00])
        message.append(command)
        let declaredLength = UInt16(message.count)
        message[0] = UInt8(declaredLength & 0xFF)
        message[1] = UInt8((declaredLength >> 8) & 0xFF)
        let checksum = message.reduce(UInt16(0)) { $0 &+ UInt16($1) }
        message.append(UInt8(checksum & 0xFF))
        message.append(UInt8((checksum >> 8) & 0xFF))

        var packet = Data([0x01])
        for byte in message {
            if byte == 0x01 || byte == 0x02 || byte == 0x03 {
                packet.append(contentsOf: [0x03, byte + 0x03])
            } else {
                packet.append(byte)
            }
        }
        packet.append(0x02)
        return packet
    }

    private func write(_ data: Data) throws {
        guard let channel, channel.isOpen() else {
            throw bridgeError("Bluetooth connection to TimeBox Mini is closed.")
        }
        var mutableData = data
        let length = UInt16(mutableData.count)
        let result = mutableData.withUnsafeMutableBytes { buffer in
            channel.writeSync(buffer.baseAddress, length: length)
        }
        guard result == kIOReturnSuccess else {
            throw bridgeError("RFCOMM write failed (0x\(String(result, radix: 16))).")
        }
    }

    private func bridgeError(_ message: String) -> NSError {
        NSError(domain: "DivoomTimeBoxMiniCodex", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }
}

let arguments = CommandLine.arguments
guard arguments.count >= 2 else {
    fputs("Usage: timebox-mini-bridge <bluetooth-address> [localhost-port]\n", stderr)
    exit(2)
}
let address = arguments[1]
let port = arguments.count >= 3 ? UInt16(arguments[2]) ?? 40585 : 40585
guard let authToken = readLine(), authToken.utf8.count == 64,
      authToken.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else {
    fputs("Missing or invalid local bridge credential. Start through codex-minitoo.\n", stderr)
    exit(2)
}
private let bridge = TimeBoxMiniBridge(address: address, port: port, authToken: authToken)
do {
    try bridge.start()
    RunLoop.main.run()
} catch {
    fputs("TimeBox Mini bridge: \(error.localizedDescription)\n", stderr)
    exit(1)
}
