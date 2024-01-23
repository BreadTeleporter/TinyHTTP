import socketserver, mimetypes, os, logging, statusCodes, sys

class HTTPHandler(socketserver.BaseRequestHandler):
    def handle(self):

        WEBROOT    = "webroot"    # Where are the web pages stored?
        SERVERNAME = "TinyHTTP" # What should we identify ourselves as in the Server header

        # TODO: This could cause issues if somebody intentionally sends
        #       more than 1024 bytes to break the server
        self.data = self.request.recv(1024).strip()

        # Decode and remove carriage returns, then split at newlines
        request = self.data.decode("UTF-8").replace("\r", "").split("\n")

        # Get the request header
        requestTypeAndURL = request[0]

        # TODO: Implement the other request types
        if (requestTypeAndURL.startswith("GET")):
            requestPath = requestTypeAndURL.split(" ")[1]

            if requestPath == "/":
                requestPath = "/index.html"

            requestFile = WEBROOT + requestPath

            responseCode = 200 # Default to 200

            if not os.path.exists(requestFile):
                responseCode = 404 # This files doesnt exist, send a 404


            userAgent = "\"_\""
            acceptTypes = "*/*"

            # TODO: Very slow, have to iterate through all the headers
            #       to find what we want
            for i in range(len(request)):
                if request[i].startswith("User-Agent: "):
                    userAgent = "\"" + request[i][12:] + "\""
                if request[i].startswith("Accept: "):
                    acceptTypes = request[i][8:].replace(" ", "").split(",")

            contentType = mimetypes.guess_type(requestFile)[0]
            if contentType not in acceptTypes:
                if "*/*" not in acceptTypes:
                    responseCode = 406

            # Looks good, start writing a response
            if responseCode == 200:

                # Headers to send to the client
                headers = [
                    "Content-Type: " + contentType,
                    "Content-Length: " + str(os.path.getsize(requestFile)),
                    "Server: " + SERVERNAME
                ]

                # This can just be read without any checks because
                # we already checked earlier
                with open(requestFile, "rb") as f:
                    filedata = f.readlines()
                try:
                    # Ready to send data. Send 200 and
                    self.request.sendall(b"HTTP/1.1 200 OK\n")
                    # start sending headers, then
                    for i in range(len(headers)):
                        self.request.sendall(headers[i].encode() + b"\n")
                    self.request.sendall(b"\n")
                    # send the actual page data.
                    for i in range(len(filedata)):
                        self.request.sendall(filedata[i])
                # Something messed up on our end, try to send 500
                except Exception as e:
                    responseCode = 500
                    logging.error(e)
                    try:
                        self.request.sendall(b"HTTP/1.1 500 Internal Server Error\n")
                    # Something went wrong here too? Assume we cant reach the client
                    except:
                        logging.error("Unable to reach " + str(self.client_address[0]))
            else:
                # Some check failed, send status code
                try:
                    self.request.sendall(str("HTTP/1.1 " + str(responseCode) + " " + statusCodes.codes[responseCode] + "\n").encode())
                    # Same as above
                except Exception as e:
                    logging.error(e)
                    logging.error("Unable to reach " + str(self.client_address[0]))
            logging.info(requestTypeAndURL + " - " + str(responseCode) + " - " + userAgent + " - " + str(self.client_address[0]))
        else:
            self.request.sendall(b"501 Not Implemented")

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 80
    logging.basicConfig(format="%(message)s", encoding='utf-8', level=logging.DEBUG, handlers=[logging.FileHandler("logs.log"), logging.StreamHandler(sys.stdout)])
    with socketserver.TCPServer((HOST, PORT), HTTPHandler) as server:
        logging.info(f"MiniHTTP started on port { PORT }")
        server.serve_forever()
