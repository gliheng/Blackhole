import os
import threading
import subprocess
import wsgiref.util

class Event:
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    # def getHandlerCount(self):
    #     return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    #__len__  = getHandlerCount


class CmdProxy():
    def __init__(self, cmd, cwd=os.getcwd()):
        self.cmd = cmd
        self.cwd = cwd
        self.proc = None
        self.reader = None
        self.running = False

        # queue use this to restarted thread
        # Tkinter is not thread-safe, use a queue to pass data from thread to Tkinter
        # http://effbot.org/zone/tkinter-threads.htm
        self.data = queue.Queue()
        
    def start(self):

        if not self.running:
            self.running = True

            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # output of cmd is directed to this pipe
            self.pipeOut, self.pipeIn = os.pipe()
            
            logger.info('Starting proc: %s' % self.cmd)
            self.proc = subprocess.Popen(self.cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                bufsize=1, # line buffered
                startupinfo=si)

            if not self.reader:
                logger.info('Daemon thread spawned.')
                self.reader = threading.Thread(target=self.getOutput)
                self.reader.daemon = True
                self.reader.start()
                

    def restart(self):
        # restart server
        # TODO: Need test. is it right to do so?
        server.stopServer()
        server.startServer()

    def stop(self):
        if self.running:
            self.running = False
            self.proc.terminate()

    def getOutput(self):
        ''' Put data on Queue
        '''
        while self.running:
            line = self.proc.stdout.readline()
            if line and LogWin.visible:
                self.data.put_nowait(line)

        logger.info('Daemon thread exited.')

    def checkRunning(self):
        if self.proc.poll() == None:
            self.running = True
            return True
        else:
            self.running = False
            return False
        
    def connect_stdout(self):
        pass

def get_absolute_url(environ):

    url = environ['REQUEST_URI'].decode('utf-8', errors='ignore')
    # relative url found, get absolute url from host header
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + environ['HTTP_HOST'] + url

    return url

def change_host(environ, host):
    environ['blackhole.orig_host'] = environ['HTTP_HOST'] 
    environ['HTTP_HOST'] = host
    uri = wsgiref.util.request_uri(environ)
    environ['REQUEST_URI'] = uri.encode('utf-8', errors='ignore')
