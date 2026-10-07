import Foundation
import Darwin
import IOBluetooth
import Network

private struct BridgeRequest: Decodable {
    let authToken: String?
    let framesBase64: [String]
    let speedMs: UInt16
    let diagnosticCodec: String?
    let frameEncoding: String?
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

private enum TransferEvent {
    case sendAll
    case chunk(Int)
    case acknowledged

    static func decode(_ packet: Data) -> TransferEvent? {
        let bytes = Array(packet)
        guard bytes.count >= 7, bytes[3] == 0x04 else { return nil }
        let body = Array(bytes[4..<(bytes.count - 3)])
        // Final completion response observed in Android captures and macOS
        // transfers. A chunk request or another device response is not an ACK.
        if body == [0xBD, 0x55, 0x13, 0x01, 0x05, 0x00] {
            return .acknowledged
        }
        guard body.count >= 3, body[0] == 0x8B, body[1] == 0x55 else { return nil }
        if body[2] == 0x00 { return .sendAll }
        if body[2] == 0x01, body.count >= 7 {
            let index = (0..<4).reduce(UInt32(0)) { partial, offset in
                partial | (UInt32(body[3 + offset]) << (UInt32(offset) * 8))
            }
            return .chunk(Int(index))
        }
        return nil
    }
}

private final class RFCOMMDelegate: NSObject, IOBluetoothRFCOMMChannelDelegate {
    private let condition = NSCondition()
    private var received = Data()
    private var closed = false

    func reset() {
        condition.lock()
        received.removeAll(keepingCapacity: true)
        condition.unlock()
    }

    func rfcommChannelData(
        _ rfcommChannel: IOBluetoothRFCOMMChannel!,
        data dataPointer: UnsafeMutableRawPointer!,
        length dataLength: Int
    ) {
        condition.lock()
        received.append(Data(bytes: dataPointer, count: dataLength))
        condition.broadcast()
        condition.unlock()
        let hex = Data(bytes: dataPointer, count: dataLength).prefix(64)
            .map { String(format: "%02x", $0) }.joined(separator: " ")
        fputs("MiniToo bridge: received \(dataLength) Bluetooth bytes: \(hex)\n", stderr)
    }

    func rfcommChannelClosed(_ rfcommChannel: IOBluetoothRFCOMMChannel!) {
        condition.lock()
        closed = true
        condition.broadcast()
        condition.unlock()
        fputs("MiniToo bridge: Bluetooth RFCOMM channel closed.\n", stderr)
    }

    func nextPacket(timeout: TimeInterval) throws -> Data? {
        let deadline = Date().addingTimeInterval(timeout)
        condition.lock()
        defer { condition.unlock() }

        while Date() < deadline {
            if closed {
                throw NSError(domain: "DivoomMiniTooCodex", code: 1, userInfo: [
                    NSLocalizedDescriptionKey: "Bluetooth disconnected while waiting for a MiniToo response."
                ])
            }
            while let first = received.first, first != 0x01 {
                received.removeFirst()
            }
            // Data can retain a non-zero startIndex after removeFirst(). Copy
            // to byte storage before using protocol offsets from zero.
            let bytes = Array(received)
            if bytes.count >= 4 {
                let declaredLength = Int(bytes[1]) | (Int(bytes[2]) << 8)
                let packetLength = declaredLength + 4
                // Inbound control packets are small. An impossible length
                // must not hide later valid packets behind a corrupt header.
                if packetLength < 7 || packetLength > 4096 {
                    received.removeFirst()
                    continue
                }
                if bytes.count >= packetLength {
                    let packetBytes = Array(bytes.prefix(packetLength))
                    let checksum = packetBytes[1..<(packetLength - 3)].reduce(UInt16(0)) { $0 &+ UInt16($1) }
                    let expected = UInt16(packetBytes[packetLength - 3]) | (UInt16(packetBytes[packetLength - 2]) << 8)
                    if packetBytes.last == 0x02, checksum == expected {
                        received.removeFirst(packetLength)
                        return Data(packetBytes)
                    }
                    // A complete frame with a bad checksum cannot confirm a
                    // transfer. Discard it as a unit so its body bytes cannot
                    // become a false header in front of the next response.
                    received.removeFirst(packetBytes.last == 0x02 ? packetLength : 1)
                    continue
                }
            }
            if !condition.wait(until: deadline) {
                break
            }
        }
        return nil
    }
}

private final class MiniTooBridge {
    private let address: String
    private let port: UInt16
    private let authToken: String
    private let requestTimeout: TimeInterval
    private let connectionLimit: Int
    private var connections: [ObjectIdentifier: LocalConnectionState] = [:]
    private let delegate = RFCOMMDelegate()
    private let workQueue = DispatchQueue(label: "divoom.minitoo.work")
    private let transferQueue = DispatchQueue(label: "divoom.minitoo.transfer")
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

    func start(resetBluetoothLink: Bool = false) throws {
        guard let device = IOBluetoothDevice(addressString: address) else {
            throw bridgeError("Bluetooth device not found at \(address). Pair the MiniToo first.")
        }
        self.device = device
        if resetBluetoothLink {
            try resetBasebandConnection(device, reason: "bounded retry after a failed display transfer")
        }
        var opened: IOBluetoothRFCOMMChannel?
        let result = device.openRFCOMMChannelSync(&opened, withChannelID: 1, delegate: delegate)
        guard result == kIOReturnSuccess, let opened else {
            let disconnectResult = device.closeConnection()
            log("closed Bluetooth baseband after RFCOMM failure (\(returnCode(disconnectResult)))")
            throw bridgeError("Could not open MiniToo RFCOMM channel (\(returnCode(result))).")
        }
        channel = opened
        try startListener()
    }

    private func resetBasebandConnection(_ device: IOBluetoothDevice, reason: String) throws {
        log("resetting Bluetooth baseband link (\(reason))")
        let closeResult = device.closeConnection()
        log("Bluetooth baseband close returned \(returnCode(closeResult))")
        Thread.sleep(forTimeInterval: 1.0)
        let openResult = device.openConnection()
        guard openResult == kIOReturnSuccess || device.isConnected() else {
            throw bridgeError(
                "Bluetooth baseband reconnect failed after RFCOMM trouble " +
                "(close: \(returnCode(closeResult)), reconnect: \(returnCode(openResult)))."
            )
        }
        log("Bluetooth baseband link restored (\(returnCode(openResult)))")
        Thread.sleep(forTimeInterval: 0.5)
    }

    func shutdown() {
        listener?.cancel()
        listener = nil
        if let channel {
            let result = channel.close()
            log("closed RFCOMM channel during shutdown (\(returnCode(result)))")
            self.channel = nil
        }
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
        let listenerPort = port
        listener?.newConnectionHandler = { [weak self] connection in
            self?.handle(connection)
        }
        listener?.stateUpdateHandler = { state in
            if case .ready = state {
                #if MINITOO_RGB_DIAGNOSTIC || MINITOO_SQUARE_JPEG_DIAGNOSTIC
                fputs("MiniToo bridge: authenticated local listener ready on port \(listenerPort).\n", stderr)
                #else
                fputs("MiniToo bridge: authenticated local listener ready on port \(listenerPort). RGB888/Zstandard supported.\n", stderr)
                #endif
            } else if case .failed(let error) = state {
                fputs("MiniToo bridge listener failed: \(error)\n", stderr)
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
                self.log("request socket failed: \(error.localizedDescription)")
                self.reply(connection, BridgeResponse(ok: false, message: error.localizedDescription, chunks: nil, acknowledged: nil))
                return
            }
            let current = accumulated + (data ?? Data())
            if current.isEmpty && complete {
                self.finishConnection(connection)
                return
            }
            if current.count > 512 * 1024 {
                self.log("rejected oversized request (\(current.count) bytes)")
                self.reply(connection, BridgeResponse(ok: false, message: "Image request is too large.", chunks: nil, acknowledged: nil))
                return
            }
            if let newline = current.firstIndex(of: 0x0a) {
                self.log("received \(newline) bytes from monitor")
                self.processRequest(Data(current[..<newline]), on: connection)
                return
            }
            if !complete {
                self.receiveRequest(connection, accumulated: current)
                return
            }
            self.processRequest(current, on: connection)
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
            #if MINITOO_RGB_DIAGNOSTIC
            guard request.frameEncoding == nil,
                  request.diagnosticCodec == "rgb888-zstd", request.framesBase64.count == 1 else {
                throw bridgeError("This diagnostic bridge requires one 128x128 RGB888 frame.")
            }
            #elseif MINITOO_SQUARE_JPEG_DIAGNOSTIC
            guard request.frameEncoding == nil,
                  request.diagnosticCodec == "jpeg128", request.framesBase64.count == 1 else {
                throw bridgeError("This diagnostic bridge requires one 128x128 JPEG frame.")
            }
            #else
            guard request.diagnosticCodec == nil else {
                throw bridgeError("Codec comparisons require their separately compiled diagnostic bridge.")
            }
            #endif
            let frames: [Data]
            let rgbPayload: Data?
            if request.frameEncoding == "rgb-zstd" {
                guard request.framesBase64.count == 1,
                      let payload = Data(base64Encoded: request.framesBase64[0]), payload.count < 384 * 1024 else {
                    throw bridgeError("Invalid or oversized RGB image payload.")
                }
                try validateRGBPayload(payload, speedMs: request.speedMs)
                frames = []
                rgbPayload = payload
            } else {
                guard request.frameEncoding == nil else {
                    throw bridgeError("Unsupported MiniToo image encoding.")
                }
                guard (1...8).contains(request.framesBase64.count) else {
                    throw bridgeError("MiniToo supports between 1 and 8 image frames.")
                }
                frames = try request.framesBase64.map { encoded -> Data in
                    guard let frame = Data(base64Encoded: encoded), frame.count < 256 * 1024 else {
                        throw bridgeError("Invalid or oversized image frame.")
                    }
                    #if MINITOO_RGB_DIAGNOSTIC
                    guard frame.count == 128 * 128 * 3 else {
                        throw bridgeError("The RGB diagnostic frame must contain exactly 49152 bytes.")
                    }
                    #endif
                    return frame
                }
                rgbPayload = nil
            }
            transferQueue.async {
                guard self.workQueue.sync(execute: { self.connections[ObjectIdentifier(connection)] != nil }) else { return }
                do {
                    self.log(rgbPayload == nil
                        ? "transferring \(frames.count) frame(s) over Bluetooth"
                        : "transferring RGB888/Zstandard animation over Bluetooth")
                    self.reply(connection, try self.send(frames: frames, speedMs: request.speedMs, rgbPayload: rgbPayload))
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

    private func send(frames: [Data], speedMs: UInt16, rgbPayload: Data? = nil) throws -> BridgeResponse {
        guard let channel, channel.isOpen() else {
            throw bridgeError("Bluetooth connection to MiniToo is closed.")
        }
        let payload = rgbPayload ?? encodePayload(frames: frames, speedMs: speedMs)
        let chunks = makeChunks(payload)
        log("prepared \(payload.count) payload bytes in \(chunks.count) chunk(s)")
        delegate.reset()
        let deadline = Date().addingTimeInterval(40)

        var startData = Data([0x00])
        startData.append(littleEndian(UInt32(payload.count)))
        startData.append(0x00)
        try write(packet(command: 0x8B, body: startData))

        var sentChunks = Set<Int>()
        var requestCount = 0
        var event = try nextTransferEvent(timeout: 5, allowAcknowledgement: false)
        guard event != nil else {
            log("no initial transfer request; 0/\(chunks.count) chunks sent; refusing blind upload")
            throw bridgeError(
                "MiniToo did not request frame data within 5 seconds; no image chunks were sent. " +
                "The Bluetooth session may be unresponsive or the device may still be loading a previous transfer."
            )
        }

        var acknowledged = false
        while deadline.timeIntervalSinceNow > 0 {
            if let current = event {
                switch current {
                case .sendAll:
                    requestCount += 1
                    guard requestCount <= chunks.count * 2 + 4 else {
                        throw bridgeError("MiniToo exceeded the transfer request limit.")
                    }
                    log("device requested all \(chunks.count) chunks")
                    try sendAll(chunks, deadline: deadline)
                    sentChunks = Set(chunks.indices)
                case .chunk(let index):
                    requestCount += 1
                    guard chunks.indices.contains(index) else {
                        throw bridgeError("MiniToo requested invalid chunk \(index) of \(chunks.count).")
                    }
                    guard requestCount <= chunks.count * 2 + 4 else {
                        throw bridgeError("MiniToo exceeded the transfer request limit.")
                    }
                    try write(chunks[index])
                    sentChunks.insert(index)
                    log("device requested chunk \(index); sent \(sentChunks.count)/\(chunks.count) unique chunks")
                case .acknowledged:
                    // An ACK before any data belongs to an earlier transfer.
                    if !sentChunks.isEmpty { acknowledged = true }
                }
            }
            if acknowledged { break }
            let waitTime = min(sentChunks.count == chunks.count ? 4.0 : 10.0, deadline.timeIntervalSinceNow)
            event = try nextTransferEvent(timeout: waitTime)
            if event == nil { break }
        }
        log("Bluetooth transfer finished; sent \(sentChunks.count)/\(chunks.count) unique chunks; final acknowledgement: \(acknowledged)")
        return BridgeResponse(
            ok: true,
            message: acknowledged ? "sent" : "sent; no final acknowledgement observed",
            chunks: chunks.count,
            acknowledged: acknowledged
        )
    }

    private func nextTransferEvent(timeout: TimeInterval, allowAcknowledgement: Bool = true) throws -> TransferEvent? {
        let deadline = Date().addingTimeInterval(timeout)
        while deadline.timeIntervalSinceNow > 0 {
            guard let packet = try delegate.nextPacket(timeout: deadline.timeIntervalSinceNow) else { return nil }
            let hex = packet.prefix(32).map { String(format: "%02x", $0) }.joined(separator: " ")
            if let event = TransferEvent.decode(packet) {
                if case .acknowledged = event, !allowAcknowledgement {
                    log("ignored acknowledgement before any frame data was sent: \(hex)")
                    continue
                }
                log("transfer response: \(hex)")
                return event
            }
            log("ignored unrelated response: \(hex)")
        }
        return nil
    }

    private func sendAll(_ chunks: [Data], deadline: Date) throws {
        for (index, chunk) in chunks.enumerated() {
            guard deadline.timeIntervalSinceNow > 0 else {
                throw bridgeError("MiniToo transfer exceeded its 40-second deadline at chunk \(index).")
            }
            try write(chunk)
            if index + 1 < chunks.count {
                Thread.sleep(forTimeInterval: 0.012)
            }
        }
    }

    private func write(_ data: Data) throws {
        guard let channel, channel.isOpen() else {
            throw bridgeError("Bluetooth connection to MiniToo is closed.")
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

    private func encodePayload(frames: [Data], speedMs: UInt16) -> Data {
        #if MINITOO_RGB_DIAGNOSTIC
        // Diagnostic only: one 128x128 RGB888 frame, matching the documented
        // Android 0x25 route. A Zstd raw block preserves every byte and needs
        // no external compression library. Its explicit window is 128 KiB.
        let rgb = frames[0] // Size and frame count validated before transfer.
        var zstd = Data([0x28, 0xB5, 0x2F, 0xFD, 0x40, 0x38])
        zstd.append(littleEndian(UInt16(rgb.count - 256)))
        let blockHeader = (UInt32(rgb.count) << 3) | 1 // Last block; raw type.
        zstd.append(contentsOf: (0..<3).map { UInt8((blockHeader >> (UInt32($0) * 8)) & 0xFF) })
        zstd.append(rgb)
        var payload = Data([0x25, 0x01])
        payload.append(bigEndian(speedMs))
        payload.append(contentsOf: [0x08, 0x08])
        payload.append(bigEndian(UInt32(zstd.count)))
        payload.append(zstd)
        return payload
        #else
        // Each frame is a 160x128 JPEG in the MiniToo's 8x10 tile grid.
        var payload = Data([0x23, UInt8(frames.count)])
        payload.append(bigEndian(speedMs))
        #if MINITOO_SQUARE_JPEG_DIAGNOSTIC
        payload.append(contentsOf: [0x08, 0x08])
        #else
        payload.append(contentsOf: [0x08, 0x0A])
        #endif
        for jpeg in frames {
            payload.append(0x01)
            payload.append(bigEndian(UInt32(jpeg.count)))
            payload.append(jpeg)
        }
        return payload
        #endif
    }

    private func validateRGBPayload(_ payload: Data, speedMs: UInt16) throws {
        let bytes = Array(payload)
        guard bytes.count >= 18, bytes[0] == 0x25, (1...8).contains(Int(bytes[1])),
              bytes[4] == 8, bytes[5] == 10,
              UInt16(bytes[2]) * 256 + UInt16(bytes[3]) == speedMs else {
            throw bridgeError("RGB payload must contain 1–8 native 160x128 frames with the requested speed.")
        }
        let length = (6..<10).reduce(UInt32(0)) { ($0 << 8) | UInt32(bytes[$1]) }
        guard Int(length) == bytes.count - 10 else {
            throw bridgeError("RGB payload length does not match its Zstandard stream.")
        }
        let zstd = Array(bytes.dropFirst(10))
        guard zstd.count >= 8, Array(zstd.prefix(4)) == [0x28, 0xB5, 0x2F, 0xFD],
              zstd[4] & 0x1B == 0 else {
            throw bridgeError("RGB payload requires a standard Zstandard frame without a dictionary.")
        }
        let descriptor = zstd[4]
        let singleSegment = descriptor & 0x20 != 0
        var offset = 5
        var window: UInt64 = 0
        if !singleSegment {
            guard offset < zstd.count else { throw bridgeError("Truncated Zstandard window.") }
            let base = UInt64(1) << (10 + UInt64(zstd[offset] >> 3))
            window = base + (base / 8) * UInt64(zstd[offset] & 7)
            offset += 1
        }
        let sizeBytes = [singleSegment ? 1 : 0, 2, 4, 8][Int(descriptor >> 6)]
        guard sizeBytes > 0, offset + sizeBytes <= zstd.count else {
            throw bridgeError("RGB Zstandard stream must declare its decompressed size.")
        }
        var contentSize = (0..<sizeBytes).reduce(UInt64(0)) {
            $0 | (UInt64(zstd[offset + $1]) << (UInt64($1) * 8))
        }
        if sizeBytes == 2 { contentSize += 256 }
        offset += sizeBytes
        if singleSegment { window = contentSize }
        guard contentSize == UInt64(bytes[1]) * 160 * 128 * 3,
              window > 0, window <= 128 * 1024 else {
            throw bridgeError("RGB Zstandard size must match the frames and its window must not exceed 128 KiB.")
        }
        while true {
            guard offset + 3 <= zstd.count else { throw bridgeError("Truncated Zstandard block header.") }
            let header = Int(zstd[offset]) | (Int(zstd[offset + 1]) << 8) | (Int(zstd[offset + 2]) << 16)
            offset += 3
            let type = (header >> 1) & 3
            let size = header >> 3
            let storedSize = type == 1 ? 1 : size
            guard type != 3, UInt64(size) <= min(window, 128 * 1024),
                  offset + storedSize <= zstd.count else {
                throw bridgeError("Invalid or truncated Zstandard block.")
            }
            offset += storedSize
            if header & 1 != 0 { break }
        }
        if descriptor & 4 != 0 { offset += 4 }
        guard offset == zstd.count else { throw bridgeError("Unexpected bytes after the RGB Zstandard frame.") }
    }

    private func makeChunks(_ payload: Data) -> [Data] {
        var chunks: [Data] = []
        let count = (payload.count + 255) / 256
        for index in 0..<count {
            let start = index * 256
            let end = min(start + 256, payload.count)
            var body = Data([0x01])
            body.append(littleEndian(UInt32(payload.count)))
            body.append(littleEndian(UInt16(index)))
            body.append(payload[start..<end])
            chunks.append(packet(command: 0x8B, body: body))
        }
        return chunks
    }

    private func packet(command: UInt8, body: Data) -> Data {
        let declaredLength = UInt16(body.count + 3)
        var result = Data([0x01])
        result.append(littleEndian(declaredLength))
        result.append(command)
        result.append(body)
        let checksum = result.dropFirst().reduce(UInt16(0)) { partial, byte in
            partial &+ UInt16(byte)
        }
        result.append(littleEndian(checksum))
        result.append(0x02)
        return result
    }

    private func littleEndian(_ value: UInt16) -> Data {
        Data([UInt8(value & 0xFF), UInt8((value >> 8) & 0xFF)])
    }

    private func littleEndian(_ value: UInt32) -> Data {
        Data((0..<4).map { UInt8((value >> (UInt32($0) * 8)) & 0xFF) })
    }

    private func bigEndian(_ value: UInt32) -> Data {
        Data((0..<4).reversed().map { UInt8((value >> (UInt32($0) * 8)) & 0xFF) })
    }

    private func bigEndian(_ value: UInt16) -> Data {
        Data([UInt8((value >> 8) & 0xFF), UInt8(value & 0xFF)])
    }

    private func bridgeError(_ message: String) -> NSError {
        NSError(domain: "DivoomMiniTooCodex", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }

    private func log(_ message: String) {
        fputs("MiniToo bridge: \(message)\n", stderr)
    }

    private func returnCode(_ value: IOReturn) -> String {
        "0x\(String(value, radix: 16))"
    }
}

let arguments = CommandLine.arguments
guard arguments.count >= 2 else {
    fputs("Usage: minitoo-bridge <bluetooth-address> [localhost-port] [--reset-link]\n", stderr)
    exit(2)
}
let address = arguments[1]
let port = arguments.count >= 3 ? UInt16(arguments[2]) ?? 40584 : 40584
guard let authToken = readLine(), authToken.utf8.count == 64,
      authToken.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else {
    fputs("Missing or invalid local bridge credential. Start through codex-minitoo.\n", stderr)
    exit(2)
}
private let bridge = MiniTooBridge(address: address, port: port, authToken: authToken)
let resetBluetoothLink = arguments.contains("--reset-link")
signal(SIGINT, SIG_IGN)
signal(SIGTERM, SIG_IGN)
let shutdownSignals = [SIGINT, SIGTERM].map { value -> DispatchSourceSignal in
    let source = DispatchSource.makeSignalSource(signal: value, queue: .main)
    source.setEventHandler {
        bridge.shutdown()
        CFRunLoopStop(CFRunLoopGetMain())
    }
    source.resume()
    return source
}
do {
    try bridge.start(resetBluetoothLink: resetBluetoothLink)
    RunLoop.main.run()
} catch {
    bridge.shutdown()
    fputs("MiniToo bridge: \(error.localizedDescription)\n", stderr)
    exit(1)
}
shutdownSignals.forEach { $0.cancel() }
bridge.shutdown()
