# Blender Live Update script. Cedric Guillemet MIT License. 2022. https://github.com/CedricGuillemet/BlenderLiveUpdate
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import _thread
import bpy
from pathlib import Path
import queue
import threading
import tempfile
import os

execution_queue = queue.Queue()
event = threading.Event()
        
def doit(handler):
    print("handler work")
    temp_name = next(tempfile._get_candidate_names())
    default_tmp_dir = tempfile._get_default_tempdir()
    tmp_file = os.path.join(default_tmp_dir, temp_name + ".gltf")

    try:
        bpy.ops.export_scene.gltf(filepath=tmp_file,export_format='GLTF_EMBEDDED')
    except:
        print("Exception: could not export scene as gltf")
    handler._set_response()
    handler.wfile.write(Path(tmp_file).read_text().encode('utf-8'))
    event.set()
        
class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        execution_queue.put({"fn":doit,"handler":self})
        print("waiting")
        event.wait()
        event.clear()
        print("ready")
        
def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

def execute_queued_functions():
    while not execution_queue.empty():
        workDict = execution_queue.get()     
        workDict["fn"](workDict["handler"])
    return 1.0

bpy.app.timers.register(execute_queued_functions)

_thread.start_new_thread( run, () )