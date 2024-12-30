#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio Remote Control Class
# $Id: rc_daemon.py,v 1.18 2024/12/21 11:21:13 bob Exp $
# 
# Author : Sander Marechal
# Website http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#
# Adapted by Bob Rathbone for the Internet Radio
# Site   : http://www.bobrathbone.com
#
# This is the daemon class for the IR remote control
# It is called frome ireventd.py
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#
# THIS CODE IS REDUNDANT AND HAS BEEN REPLACED BY ir_daemon.py (Python3)

import sys, os, time, atexit
from signal import SIGKILL 
from signal import SIGHUP 
import pdb

class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
    
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            self.ppid = os.getpid() 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError as e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
    
        # decouple from parent environment
        os.chdir("/") 
        os.setsid() 
        os.umask(0) 
    
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError as e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 
    
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile,'w+').write("%s\n" % pid)
    
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        self.begin(True)

    def nodaemon(self):
        """
        Start the program in foreground
        Test purposes only
        """

        try:
            self.begin(False)

        except KeyboardInterrupt:
            pid = os.getpid()
            print("\nStopping remote control pid",pid)
            # Remove pid file
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            sys.exit(0)
 
    def begin(self,daemonize):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
    
        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        
        # Start the daemon
        if daemonize:
            self.daemonize()
        else:
            pid = str(os.getpid())
            open(self.pidfile,'w+').write("%s\n" % pid)
            print("IR Remote control listener running pid " + str(pid))

        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
    
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Remove pid file
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

        # Try killing the daemon process    
        try:
            os.kill(pid, SIGHUP)
            sys.exit(0)

        except ValueError as err:
            print("Remote control daemon not running")
            os.remove(self.pidfile)

        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def status(self):
        """
        Status
        """

    def flash(self):
        """
        Flash activity LED
        """


    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """

    # Execute system command
    def execCommand(self,cmd):
        p = os.popen(cmd)
        result = p.readline().rstrip('\n')
        return result

### End ###
