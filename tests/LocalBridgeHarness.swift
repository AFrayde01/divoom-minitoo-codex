// Appended to either production bridge. Bluetooth writes are simulated;
// the production Network listener, parser and authentication remain intact.
private final class LocalTestChannel: IOBluetoothRFCOMMChannel {
    var onWrite: ((Data) -> Void)?
    override func isOpen() -> Bool { true }
    override func writeSync(_ data: UnsafeMutableRawPointer!, length: UInt16) -> IOReturn {
        fputs("TEST_BLUETOOTH_WRITE\n", stderr)
        onWrite?(Data(bytes: data, count: Int(length)))
        return kIOReturnSuccess
    }
}

private extension TEST_BRIDGE_TYPE {
    static func validateTestRequests() throws {
        let token = String(repeating: "a", count: 64)
        let bridge = TEST_BRIDGE_TYPE(address: "simulated", port: 40584, authToken: token)
        for candidate: String? in [nil, "", String(repeating: "b", count: 64),
                                   String(repeating: "a", count: 63), token + "extra"] {
            var body: [String: Any] = ["framesBase64": ["AA=="], "speedMs": 0]
            if let candidate { body["authToken"] = candidate }
            do {
                _ = try bridge.decodeAuthenticatedRequest(JSONSerialization.data(withJSONObject: body))
                fatalError("unauthorized request accepted")
            } catch {
                assert(error.localizedDescription.contains("Unauthorized"))
            }
        }
        let body: [String: Any] = ["framesBase64": ["AA=="], "speedMs": 0, "authToken": token]
        let request = try bridge.decodeAuthenticatedRequest(JSONSerialization.data(withJSONObject: body))
        assert(request.framesBase64 == ["AA=="])
        print("Authentication validation passed")
    }

    static func serveTestRequests(port: UInt16, token: String) throws -> TEST_BRIDGE_TYPE {
        let bridge = TEST_BRIDGE_TYPE(address: "simulated", port: port, authToken: token,
                                     requestTimeout: 0.8, connectionLimit: 2)
        let channel = LocalTestChannel()
        bridge.channel = channel
        TEST_MINITOO_ACKS
        try bridge.startListener()
        return bridge
    }
}

if CommandLine.arguments[1] == "--validate-only" {
    try TEST_BRIDGE_TYPE.validateTestRequests()
} else {
    let testPort = UInt16(CommandLine.arguments[1])!
    let testToken = readLine()!
    let testBridge = try TEST_BRIDGE_TYPE.serveTestRequests(port: testPort, token: testToken)
    withExtendedLifetime(testBridge) { RunLoop.current.run() }
}
