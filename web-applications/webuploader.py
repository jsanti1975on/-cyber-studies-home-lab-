from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
from io import BytesIO

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content_type = self.headers['Content-Type']
        
        # Extract boundary from content type
        boundary = content_type.split("boundary=")[1].encode()
        body = self.rfile.read(content_length)

        try:
            parts = self.parse_multipart(body, boundary)
            for part in parts:
                if 'filename' in part['headers']['Content-Disposition']:
                    filename = os.path.basename(part['headers']['Content-Disposition'].split('filename=')[1].strip('"'))
                    with open(filename, 'wb') as f:
                        f.write(part['body'])
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"File uploaded successfully")
                    return

            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"File upload failed")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal server error")
            print("Error:", e)

    def parse_multipart(self, body, boundary):
        parts = []
        boundary = b'--' + boundary
        for part in body.split(boundary):
            if part and part != b'--\r\n':
                part = part.strip(b'\r\n')
                headers, body = part.split(b'\r\n\r\n', 1)
                headers = self.parse_headers(headers.decode())
                parts.append({'headers': headers, 'body': body})
        return parts

    def parse_headers(self, headers):
        header_dict = {}
        for line in headers.split('\r\n'):
            key, value = line.split(': ', 1)
            header_dict[key] = value
        return header_dict

    def do_GET(self):
        if self.path == '/upload':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.upload_form().encode())
        else:
            super().do_GET()

    def upload_form(self):
        return '''<html>
                  <body>
                  <form enctype="multipart/form-data" method="post" action="/upload">
                    <input type="file" name="file" />
                    <input type="submit" value="Upload" />
                  </form>
                  </body>
                  </html>'''

def run(server_class=HTTPServer, handler_class=CustomHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
