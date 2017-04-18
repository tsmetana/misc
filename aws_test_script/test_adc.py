#!/usr/bin/python3

import sys
import threading
import time
import subprocess
import glob
import os
import signal
import random

exit_flag = threading.Event()
pods_limit = 20
pvc_limit = 5

class ClusterObjects:
    last_pvc_num = 0
    last_pod_num = 0
    pvc_template = """
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: testclaim%(claim_num)s
  annotations:
    "volume.alpha.kubernetes.io/storage-class": "fast"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi"""

    pod_template = """
apiVersion: v1
kind: Pod
metadata:
  name: busybox-test-%(pod_num)s
  labels:
    name: busybox-test-%(pod_num)s
spec:
  restartPolicy: Never
  containers:
    - resources:
        limits :
          cpu: 0.5
      image: gcr.io/google_containers/busybox
      command:
        - "/bin/sh"
        - "-c"
        - "while true; do date; sleep 1; done"
      name: busybox
      volumeMounts:
        - name: vol
          mountPath: /mnt/test
  volumes:
      - name: vol
        persistentVolumeClaim:
          claimName: testclaim%(claim_num)s"""

    def __init__(self):
        self.pods = set()
        self.pvcs = set()

    def _kubectl_create(self, file_arg):
        try:
            subprocess.run("cluster/kubectl.sh create -f %s" % file_arg, shell=True, check=True)
        except:
            print("Error creating resource from %s" % file_arg)

    def create_pvc_yaml(self, claim_num):
        filename = "/tmp/pvc-" + str(claim_num) + ".yaml"
        with open(filename, 'w') as f:
            f.write(self.pvc_template % { 'claim_num': claim_num })
        return filename

    def create_pod_yaml(self, pod_num, claim_num):
        filename = "/tmp/pod-" + str(pod_num) + ".yaml"
        with open(filename, 'w') as f:
            f.write(self.pod_template % { 'pod_num': pod_num, 'claim_num': claim_num })
        return filename

    def create_pvc(self):
        if len(self.pvcs) < pvc_limit:
            pvc_num = 0
            while pvc_num in self.pvcs:
                pvc_num = round(random.random() * (pvc_limit - 1))
            yaml_file = self.create_pvc_yaml(pvc_num)
            if yaml_file != None:
                self._kubectl_create(yaml_file)
                self.pvcs.add(pvc_num)
                #os.unlink(yaml_file)

    def create_pod(self):
        if len(self.pods) < pods_limit:
            pod_num = 0
            if len(self.pvcs) == 0:
                return
            while pod_num in self.pods:
                pod_num = round(random.random() * (pods_limit - 1))
            claim_num = random.sample(self.pvcs, 1)[0]
            yaml_file = self.create_pod_yaml(pod_num, claim_num)
            if yaml_file != None:
                self._kubectl_create(yaml_file)
                self.pods.add(pod_num)
                #os.unlink(yaml_file)

    def delete_pod(self):
        if len(self.pods) > 0:
            pod_num = random.sample(self.pods, 1)[0]
            subprocess.run("cluster/kubectl.sh delete pod busybox-test-%s --grace-period=1" % pod_num, shell=True)

class ControllerSpawner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.controller_process = None
        self.controller_cmd = "sudo -E _output/local/bin/linux/amd64//hyperkube controller-manager --v=3 \
    --service-account-private-key-file=/tmp/kube-serviceaccount.key --root-ca-file=/var/run/kubernetes/server-ca.crt \
    --enable-hostpath-provisioner=false --pvclaimbinder-sync-period=15s --feature-gates=AllAlpha=true \
    --cloud-provider=aws --cloud-config= --kubeconfig /var/run/kubernetes/controller.kubeconfig \
    --use-service-account-credentials --master=https://localhost:6443"

    def _find_pid(self):
        pid = None
        cmdfiles = glob.glob("/proc/*/cmdline")
        for cmdfile in cmdfiles:
            with open(cmdfile, mode='rb') as fr:
                content = fr.read().decode().split('\x00')
                if (len(content) >= 2) and (content[1] == 'controller-manager'):
                    pid = os.path.basename(os.path.dirname(cmdfile))
                    break
        return pid

    def _restart_controller(self):
        if self.controller_process == None:
            pid = self._find_pid()
            if pid == None:
                print("Error: controller PID not found")
                return
        else:
            pid = self.controller_process.pid
        print("Killing the controller process PID %s" % pid)
        subprocess.run("sudo kill -KILL %s" % pid, shell=True)
        if self.controller_process != None:
            self.controller_process.wait()
        print("Starting new controller process")
        try:
            self.controller_process = subprocess.Popen(self.controller_cmd, shell=True)
        except Exception as e:
            print ("Error starting new controller: {0}".format(e))

    def run(self):
        print("Starting ControllerSpawner")
        # Wait for random time (0 - 30s) and force-restart the controller
        while not exit_flag.is_set():
            self._restart_controller()
            wait_time = 20 + random.random() * 120
            exit_flag.wait(timeout=wait_time)

class PodSpawner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.aws = ClusterObjects()

    def run(self):
        print("Starting PodSpawner")
        while not exit_flag.is_set():
            case = round(random.random() * 2)
            if case == 0:
                self.aws.create_pod()
            elif case == 1:
                self.aws.create_pvc()
            elif case == 2:
                self.aws.delete_pod()
            wait = random.random() * 10
            exit_flag.wait(timeout=wait)

def main():
    ctrl_spawner = ControllerSpawner()
    pod_spawner = PodSpawner()

    exit_flag.clear()
    pod_spawner.start()
    ctrl_spawner.start()
    time.sleep(600) # 10 minutes
    exit_flag.set()
    pod_spawner.join()
    ctrl_spawner.join()
    return 0

if __name__ == "__main__":
    sys.exit(main())
