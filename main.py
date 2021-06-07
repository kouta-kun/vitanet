import http.server as hs
import json
import socketserver
import threading
import time
from http.server import BaseHTTPRequestHandler
from typing import Tuple

import cv2

from rvm import rvm


def make_handler(vm: rvm.RVMPersistentContext):
    class RvmHttpProxyRequestHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
            super().__init__(request, client_address, server)

        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path == '/status/':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(
                    (json.dumps({'actors': vm.actors,
                                 'chunkpos': {
                                     k: [[p // vm.simulation_map.chunk_x, p % vm.simulation_map.chunk_x] for p in
                                         vm.actors[k]['position']] for
                                     k in vm.actors},
                                 'world_frame': vm.frame_count})).encode('ascii'))
                self.close_connection = True
            elif self.path.startswith('/self_status/'):
                *args, user_id = self.path.split('/')
                user_id = int(user_id)
                status = vm.status_of(user_id)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(
                    json.dumps(status).encode('ascii')
                )
                self.close_connection = True
            elif self.path == "/chara/":
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open('chara.png', 'rb') as f:
                    self.wfile.write(f.read())
                self.close_connection = True
            elif self.path.startswith("/chunk/"):
                *args, chunk_x, chunk_y = self.path.split("/")
                chunk_x = int(chunk_x)
                chunk_y = int(chunk_y)
                chunk_image = vm.simulation_map.render_chunk(chunk_x, chunk_y)
                succ, enc = cv2.imencode(".jpg", chunk_image)
                if succ:
                    self.send_response(200)
                    image_bytes = enc.tobytes()
                    self.send_header('Content-Type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(image_bytes)
                    self.close_connection = True
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'failed to encode image'}).encode("ascii"))
                    self.close_connection = True
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'path not found'
                }).encode('ascii'))
                self.close_connection = True

        def do_POST(self):
            if self.path.startswith('/start/'):
                user = self.path.split('/')[-1]
                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                user_id = vm.create_player(user)
                self.wfile.write(json.dumps({'actor_id': user_id}).encode('ascii'))
                self.close_connection = True
            elif self.path == "/debug":
                indata = self.rfile.read(int(self.headers.get('content-length')))
                print('got debug', indata)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write("{}".encode())
                self.close_connection = True
            elif self.path.startswith('/action/'):
                user_id = int(self.path.split('/')[-1])
                if user_id in vm.actor_scripts:
                    indata = self.rfile.read(int(self.headers.get('content-length')))
                    action_object = json.loads(indata)
                    self.send_response(201)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    vm.actor_scripts[user_id].environment['act'] = action_object
                    self.wfile.write(json.dumps({
                        'actor_id': user_id,
                        'action': vm.actor_scripts[user_id].environment['act']
                    }).encode('ascii'))
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'error': 'user not found'
                    }).encode('ascii'))
                self.close_connection = True
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'path not found'
                }).encode('ascii'))
                self.close_connection = True

    return RvmHttpProxyRequestHandler


def load_script(path, name):
    script_file = open(path, 'r')
    script_content = script_file.read()
    script_file.close()
    return rvm.RVMScript(script_content, name)


def main():
    vm = rvm.RVMPersistentContext()
    httpserver = hs.HTTPServer(('0.0.0.0', 4242), make_handler(vm))
    http_thread = threading.Thread(target=httpserver.serve_forever)

    step_time = time.monotonic()

    def step_thread():
        nonlocal step_time
        while True:
            curr_time = time.monotonic()
            timediff = curr_time - step_time
            if timediff > 0.25:
                while timediff > 0.25:
                    vm.step()
                    timediff -= 0.25
                step_time = curr_time
            time.sleep(0)

    rvm_update = threading.Thread(target=step_thread)

    rvm_update.start()
    http_thread.start()
    while True:
        time.sleep(0)


main()
