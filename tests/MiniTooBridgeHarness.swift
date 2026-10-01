// Appended to the production source by test_swift_bridge.py. The simulated
// channel exercises the real transfer loop without opening Bluetooth.
private final class SimulatedChannel: IOBluetoothRFCOMMChannel {
    var onWrite: ((Data) -> Void)?
    var chunkIndices: [Int] = []

    override func isOpen() -> Bool { true }

    override func writeSync(_ data: UnsafeMutableRawPointer!, length: UInt16) -> IOReturn {
        let packet = Data(bytes: data, count: Int(length))
        let bytes = Array(packet)
        if bytes.count > 11, bytes[4] == 0x01 {
            chunkIndices.append(Int(bytes[9]) | (Int(bytes[10]) << 8))
        }
        onWrite?(packet)
        return kIOReturnSuccess
    }
}

private func feed(_ delegate: RFCOMMDelegate, _ data: Data) {
    var mutable = data
    mutable.withUnsafeMutableBytes { buffer in
        delegate.rfcommChannelData(nil, data: buffer.baseAddress, length: buffer.count)
    }
}

private extension MiniTooBridge {
    static func runConnectionChecks() throws {
        // Capture-derived packets, including the outer response command 0x04.
        let all = Data([0x01, 0x07, 0x00, 0x04, 0x8B, 0x55, 0x00, 0x01, 0xEC, 0x00, 0x02])
        let ack = Data([0x01, 0x09, 0x00, 0x04, 0xBD, 0x55, 0x13, 0x01, 0x05, 0x00, 0x38, 0x01, 0x02])
        let bridge = MiniTooBridge(address: "simulated", port: 40584, authToken: String(repeating: "a", count: 64))
        func request(_ index: UInt32) -> Data {
            bridge.packet(command: 0x04, body: Data([0x8B, 0x55, 0x01]) + bridge.littleEndian(index))
        }

        let parser = RFCOMMDelegate()
        feed(parser, Data([0xFF, 0x01, 0x00, 0x00]) + all.prefix(5))
        feed(parser, Data(all.dropFirst(5)) + ack)
        let parsedRequest = try parser.nextPacket(timeout: 0.1)
        let parsedAck = try parser.nextPacket(timeout: 0.1)
        assert(parsedRequest == all, "fragmented request lost")
        assert(parsedAck == ack, "coalesced ACK lost")
        var corrupt = ack
        corrupt[10] ^= 0x01
        feed(parser, corrupt + Data([0x01, 0xFF, 0xFF]) + all)
        let recoveredPacket = try parser.nextPacket(timeout: 0.1)
        assert(recoveredPacket == all, "corrupt packet hid valid response")

        if case .sendAll? = TransferEvent.decode(all) {} else { fatalError("request mistaken for ACK") }
        if case .acknowledged? = TransferEvent.decode(ack) {} else { fatalError("completion not recognized") }
        assert(TransferEvent.decode(bridge.packet(command: 0x08, body: Data([0, 0, 0]))) == nil)

        // Stream -> request a missing block -> final completion. Previously,
        // the missing-block request itself was incorrectly counted as ACK.
        let streamChannel = SimulatedChannel()
        bridge.channel = streamChannel
        var requestedResend = false
        streamChannel.onWrite = { packet in
            let bytes = Array(packet)
            if bytes[4] == 0 {
                // A late completion from a prior job must not consume START.
                feed(bridge.delegate, ack + all)
            } else if streamChannel.chunkIndices == [0, 1], !requestedResend {
                requestedResend = true
                feed(bridge.delegate, request(0))
            } else if streamChannel.chunkIndices == [0, 1, 0] {
                feed(bridge.delegate, ack)
            }
        }
        let streamResult = try bridge.send(frames: [Data(repeating: 0xAA, count: 300)], speedMs: 0)
        assert(streamResult.acknowledged == true)
        assert(streamChannel.chunkIndices == [0, 1, 0], "missing block not resent")

        // The completion can arrive in the pull loop itself. It must survive
        // that loop instead of being discarded before a second ACK wait.
        let pullBridge = MiniTooBridge(address: "simulated", port: 40584, authToken: String(repeating: "a", count: 64))
        let pullChannel = SimulatedChannel()
        pullBridge.channel = pullChannel
        pullChannel.onWrite = { packet in
            if Array(packet)[4] == 0 {
                feed(pullBridge.delegate, request(0))
            } else if pullChannel.chunkIndices == [0] {
                feed(pullBridge.delegate, request(1))
            } else {
                feed(pullBridge.delegate, ack)
            }
        }
        let pullResult = try pullBridge.send(frames: [Data(repeating: 0xAA, count: 300)], speedMs: 0)
        assert(pullResult.acknowledged == true)
        assert(pullChannel.chunkIndices == [0, 1])

        let invalidBridge = MiniTooBridge(address: "simulated", port: 40584, authToken: String(repeating: "a", count: 64))
        let invalidChannel = SimulatedChannel()
        invalidBridge.channel = invalidChannel
        invalidChannel.onWrite = { _ in feed(invalidBridge.delegate, request(99)) }
        do {
            _ = try invalidBridge.send(frames: [Data(repeating: 0, count: 300)], speedMs: 0)
            fatalError("out-of-range request accepted")
        } catch {
            assert(error.localizedDescription.contains("invalid chunk 99"))
        }
        assert(invalidChannel.chunkIndices.isEmpty)

        // The exact failure reported by the monitor: START receives no reply.
        // Sending a complete animation blindly must never be a fallback.
        let silentBridge = MiniTooBridge(address: "simulated", port: 40584, authToken: String(repeating: "a", count: 64))
        let silentChannel = SimulatedChannel()
        silentBridge.channel = silentChannel
        do {
            _ = try silentBridge.send(frames: [Data(repeating: 0xAA, count: 61403)], speedMs: 600)
            fatalError("unresponsive device accepted a blind upload")
        } catch {
            assert(error.localizedDescription.contains("no image chunks were sent"))
        }
        assert(silentChannel.chunkIndices.isEmpty, "animation sent without a device request")

        // Disconnect must wake a blocked reader immediately, not wait for a
        // timeout or return an ambiguous "no final acknowledgement" response.
        let disconnected = RFCOMMDelegate()
        disconnected.rfcommChannelClosed(nil)
        do {
            _ = try disconnected.nextPacket(timeout: 10)
            fatalError("closed channel accepted")
        } catch {
            assert(error.localizedDescription.contains("Bluetooth disconnected"))
        }
        print("MiniToo packet and transfer simulations passed")
    }
}

try MiniTooBridge.runConnectionChecks()
