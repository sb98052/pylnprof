#!/usr/bin/python

import sys
import os
import time
import signal

from optparse import OptionParser

LNPROF_NS = 'test'
LNPROF_NODEID=0
LNPROF_ROOT='/'

def get_nodeid(ns=LNPROF_NS):
    node_id_file = '/etc/lnprof-%s'%ns
    try:
        node_id = open(node_id_file).read().rstrip()
    except IOError:
        hostname = os.popen('/usr/bin/hostname').read().rstrip()
        node_id = os.popen('wget www.lnprof.org/command?action=getnode&ns=%s&hostname=%s'%(ns,hostname)).read().rstrip()
        open(node_id_file).write(node_id)
    return node_id


def excepthook(t, val, tb):
    exc_name = str(t)
    exc_name = exc_name[18:].split("'")[0]     

    count=3
    exc=[]
    while (count>0 and tb):
        s = "%s:%s"%(tb.tb_frame.f_code.co_filename,tb.tb_frame.f_code.co_firstlineno)
        s=s.replace('.','')
        s=s.replace('/','')
        exc.append(s)
        tb = tb.tb_next
        count = count - 1

    inp = {'root':LNPROF_ROOT,'trace':'/'.join(exc),'exc_name':exc_name,'val':val}
    log_path = """
    %(root)sError/%(exc_name)s/%(trace)s/%(val)s
    """%inp

    pushlog(get_nodeid(),log_path)
    runcron()

def handler(signum, frame):
    if (signum==signal.SIGALRM):
        runcron()

def runcron():
    last_sync_file='/tmp/lnprof-sync-%s-%s'%(LNPROF_NS,LNPROF_NODEID)
    stamp = False
    try:
        last_stamp = int(open(last_sync_file).read())
        now = int(time.time())
        if (now-last_stamp>=300):
            commit(get_nodeid())
            stamp = True
    except:
        stamp = True

    if (stamp):
        s='%d'%int(time.time())
        open(last_sync_file,'w').write(s)
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(300)


sys.excepthook = excepthook

def pushlog(log_path,node_id=LNPROF_NODEID,ns=LNPROF_NS):
    cache = open('/tmp/lnprof-%s-%s'%(ns,nodeid),'a') 
    cache.write(log_path+'\n')

def commit(node_id=LNPROF_NODEID,ns=LNPROF_NS):
    logpaths = {}
    for i in range(0,1024):
        si = '%d'%i
        try:
            fname = '/tmp/lnprof-%s-%d'%(ns,i)
            logs = open(fname).readlines()
            logs = map(lambda l:l.rstrip(),logs)
            for l in logs:
                try:
                    try:
                        logpaths[l]['nodeset'].add(si)
                    except KeyError:
                        logpaths[l]={'nodeset':set([si])}
                except AttributeError:
                    logpaths[l].nodeset = set([si])
            if (not pretend):
                os.remove(fname)
        except IOError:
            pass
    for k in logpaths.keys():
        nodeset = list(logpaths[k]['nodeset'])
        data = options
        command = '/usr/bin/curl -s --cookie /tmp/fil --cookie-jar /tmp/fil -o - --data \'action=pushlog_nodes&ns=%s&nodes=%s&log_path=%s http://www.lnprof.org/command?pushlog_nodes >> /tmp/src.html'%(data.ns,','.join(nodeset),k)
        if (pretend):
            print command
        else:
            os.system(command)

def main():
    parser = OptionParser()
    parser.add_option("-l", "--log-path", dest="log_path",
                  help="Log path to push", metavar="PATH")
    parser.add_option("-n", "--nodeid",
                  dest="nodeid", 
                  help="Lnprof node id")
    parser.add_option("-N", "--namespace",
                  dest="ns", 
                  help="Lnprof namespace")
    parser.add_option("-k", "--api-key", dest="key",
                  help="API key for your app", metavar="KEY", default = '')
    parser.add_option("-p", "--pretend",
                  dest="pretend", default=False, action="store_true",
                  help="don't run only print")

    (options, args) = parser.parse_args ()

    try:
        action = args[0]
        if (action not in ["pushlog","commit"]):
            raise Exception("bad action")
    except:
        print "Action needs to be one of pushlog and commit"
        return

    if (action=="pushlog"):
        pushlog(options.log_path, options.node_id, options.ns)
    elif (action=="commit"):
        commit(options.log_path, options.node_id, options.ns) 

if __name__ == '__main__':
    main()
